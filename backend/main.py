"""Simple Voice AI Assistant - FastAPI backend for voice calls with Groq LLM"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from gtts import gTTS
from pydub import AudioSegment
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client as TwilioClient

load_dotenv()

# Config

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_LLM_MODEL = os.getenv("GROQ_LLM_MODEL", "llama-3.3-70b-versatile")
AUDIO_DIR = os.getenv("AUDIO_DIR", "audio_files")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("PORT", "7860"))  # HF Spaces default

# Twilio creds - can be set via UI or .env
TWILIO_CREDENTIALS = {
    "account_sid": os.getenv("TWILIO_ACCOUNT_SID", ""),
    "auth_token": os.getenv("TWILIO_AUTH_TOKEN", ""),
    "phone_number": os.getenv("TWILIO_PHONE_NUMBER", ""),
    "ui_set": False
}

SYSTEM_PROMPT = "You are a helpful AI assistant. Keep responses concise."
LLM_TEMPERATURE = 1
LLM_MAX_TOKENS = 1024
CONVERSATION_HISTORY_LIMIT = 10

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)


class JSONLogger:
    """
    JSON Logger - Structured event logging system
    
    Purpose: Logs all events (calls, chat, errors) in structured JSON format
    Why: Makes it easy to analyze logs, track performance, debug issues
    Features:
    - Saves to logs/app_logs.json
    - Tracks timestamps, durations, event types
    - Persists across server restarts
    - Structured data for easy parsing
    """
    
    def __init__(self, log_file="logs/app_logs.json"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)
        self.logs = []
        self.load_existing_logs()
    
    def load_existing_logs(self):
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    self.logs = json.load(f)
            except Exception:
                self.logs = []
    
    def save_logs(self):
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.logs, f, indent=2)
        except Exception as e:
            log.error(f"Failed to save logs: {e}")
    
    def log_event(self, event_type, call_sid=None, step=None, data=None, duration=None):
        now = datetime.now()
        log_entry = {
            "timestamp": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S.%f")[:-3],  # Include milliseconds (3 digits)
            "event_type": event_type,
            "call_sid": call_sid,
            "step": step,
            "data": data or {},
            "duration_seconds": duration
        }
        self.logs.append(log_entry)
        self.save_logs()
        return log_entry


# Setup
os.makedirs("logs", exist_ok=True)
os.makedirs(f"{AUDIO_DIR}/output", exist_ok=True)

groq_client = Groq(api_key=GROQ_API_KEY)
json_logger = JSONLogger()
conversations = {}  # per-call conversation history

app = FastAPI(title="Voice AI Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_llm_response(messages, model=GROQ_LLM_MODEL, timeout=30):
    """
    Helper: Get AI response from Groq LLM
    
    Purpose: Centralized function to call Groq API with consistent settings
    Why: Reusable across voice and chat endpoints, consistent error handling
    Returns: AI-generated text response
    Raises: TimeoutError if request times out, Exception for other errors
    """
    import asyncio
    import signal
    
    try:
        # Note: Groq SDK doesn't have built-in timeout, but we handle it at the exception level
        completion = groq_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        error_str = str(e).lower()
        # Check for timeout-related errors
        if "timeout" in error_str or "timed out" in error_str or "connection" in error_str:
            log.error(f"LLM Timeout Error: {str(e)}")
            raise TimeoutError(f"LLM request timed out: {str(e)}")
        log.error(f"LLM Error: {str(e)}")
        raise


def generate_tts_audio(text, call_sid):
    """
    Helper: Generate TTS audio file
    
    Purpose: Converts text to speech audio file for voice responses
    Why: Twilio needs WAV format, but gTTS creates MP3 - this handles conversion
    Returns: (wav_path, mp3_path) or (None, None) on error
    Process: Generate MP3 with gTTS -> Convert to WAV with pydub
    """
    try:
        tts = gTTS(text=text, lang="en", slow=False)
        mp3_path = f"{AUDIO_DIR}/output/tts_{call_sid}_{os.urandom(4).hex()}.mp3"
        os.makedirs(os.path.dirname(mp3_path), exist_ok=True)
        tts.save(mp3_path)
        
        # Twilio needs WAV format
        audio = AudioSegment.from_mp3(mp3_path)
        wav_path = mp3_path.replace(".mp3", ".wav")
        audio.export(wav_path, format="wav")
        
        return wav_path, mp3_path
    except Exception as e:
        log.error(f"TTS Error: {str(e)}")
        return None, None


def validate_twilio_credentials(account_sid, auth_token, phone_number):
    """
    Helper: Validate Twilio credential formats
    
    Purpose: Check if credentials match expected format before API testing
    Why: Catch format errors early before making API calls
    Returns: (is_valid: bool, error_message: str or None)
    Validates: Account SID format (starts with AC, min 30 chars), Auth token length, Phone format
    """
    if not account_sid.startswith("AC") or len(account_sid) < 30:
        return False, "Invalid Account SID format. It should start with 'AC' and be at least 30 characters."
    
    if len(auth_token) < 30:
        return False, "Invalid Auth Token format. It should be at least 30 characters."
    
    if not phone_number.startswith("+") or len(phone_number) < 10:
        return False, "Invalid Phone Number format. It should start with '+' (e.g., +1234567890)."
    
    return True, None


# Routes

@app.get("/")
async def root():
    """
    Root endpoint - API information
    
    Purpose: Provides basic API information and lists all available endpoints
    When called: When someone visits the root URL (/) or wants to see API info
    Returns: API name, status, version, and list of all endpoints
    Use case: Quick health check or API discovery
    """
    log.info("🌐 ROOT ENDPOINT ACCESSED")
    return {
        "message": "Voice AI Assistant API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "voice_incoming": "POST /api/voice/incoming",
            "voice_process": "POST /api/voice/process",
            "voice_audio": "GET /api/voice/audio/{filename}",
            "chat": "GET/POST /api/chat",
            "status": "GET /api/status",
            "twilio_credentials": "GET/POST /api/twilio/credentials"
        }
    }


@app.get("/api/status")
async def status():
    """
    Status endpoint - Check if API is running
    
    Purpose: Simple health check endpoint to verify API is operational
    When called: By monitoring tools, frontend status checks, or manual verification
    Returns: Current status, model being used, and available endpoints
    Use case: Health monitoring, debugging, or checking API availability
    """
    log.info("📊 STATUS CHECK - API is running")
    return {
        "status": "running",
        "model": GROQ_LLM_MODEL,
        "endpoints": {
            "voice_incoming": "POST /api/voice/incoming",
            "voice_process": "POST /api/voice/process",
            "voice_audio": "GET /api/voice/audio/{filename}",
            "chat": "GET/POST /api/chat"
        }
    }


@app.post("/api/voice/incoming")
async def incoming_call(CallSid: str = Form(...), From: str = Form(...)):
    """
    Incoming call handler - First endpoint called when Twilio receives a call
    
    Purpose: Handles the initial call setup when someone calls your Twilio number
    When called: Automatically by Twilio when a call comes in (webhook)
    Returns: TwiML XML response that tells Twilio to listen for speech
    Use case: Starting a voice conversation - initializes conversation history and prompts user to speak
    
    Flow:
    1. Twilio calls this endpoint when someone dials your number
    2. We create a new conversation session for this call
    3. Return TwiML that says "Hello! Please speak" and starts listening
    4. Next step: Twilio sends speech to /api/voice/process
    """
    log.info(f"📞 INCOMING CALL - SID: {CallSid}, From: {From}")
    
    # Initialize conversation
    conversations[CallSid] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    
    # Create TwiML response
    response = VoiceResponse()
    response.say("Hello! Please speak.", voice="alice")
    gather = Gather(
        input="speech",
        action=f"/api/voice/process?call_sid={CallSid}",
        method="POST",
        speech_timeout="auto"
    )
    response.append(gather)
    
    json_logger.log_event(
        event_type="call_incoming",
        call_sid=CallSid,
        step="call_received",
        data={"from": From}
    )
    
    return Response(content=str(response), media_type="application/xml")


@app.post("/api/voice/process")
async def process_speech(
    request: Request,
    call_sid: str = Query(...),
    SpeechResult: str = Form("")
):
    """
    Main voice processing pipeline - The core of the voice AI system
    
    Purpose: Processes user speech through the complete AI pipeline
    When called: After user speaks, Twilio sends transcribed speech here
    Returns: TwiML XML with AI response (as audio or text-to-speech)
    Use case: This is where the magic happens - converts speech to AI response
    
    Processing Pipeline (4 steps):
    1. STT (Speech-to-Text): Already done by Twilio, we receive the text
    2. LLM: Send text to Groq AI to get intelligent response
    3. TTS (Text-to-Speech): Convert AI response to audio using Google TTS
    4. Response: Send audio back to Twilio to play to caller
    
    Why this design:
    - Separates concerns: each step is logged and can be debugged independently
    - Maintains conversation history per call (using call_sid)
    - Falls back to Twilio TTS if our TTS fails
    - Keeps last 10 messages for context (CONVERSATION_HISTORY_LIMIT)
    """
    process_start_time = datetime.now()
    
    log.info("=" * 60)
    log.info(f"🔄 PROCESSING SPEECH REQUEST")
    log.info(f"   Call SID: {call_sid}")
    log.info(f"   Speech Result Length: {len(SpeechResult) if SpeechResult else 0}")
    
    # Validate speech input - Handle silence / no speech
    if not SpeechResult or len(SpeechResult.strip()) < 2:
        log.warning("⚠️  No speech detected or speech too short")
        json_logger.log_event(
            event_type="speech_processing",
            call_sid=call_sid,
            step="no_speech_detected",
            data={
                "error": "No speech or speech too short",
                "error_type": "silence_or_no_speech",
                "speech_result_length": len(SpeechResult) if SpeechResult else 0
            },
            duration=(datetime.now() - process_start_time).total_seconds()
        )
        
        response = VoiceResponse()
        response.say("I didn't hear anything. Please speak again.", voice="alice")
        gather = Gather(
            input="speech",
            action=f"/api/voice/process?call_sid={call_sid}",
            method="POST",
            speech_timeout="auto"
        )
        response.append(gather)
        log.info("=" * 60)
        return Response(content=str(response), media_type="application/xml")
    
    # Handle STT failure (empty or invalid transcription)
    if SpeechResult.strip().lower() in ["", "error", "failed", "timeout"]:
        log.warning("⚠️  STT failure detected")
        json_logger.log_event(
            event_type="stt",
            call_sid=call_sid,
            step="stt_failure",
            data={
                "error": "STT failure",
                "error_type": "stt_failure",
                "speech_result": SpeechResult
            },
            duration=(datetime.now() - process_start_time).total_seconds()
        )
        
        response = VoiceResponse()
        response.say("I'm having trouble understanding. Please try again.", voice="alice")
        gather = Gather(
            input="speech",
            action=f"/api/voice/process?call_sid={call_sid}",
            method="POST",
            speech_timeout="auto"
        )
        response.append(gather)
        log.info("=" * 60)
        return Response(content=str(response), media_type="application/xml")
    
    user_text = SpeechResult.strip()
    turn_num = len(conversations.get(call_sid, [])) - 1
    
    # STEP 1: Speech-to-Text (already done by Twilio)
    stt_start = datetime.now()
    log.info(f"📝 STEP 1: SPEECH-TO-TEXT (STT)")
    log.info(f"   Source: Twilio Speech Recognition")
    log.info(f"   Note: Twilio handles STT internally, no raw audio file received")
    log.info(f"   Transcribed Text: \"{user_text}\"")
    log.info(f"   Text Length: {len(user_text)} characters")
    log.info(f"   Turn Number: {turn_num}")
    
    stt_duration = (datetime.now() - stt_start).total_seconds()
    json_logger.log_event(
        event_type="stt",
        call_sid=call_sid,
        step="speech_to_text",
        data={
            "provider": "twilio",
            "transcribed_text": user_text,
            "text_length": len(user_text),
            "turn_number": turn_num,
            "note": "Twilio handles STT internally, no raw audio file available"
        },
        duration=stt_duration
    )
    
    # STEP 2: LLM Processing
    log.info(f"🤖 STEP 2: LLM PROCESSING")
    log.info(f"   Model: {GROQ_LLM_MODEL}")
    
    messages = conversations.get(call_sid, []) + [{"role": "user", "content": user_text}]
    
    llm_start = datetime.now()
    try:
        ai_response = get_llm_response(messages)
        llm_duration = (datetime.now() - llm_start).total_seconds()
        
        # Update conversation history
        messages.append({"role": "assistant", "content": ai_response})
        conversations[call_sid] = messages[-CONVERSATION_HISTORY_LIMIT:]
        
        log.info(f"✅ LLM Response received")
        log.info(f"   Response: \"{ai_response[:100]}{'...' if len(ai_response) > 100 else ''}\"")
        log.info(f"   Processing Time: {llm_duration:.2f} seconds")
        
        # Log LLM response
        json_logger.log_event(
            event_type="llm",
            call_sid=call_sid,
            step="llm_response",
            data={
                "model": GROQ_LLM_MODEL,
                "model_response_text": ai_response,
                "response_length": len(ai_response),
                "turn_number": turn_num
            },
            duration=llm_duration
        )
        
    except TimeoutError as e:
        ai_response = "I apologize, but the request timed out. Please try again."
        log.error(f"❌ LLM TIMEOUT: {str(e)}")
        json_logger.log_event(
            event_type="llm",
            call_sid=call_sid,
            step="llm_timeout",
            data={
                "error": str(e),
                "error_type": "timeout",
                "turn_number": turn_num
            },
            duration=(datetime.now() - llm_start).total_seconds()
        )
    except Exception as e:
        ai_response = f"I apologize, but I encountered an error: {str(e)}"
        log.error(f"❌ LLM ERROR: {str(e)}")
        json_logger.log_event(
            event_type="llm",
            call_sid=call_sid,
            step="llm_error",
            data={
                "error": str(e),
                "error_type": type(e).__name__,
                "turn_number": turn_num
            },
            duration=(datetime.now() - llm_start).total_seconds()
        )
    
    # STEP 3: Text-to-Speech
    log.info(f"🔊 STEP 3: TEXT-TO-SPEECH (TTS)")
    log.info(f"   Provider: Google TTS (gTTS)")
    
    tts_start = datetime.now()
    wav_path, mp3_path = generate_tts_audio(ai_response, call_sid)
    tts_duration = (datetime.now() - tts_start).total_seconds()
    
    audio_url = None
    tts_filename = None
    if wav_path:
        tts_filename = os.path.basename(wav_path)
        base_url = str(request.base_url).rstrip("/")
        audio_url = f"{base_url}/api/voice/audio/{tts_filename}"
        log.info(f"✅ TTS Audio generated successfully")
        log.info(f"   TTS Filename: {tts_filename}")
        log.info(f"   Audio URL: {audio_url}")
        log.info(f"   TTS Time: {tts_duration:.2f} seconds")
        
        json_logger.log_event(
            event_type="tts",
            call_sid=call_sid,
            step="text_to_speech",
            data={
                "provider": "gtts",
                "tts_filename": tts_filename,
                "audio_url": audio_url,
                "text_length": len(ai_response),
                "turn_number": turn_num
            },
            duration=tts_duration
        )
    else:
        log.warning("⚠️  TTS failed, falling back to Twilio TTS")
        json_logger.log_event(
            event_type="tts",
            call_sid=call_sid,
            step="tts_error",
            data={
                "error": "TTS generation failed",
                "error_type": "tts_failure",
                "fallback": "twilio_tts",
                "turn_number": turn_num
            },
            duration=tts_duration
        )
    
    # STEP 4: Send Response
    log.info(f"📤 STEP 4: SENDING RESPONSE")
    response = VoiceResponse()
    
    if audio_url:
        response.play(audio_url)
        log.info(f"   Using generated audio file")
    else:
        response.say(ai_response, voice="alice")
        log.info(f"   Using Twilio text-to-speech fallback")
    
    gather = Gather(
        input="speech",
        action=f"/api/voice/process?call_sid={call_sid}",
        method="POST",
        speech_timeout="auto"
    )
    response.append(gather)
    response.hangup()
    
    total_duration = (datetime.now() - process_start_time).total_seconds()
    
    json_logger.log_event(
        event_type="speech_processing",
        call_sid=call_sid,
        step="complete",
        data={"turn_number": turn_num, "total_steps": 4},
        duration=total_duration
    )
    
    log.info(f"✅ Response sent to Twilio")
    log.info(f"   Total Processing Time: {total_duration:.2f} seconds")
    log.info("=" * 60)
    
    return Response(content=str(response), media_type="application/xml")


@app.get("/api/voice/audio/{filename}")
async def serve_audio(filename: str):
    """
    Audio file server - Serves generated TTS audio files
    
    Purpose: Provides HTTP access to generated audio files for Twilio to play
    When called: By Twilio when it needs to play the audio file we generated
    Returns: WAV audio file or 404 if file doesn't exist
    Use case: Twilio can't access local files, so we serve them via HTTP
    
    Why needed:
    - We generate audio files locally (in audio_files/output/)
    - Twilio needs a public URL to fetch and play the audio
    - This endpoint makes our local files accessible via HTTP
    - Used in the response.play() call in process_speech endpoint
    """
    audio_path = f"{AUDIO_DIR}/output/{filename}"
    if os.path.exists(audio_path):
        return FileResponse(audio_path, media_type="audio/wav")
    return Response(status_code=404)


@app.post("/api/chat")
async def chat_endpoint(message: str = Form(...)):
    """
    Chat endpoint (POST) - Text-based chat interface for frontend
    
    Purpose: Allows frontend to send text messages and get AI responses
    When called: When user types a message in the web UI and submits
    Returns: AI response as JSON with status, input, response, and model info
    Use case: Web-based chat interface (separate from voice calls)
    
    Why separate from voice:
    - Voice uses Twilio webhooks (Form data from Twilio)
    - Chat uses standard POST requests from frontend
    - Different use cases: voice calls vs text chat
    - Same LLM backend, different input/output methods
    """
    start_time = datetime.now()
    log.info("=" * 60)
    log.info(f"💬 CHAT ENDPOINT (POST)")
    log.info(f"   Input Message: \"{message}\"")
    log.info(f"   Model: {GROQ_LLM_MODEL}")
    
    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message}
        ]
        
        ai_response = get_llm_response(messages)
        duration = (datetime.now() - start_time).total_seconds()
        
        log.info(f"✅ LLM Response received")
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
        log.info("=" * 60)
        
        json_logger.log_event(
            event_type="chat",
            step="llm_error",
            data={"error": str(e), "input": message},
            duration=duration
        )
        
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/api/chat")
async def chat_endpoint_get(message: str = Query(...)):
    """
    Chat endpoint (GET) - Alternative text chat using GET method
    
    Purpose: Same as POST /api/chat but uses GET method for convenience
    When called: When frontend wants to use GET instead of POST (easier for testing)
    Returns: Same as POST endpoint - AI response as JSON
    Use case: Testing, simple integrations, or when POST isn't preferred
    
    Why both GET and POST:
    - Some clients prefer GET for simplicity
    - GET is easier to test in browser (just add ?message=hello)
    - POST is more standard for form submissions
    - Both use the same LLM processing logic
    """
    start_time = datetime.now()
    log.info("=" * 60)
    log.info(f"💬 CHAT ENDPOINT (GET)")
    log.info(f"   Input Message: \"{message}\"")
    log.info(f"   Model: {GROQ_LLM_MODEL}")
    
    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message}
        ]
        
        ai_response = get_llm_response(messages)
        duration = (datetime.now() - start_time).total_seconds()
        
        log.info(f"✅ LLM Response received")
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
        log.info("=" * 60)
        
        json_logger.log_event(
            event_type="chat",
            step="llm_error_get",
            data={"error": str(e), "input": message},
            duration=duration
        )
        
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/api/twilio/credentials")
async def set_twilio_credentials(
    account_sid: str = Form(...),
    auth_token: str = Form(...),
    phone_number: str = Form(...)
):
    """
    Set Twilio credentials - Validates and stores Twilio account info
    
    Purpose: Allows users to configure Twilio credentials via UI instead of .env file
    When called: When user submits Twilio credentials in the frontend settings
    Returns: Success/error status with validation results
    Use case: Dynamic credential management - no need to restart server or edit .env
    
    Why this exists:
    - Users can set credentials through UI without touching code
    - Validates credentials before storing (tests with Twilio API)
    - Verifies phone number belongs to the account
    - Overrides .env credentials when set (ui_set flag)
    - Credentials stored in memory (lost on restart, falls back to .env)
    
    Security note:
    - Validates format before testing
    - Tests credentials with actual Twilio API call
    - Only stores if validation succeeds
    - Provides user-friendly error messages
    """
    log.info(f"🔐 VALIDATING TWILIO CREDENTIALS")
    log.info(f"   Account SID: {account_sid[:10]}...")
    log.info(f"   Phone Number: {phone_number}")
    
    try:
        # Validate format
        is_valid, error_msg = validate_twilio_credentials(account_sid, auth_token, phone_number)
        if not is_valid:
            log.warning(f"❌ {error_msg}")
            return {"status": "error", "error": error_msg}
        
        # Test credentials with Twilio API
        log.info(f"   Testing credentials with Twilio API...")
        try:
            test_client = TwilioClient(account_sid, auth_token)
            account = test_client.api.accounts(account_sid).fetch()
            
            if not account:
                return {
                    "status": "error",
                    "error": "Failed to validate credentials with Twilio"
                }
            
            log.info(f"✅ Twilio credentials validated successfully")
            log.info(f"   Account Name: {account.friendly_name}")
            
            # Verify phone number belongs to this account
            try:
                incoming_numbers = test_client.incoming_phone_numbers.list(
                    phone_number=phone_number,
                    limit=1
                )
                if not incoming_numbers:
                    log.warning(f"⚠️  Phone number {phone_number} not found in account")
                    return {
                        "status": "error",
                        "error": f"Phone number {phone_number} not found in your Twilio account."
                    }
                log.info(f"✅ Phone number verified: {phone_number}")
            except Exception as phone_error:
                log.warning(f"⚠️  Could not verify phone number: {str(phone_error)}")
            
            # Store credentials after validation
            TWILIO_CREDENTIALS["account_sid"] = account_sid
            TWILIO_CREDENTIALS["auth_token"] = auth_token
            TWILIO_CREDENTIALS["phone_number"] = phone_number
            TWILIO_CREDENTIALS["ui_set"] = True
            
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
            
        except Exception as twilio_error:
            error_msg = str(twilio_error)
            log.error(f"❌ TWILIO VALIDATION ERROR: {error_msg}")
            
            # User-friendly error messages
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
    """
    Get Twilio credentials status - Check if credentials are configured
    
    Purpose: Frontend can check if Twilio is set up without exposing sensitive data
    When called: When frontend loads settings page or checks connection status
    Returns: Configuration status, phone number (safe), and masked account SID preview
    Use case: UI needs to know if credentials are set to show/hide setup form
    
    Why this endpoint:
    - Frontend needs to know if Twilio is configured
    - Can't expose full credentials for security
    - Shows only safe info: phone number and first 10 chars of SID
    - Only returns true if credentials were set via UI (not just .env)
    
    Security:
    - Never returns auth_token
    - Only shows partial account_sid (first 10 chars)
    - Phone number is safe to expose
    """
    log.info(f"🔍 GETTING TWILIO CREDENTIALS STATUS")
    
    # Only consider configured if credentials were set via UI
    has_credentials = (
        TWILIO_CREDENTIALS.get("ui_set", False) and
        TWILIO_CREDENTIALS.get("account_sid") and
        TWILIO_CREDENTIALS.get("auth_token") and
        TWILIO_CREDENTIALS.get("phone_number")
    )
    
    return {
        "status": "success",
        "configured": has_credentials,
        "phone_number": TWILIO_CREDENTIALS.get("phone_number", "") if has_credentials else "",
        "account_sid_preview": (
            TWILIO_CREDENTIALS.get("account_sid", "")[:10] + "..." 
            if has_credentials else ""
        )
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
    
    port = int(os.getenv("PORT", "7860"))
    log.info(f"   Using port: {port} (Hugging Face Spaces)")
    uvicorn.run(app, host="0.0.0.0", port=port)
