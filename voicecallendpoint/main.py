"""Simple Voice AI Assistant"""
from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client as TwilioClient
from groq import Groq
from gtts import gTTS
from pydub import AudioSegment
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configure terminal logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)

# JSON Logging System
class JSONLogger:
    def __init__(self, log_file="logs/app_logs.json"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)
        self.logs = []
        self.load_existing_logs()
    
    def load_existing_logs(self):
        """Load existing logs from file."""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    self.logs = json.load(f)
            except:
                self.logs = []
    
    def save_logs(self):
        """Save logs to JSON file."""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.logs, f, indent=2)
        except Exception as e:
            log.error(f"Failed to save logs: {e}")
    
    def log_event(self, event_type, call_sid=None, step=None, data=None, duration=None):
        """Log an event with timestamp and duration."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "call_sid": call_sid,
            "step": step,
            "data": data or {},
            "duration_seconds": duration
        }
        self.logs.append(log_entry)
        self.save_logs()
        return log_entry

# Global JSON logger instance
json_logger = JSONLogger()

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_LLM_MODEL = os.getenv("GROQ_LLM_MODEL", "llama-3.3-70b-versatile")
AUDIO_DIR = os.getenv("AUDIO_DIR", "audio_files")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("PORT", "7860"))  # Hugging Face Spaces uses port 7860

# Create directories
os.makedirs("logs", exist_ok=True)
os.makedirs(f"{AUDIO_DIR}/output", exist_ok=True)

groq_client = Groq(api_key=GROQ_API_KEY)
conversations = {}

# Twilio credentials storage (in production, use secure storage like database)
# Environment variables are used as defaults, but UI-set credentials override them
twilio_credentials = {
    "account_sid": os.getenv("TWILIO_ACCOUNT_SID", ""),
    "auth_token": os.getenv("TWILIO_AUTH_TOKEN", ""),
    "phone_number": os.getenv("TWILIO_PHONE_NUMBER", ""),
    "ui_set": False  # Flag to track if credentials were set via UI
}


@app.post("/api/voice/incoming")
async def incoming_call(CallSid: str = Form(...), From: str = Form(...)):
    """Handle incoming call."""
    conversations[CallSid] = [{"role": "system", "content": "You are a helpful AI assistant. Keep responses concise."}]
    
    response = VoiceResponse()
    response.say("Hello! Please speak.", voice="alice")
    gather = Gather(input="speech", action=f"/api/voice/process?call_sid={CallSid}", method="POST", speech_timeout="auto")
    response.append(gather)
    return Response(content=str(response), media_type="application/xml")


@app.post("/api/voice/process")
async def process_speech(request: Request, call_sid: str = Query(...), SpeechResult: str = Form("")):
    """Process: Speech -> LLM -> TTS."""
    process_start_time = datetime.now()
    
    log.info("=" * 60)
    log.info(f"🔄 PROCESSING SPEECH REQUEST")
    log.info(f"   Call SID: {call_sid}")
    log.info(f"   Speech Result Length: {len(SpeechResult) if SpeechResult else 0}")
    
    if not SpeechResult or len(SpeechResult.strip()) < 2:
        log.warning("⚠️  No speech detected or speech too short")
        log.info("   Requesting speech again...")
        json_logger.log_event(
            event_type="speech_processing",
            call_sid=call_sid,
            step="no_speech_detected",
            data={"error": "No speech or speech too short"},
            duration=(datetime.now() - process_start_time).total_seconds()
        )
        response = VoiceResponse()
        gather = Gather(input="speech", action=f"/api/voice/process?call_sid={call_sid}", method="POST", speech_timeout="auto")
        response.append(gather)
        log.info("=" * 60)
        return Response(content=str(response), media_type="application/xml")
    
    user_text = SpeechResult.strip()
    turn_num = len(conversations.get(call_sid, [])) - 1
    
    log.info(f"📝 STEP 1: SPEECH-TO-TEXT (STT)")
    log.info(f"   Source: Twilio Speech Recognition")
    log.info(f"   Raw Speech Result: \"{SpeechResult}\"")
    log.info(f"   Transcribed Text: \"{user_text}\"")
    log.info(f"   Text Length: {len(user_text)} characters")
    log.info(f"   Turn Number: {turn_num}")
    
    stt_start = datetime.now()
    stt_duration = (datetime.now() - stt_start).total_seconds()
    
    json_logger.log_event(
        event_type="stt",
        call_sid=call_sid,
        step="speech_to_text",
        data={
            "provider": "twilio",
            "raw_speech_result": SpeechResult,
            "transcribed_text": user_text,
            "text_length": len(user_text),
            "turn_number": turn_num,
            "confidence": "N/A (Twilio built-in)"
        },
        duration=stt_duration
    )
    
    log.info(f"   ✅ STT completed in {stt_duration:.3f} seconds")
    
    # LLM
    log.info(f"🤖 STEP 2: LLM PROCESSING")
    log.info(f"   Model: {GROQ_LLM_MODEL}")
    log.info(f"   Sending request to Groq API...")
    
    messages = conversations.get(call_sid, []) + [{"role": "user", "content": user_text}]
    try:
        start_time = datetime.now()
        completion = groq_client.chat.completions.create(
            model=GROQ_LLM_MODEL,
            messages=messages,
            temperature=1,
            max_completion_tokens=1024
        )
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        ai_response = completion.choices[0].message.content.strip()
        messages.append({"role": "assistant", "content": ai_response})
        conversations[call_sid] = messages[-10:]
        
        log.info(f"✅ LLM Response received")
        log.info(f"   Response: \"{ai_response[:100]}{'...' if len(ai_response) > 100 else ''}\"")
        log.info(f"   Response Length: {len(ai_response)} characters")
        log.info(f"   Processing Time: {duration:.2f} seconds")
        
    except Exception as e:
        ai_response = f"Error: {str(e)}"
        log.error(f"❌ LLM ERROR: {str(e)}")
        log.error(f"   Error Type: {type(e).__name__}")
    
    # TTS
    log.info(f"🔊 STEP 3: TEXT-TO-SPEECH (TTS)")
    log.info(f"   Provider: Google TTS (gTTS)")
    log.info(f"   Input Text: \"{ai_response[:50]}{'...' if len(ai_response) > 50 else ''}\"")
    log.info(f"   Text Length: {len(ai_response)} characters")
    log.info(f"   Language: en (English)")
    log.info(f"   Generating audio from text...")
    
    tts_start = datetime.now()
    try:
        # Step 3.1: Generate TTS
        tts_generate_start = datetime.now()
        tts = gTTS(text=ai_response, lang="en", slow=False)
        tts_generate_duration = (datetime.now() - tts_generate_start).total_seconds()
        log.info(f"   ✅ TTS object created in {tts_generate_duration:.3f} seconds")
        
        # Step 3.2: Save MP3
        mp3_save_start = datetime.now()
        mp3_path = f"{AUDIO_DIR}/output/tts_{call_sid}_{os.urandom(4).hex()}.mp3"
        os.makedirs(os.path.dirname(mp3_path), exist_ok=True)
        log.info(f"   Saving MP3 file: {mp3_path}")
        tts.save(mp3_path)
        mp3_save_duration = (datetime.now() - mp3_save_start).total_seconds()
        mp3_size = os.path.getsize(mp3_path)
        log.info(f"   ✅ MP3 saved in {mp3_save_duration:.3f} seconds ({mp3_size / 1024:.2f} KB)")
        
        # Step 3.3: Convert to WAV
        wav_convert_start = datetime.now()
        log.info(f"   Converting MP3 to WAV for Twilio...")
        audio = AudioSegment.from_mp3(mp3_path)
        wav_path = mp3_path.replace(".mp3", ".wav")
        audio.export(wav_path, format="wav")
        wav_convert_duration = (datetime.now() - wav_convert_start).total_seconds()
        wav_size = os.path.getsize(wav_path)
        log.info(f"   ✅ WAV converted in {wav_convert_duration:.3f} seconds ({wav_size / 1024:.2f} KB)")
        
        tts_total_duration = (datetime.now() - tts_start).total_seconds()
        
        base_url = str(request.base_url).rstrip("/")
        audio_url = f"{base_url}/api/voice/audio/{os.path.basename(wav_path)}"
        
        log.info(f"✅ TTS Audio generated successfully")
        log.info(f"   MP3 File: {mp3_path}")
        log.info(f"   WAV File: {wav_path}")
        log.info(f"   Audio URL: {audio_url}")
        log.info(f"   Total TTS Time: {tts_total_duration:.2f} seconds")
        log.info(f"   Breakdown:")
        log.info(f"     - TTS Generation: {tts_generate_duration:.3f}s")
        log.info(f"     - MP3 Save: {mp3_save_duration:.3f}s")
        log.info(f"     - WAV Conversion: {wav_convert_duration:.3f}s")
        
        json_logger.log_event(
            event_type="tts",
            call_sid=call_sid,
            step="text_to_speech",
            data={
                "provider": "gtts",
                "language": "en",
                "input_text": ai_response,
                "text_length": len(ai_response),
                "mp3_path": mp3_path,
                "mp3_size_kb": round(mp3_size / 1024, 2),
                "wav_path": wav_path,
                "wav_size_kb": round(wav_size / 1024, 2),
                "audio_url": audio_url,
                "turn_number": turn_num
            },
            duration=tts_total_duration
        )
        
    except Exception as e:
        tts_duration = (datetime.now() - tts_start).total_seconds()
        audio_url = None
        log.error(f"❌ TTS ERROR: {str(e)}")
        log.error(f"   Error Type: {type(e).__name__}")
        log.warning("   Falling back to Twilio text-to-speech")
        
        json_logger.log_event(
            event_type="tts",
            call_sid=call_sid,
            step="tts_error",
            data={
                "provider": "gtts",
                "error": str(e),
                "error_type": type(e).__name__,
                "input_text": ai_response,
                "text_length": len(ai_response),
                "fallback": "twilio_tts"
            },
            duration=tts_duration
        )
    
    # Response
    log.info(f"📤 STEP 4: SENDING RESPONSE")
    response_start = datetime.now()
    response = VoiceResponse()
    if audio_url:
        log.info(f"   Using generated audio file")
        response.play(audio_url)
    else:
        log.info(f"   Using Twilio text-to-speech fallback")
        response.say(ai_response, voice="alice")
    
    gather = Gather(input="speech", action=f"/api/voice/process?call_sid={call_sid}", method="POST", speech_timeout="auto")
    response.append(gather)
    response.hangup()
    
    total_duration = (datetime.now() - process_start_time).total_seconds()
    response_duration = (datetime.now() - response_start).total_seconds()
    
    json_logger.log_event(
        event_type="speech_processing",
        call_sid=call_sid,
        step="response_sent",
        data={
            "turn_number": turn_num,
            "used_audio_file": audio_url is not None,
            "audio_url": audio_url
        },
        duration=response_duration
    )
    
    json_logger.log_event(
        event_type="speech_processing",
        call_sid=call_sid,
        step="complete",
        data={
            "turn_number": turn_num,
            "total_steps": 4
        },
        duration=total_duration
    )
    
    log.info(f"✅ Response sent to Twilio")
    log.info(f"   Turn {turn_num} completed")
    log.info(f"   Total Processing Time: {total_duration:.2f} seconds")
    log.info("=" * 60)
    
    return Response(content=str(response), media_type="application/xml")


@app.get("/api/voice/audio/{filename}")
async def serve_audio(filename: str):
    """Serve audio files."""
    audio_path = f"{AUDIO_DIR}/output/{filename}"
    return FileResponse(audio_path, media_type="audio/wav") if os.path.exists(audio_path) else Response(status_code=404)


@app.get("/")
async def root():
    """API info endpoint."""
    log.info(f"🌐 ROOT ENDPOINT ACCESSED")
    return {
        "message": "Voice AI Assistant API",
        "status": "running",
        "endpoints": {
            "voice_incoming": "POST /api/voice/incoming",
            "voice_process": "POST /api/voice/process",
            "voice_audio": "GET /api/voice/audio/{filename}",
            "status": "/api/status"
        }
    }


@app.post("/api/chat")
async def chat_endpoint(message: str = Form(...)):
    """Chat endpoint for frontend - send text and get LLM response."""
    start_time = datetime.now()
    log.info("=" * 60)
    log.info(f"💬 CHAT ENDPOINT")
    log.info(f"   Input Message: \"{message}\"")
    log.info(f"   Model: {GROQ_LLM_MODEL}")
    
    try:
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Keep responses concise."},
            {"role": "user", "content": message}
        ]
        
        log.info(f"   Sending request to Groq API...")
        
        completion = groq_client.chat.completions.create(
            model=GROQ_LLM_MODEL,
            messages=messages,
            temperature=1,
            max_completion_tokens=1024
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        ai_response = completion.choices[0].message.content.strip()
        
        log.info(f"✅ LLM Response received")
        log.info(f"   Response: \"{ai_response[:100]}{'...' if len(ai_response) > 100 else ''}\"")
        log.info(f"   Response Length: {len(ai_response)} characters")
        log.info(f"   Processing Time: {duration:.2f} seconds")
        log.info("=" * 60)
        
        json_logger.log_event(
            event_type="chat",
            step="llm_response",
            data={
                "model": GROQ_LLM_MODEL,
                "input": message,
                "response": ai_response,
                "response_length": len(ai_response)
            },
            duration=duration
        )
        
        return {
            "status": "success",
            "input": message,
            "response": ai_response,
            "model": GROQ_LLM_MODEL
        }
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        log.error(f"❌ LLM ERROR: {str(e)}")
        log.error(f"   Error Type: {type(e).__name__}")
        log.info("=" * 60)
        
        json_logger.log_event(
            event_type="chat",
            step="llm_error",
            data={
                "error": str(e),
                "error_type": type(e).__name__,
                "input": message
            },
            duration=duration
        )
        
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/api/chat")
async def chat_endpoint_get(message: str = Query(...)):
    """Chat endpoint for frontend - GET version."""
    start_time = datetime.now()
    log.info("=" * 60)
    log.info(f"💬 CHAT ENDPOINT (GET)")
    log.info(f"   Input Message: \"{message}\"")
    log.info(f"   Model: {GROQ_LLM_MODEL}")
    
    try:
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Keep responses concise."},
            {"role": "user", "content": message}
        ]
        
        log.info(f"   Sending request to Groq API...")
        
        completion = groq_client.chat.completions.create(
            model=GROQ_LLM_MODEL,
            messages=messages,
            temperature=1,
            max_completion_tokens=1024
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        ai_response = completion.choices[0].message.content.strip()
        
        log.info(f"✅ LLM Response received")
        log.info(f"   Response: \"{ai_response[:100]}{'...' if len(ai_response) > 100 else ''}\"")
        log.info(f"   Response Length: {len(ai_response)} characters")
        log.info(f"   Processing Time: {duration:.2f} seconds")
        log.info("=" * 60)
        
        json_logger.log_event(
            event_type="chat",
            step="llm_response_get",
            data={
                "model": GROQ_LLM_MODEL,
                "input": message,
                "response": ai_response,
                "response_length": len(ai_response)
            },
            duration=duration
        )
        
        return {
            "status": "success",
            "input": message,
            "response": ai_response,
            "model": GROQ_LLM_MODEL
        }
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        log.error(f"❌ LLM ERROR: {str(e)}")
        log.error(f"   Error Type: {type(e).__name__}")
        log.info("=" * 60)
        
        json_logger.log_event(
            event_type="chat",
            step="llm_error_get",
            data={
                "error": str(e),
                "error_type": type(e).__name__,
                "input": message
            },
            duration=duration
        )
        
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/api/status")
async def status():
    """API status endpoint."""
    log.info(f"📊 STATUS CHECK - API is running")
    return {
        "status": "running",
        "endpoints": {
            "voice_incoming": "POST /api/voice/incoming",
            "voice_process": "POST /api/voice/process",
            "voice_audio": "GET /api/voice/audio/{filename}",
            "chat": "GET/POST /api/chat"
        }
    }


@app.post("/api/twilio/credentials")
async def set_twilio_credentials(
    account_sid: str = Form(...),
    auth_token: str = Form(...),
    phone_number: str = Form(...)
):
    """Validate and store Twilio credentials."""
    log.info(f"🔐 VALIDATING TWILIO CREDENTIALS")
    log.info(f"   Account SID: {account_sid[:10]}...")
    log.info(f"   Phone Number: {phone_number}")
    
    try:
        # Validate credentials format
        if not account_sid.startswith("AC") or len(account_sid) < 30:
            log.warning(f"❌ Invalid Account SID format")
            return {
                "status": "error",
                "error": "Invalid Account SID format. It should start with 'AC' and be at least 30 characters."
            }
        
        if len(auth_token) < 30:
            log.warning(f"❌ Invalid Auth Token format")
            return {
                "status": "error",
                "error": "Invalid Auth Token format. It should be at least 30 characters."
            }
        
        if not phone_number.startswith("+") or len(phone_number) < 10:
            log.warning(f"❌ Invalid Phone Number format")
            return {
                "status": "error",
                "error": "Invalid Phone Number format. It should start with '+' (e.g., +1234567890)."
            }
        
        # Test credentials by making an API call to Twilio
        log.info(f"   Testing credentials with Twilio API...")
        try:
            test_client = TwilioClient(account_sid, auth_token)
            # Try to fetch account info to verify credentials
            account = test_client.api.accounts(account_sid).fetch()
            
            if account:
                log.info(f"✅ Twilio credentials validated successfully")
                log.info(f"   Account Name: {account.friendly_name}")
                
                # Verify phone number belongs to this account
                try:
                    incoming_numbers = test_client.incoming_phone_numbers.list(phone_number=phone_number, limit=1)
                    if not incoming_numbers:
                        log.warning(f"⚠️  Phone number {phone_number} not found in account")
                        return {
                            "status": "error",
                            "error": f"Phone number {phone_number} not found in your Twilio account. Please verify the number."
                        }
                    log.info(f"✅ Phone number verified: {phone_number}")
                except Exception as phone_error:
                    log.warning(f"⚠️  Could not verify phone number: {str(phone_error)}")
                    # Continue anyway, phone number verification is not critical
                
                # Store credentials only after validation
                twilio_credentials["account_sid"] = account_sid
                twilio_credentials["auth_token"] = auth_token
                twilio_credentials["phone_number"] = phone_number
                twilio_credentials["ui_set"] = True  # Mark as UI-set credentials
                
                json_logger.log_event(
                    event_type="twilio_config",
                    step="credentials_validated_and_set",
                    data={
                        "account_sid_set": True,
                        "phone_number": phone_number,
                        "account_name": account.friendly_name
                    }
                )
                
                log.info(f"✅ Twilio credentials validated and stored successfully")
                return {
                    "status": "success",
                    "message": "Twilio credentials validated and connected successfully"
                }
            else:
                log.error(f"❌ Failed to fetch account info")
                return {
                    "status": "error",
                    "error": "Failed to validate credentials with Twilio"
                }
        except Exception as twilio_error:
            error_msg = str(twilio_error)
            log.error(f"❌ TWILIO VALIDATION ERROR: {error_msg}")
            
            # Provide user-friendly error messages
            if "20003" in error_msg or "Authenticate" in error_msg or "Invalid" in error_msg:
                return {
                    "status": "error",
                    "error": "Invalid Account SID or Auth Token. Please check your credentials."
                }
            elif "20001" in error_msg:
                return {
                    "status": "error",
                    "error": "Unauthorized. Please check your Account SID and Auth Token."
                }
            else:
                return {
                    "status": "error",
                    "error": f"Failed to connect to Twilio: {error_msg}"
                }
        
    except Exception as e:
        log.error(f"❌ ERROR VALIDATING CREDENTIALS: {str(e)}")
        return {
            "status": "error",
            "error": f"Error: {str(e)}"
        }


@app.get("/api/twilio/credentials")
async def get_twilio_credentials():
    """Get Twilio credentials status (without sensitive data)."""
    log.info(f"🔍 GETTING TWILIO CREDENTIALS STATUS")
    
    # Only consider configured if credentials were set via UI (not just env vars)
    # This ensures UI-set credentials reset on page refresh
    has_credentials = (
        twilio_credentials.get("ui_set", False) and
        twilio_credentials.get("account_sid") and
        twilio_credentials.get("auth_token") and
        twilio_credentials.get("phone_number")
    )
    
    return {
        "status": "success",
        "configured": has_credentials,
        "phone_number": twilio_credentials.get("phone_number", "") if has_credentials else "",
        "account_sid_preview": twilio_credentials.get("account_sid", "")[:10] + "..." if has_credentials else ""
    }


if __name__ == "__main__":
    import uvicorn
    start_time = datetime.now()
    log.info("=" * 60)
    log.info("🚀 STARTING VOICE AI ASSISTANT SERVER")
    log.info(f"   Host: {API_HOST}")
    log.info(f"   Port: {API_PORT}")
    log.info(f"   Groq Model: {GROQ_LLM_MODEL}")
    log.info(f"   Audio Directory: {AUDIO_DIR}")
    log.info(f"   Log File: logs/app_logs.json")
    log.info("=" * 60)
    
    json_logger.log_event(
        event_type="server_start",
        step="server_initialized",
        data={
            "host": API_HOST,
            "port": API_PORT,
            "model": GROQ_LLM_MODEL,
            "audio_dir": AUDIO_DIR
        },
        duration=0
    )
    
    # For Hugging Face Spaces, use port 7860
    port = int(os.getenv("PORT", "7860"))
    log.info(f"   Using port: {port} (Hugging Face Spaces)")
    uvicorn.run(app, host="0.0.0.0", port=port)
