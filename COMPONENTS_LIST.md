# Complete Components List

This document provides a comprehensive list of all components, libraries, and technologies used in the Voice AI Assistant implementation.

## Frontend Components

### React Application
- **React** v18.2.0 - UI framework
- **react-dom** v18.2.0 - DOM rendering
- **react-scripts** v5.0.1 - Build tooling

### React Hooks Used
- `useState` - State management
- `useEffect` - Side effects and lifecycle
- `useRef` - DOM and object references
- `useCallback` - Memoized callbacks

### Browser APIs
- **Web Speech API**
  - `window.SpeechRecognition` / `window.webkitSpeechRecognition` - Speech-to-Text
  - `window.speechSynthesis` - Text-to-Speech engine
  - `SpeechSynthesisUtterance` - TTS utterance object
- **localStorage API** - Browser storage
- **Fetch API** - HTTP requests

### Frontend Files
- `App.jsx` - Main React component
- `App.css` - Component styles
- `index.js` - React entry point
- `index.css` - Global styles

## Backend Components

### Web Framework
- **FastAPI** v0.104.1 - Modern Python web framework
- **Uvicorn** v0.24.0 - ASGI server
- **CORSMiddleware** - Cross-origin resource sharing

### Twilio Integration
- **twilio** v8.10.0 - Twilio Python SDK
  - `twilio.rest.Client` - REST API client
  - `twilio.twiml.voice_response.VoiceResponse` - TwiML builder
  - `twilio.twiml.voice_response.Gather` - Speech input collection
  - `twilio.twiml.voice_response.Say` - Text-to-speech verb
  - `twilio.twiml.voice_response.Play` - Audio playback verb

### LLM Integration
- **groq** v0.4.1 - Groq Python SDK
  - `Groq()` - Client initialization
  - `chat.completions.create()` - LLM API method
  - Model: `llama-3.3-70b-versatile` (configurable)

### Text-to-Speech
- **gtts** v2.5.0 - Google Text-to-Speech
  - `gTTS()` - TTS generator
- **pydub** v0.25.1 - Audio processing
  - `AudioSegment.from_mp3()` - MP3 loader
  - `audio.export(format="wav")` - WAV converter

### Request Handling
- **python-multipart** v0.0.6 - Multipart form data
- **pydantic** v2.5.0 - Data validation
- FastAPI `Form()` - Form data parsing
- FastAPI `Query()` - Query parameter parsing
- FastAPI `Request` - Request object

### Environment & Configuration
- **python-dotenv** v1.0.0 - Environment variable loading
- `.env` file - Configuration storage
- `os.getenv()` - Environment variable access

### Logging System
- **JSONLogger** - Custom logging class
- Python `logging` - Standard logging
- Python `json` - JSON serialization
- Python `datetime` - Timestamp generation
- `logs/app_logs.json` - Log file storage

### File Management
- Python `os` - Operating system interface
- Python `pathlib.Path` - Path handling
- `os.makedirs()` - Directory creation
- `os.path.exists()` - File existence check
- `audio_files/output/` - Audio storage directory

### Response Handling
- `Response` - HTTP response (FastAPI)
- `FileResponse` - File serving (FastAPI)

### HTTP Client
- **httpx** v0.25.1 - HTTP client library

### Async File Operations
- **aiofiles** v23.2.1 - Async file operations

## Backend API Endpoints

### Voice Endpoints
1. **POST /api/voice/incoming**
   - Handles incoming Twilio calls
   - Components: `Form()`, `VoiceResponse()`, `Say()`, `Gather()`, `JSONLogger`

2. **POST /api/voice/process**
   - Processes speech through AI pipeline
   - Components: `Form()`, `Query()`, `Request`, `get_llm_response()`, `generate_tts_audio()`, `VoiceResponse()`, `Play()`, `JSONLogger`

3. **GET /api/voice/audio/{filename}**
   - Serves audio files to Twilio
   - Components: `FileResponse`, `os.path.exists()`, `pathlib.Path`

### Chat Endpoints
4. **GET /api/chat**
   - Text chat via GET method
   - Components: `Query()`, `Groq()`, `JSONLogger`

5. **POST /api/chat**
   - Text chat via POST method
   - Components: `Form()`, `Groq()`, `JSONLogger`

### Status Endpoints
6. **GET /api/status**
   - Health check endpoint
   - Components: Basic response

### Twilio Configuration Endpoints
7. **GET /api/twilio/credentials**
   - Get Twilio configuration status
   - Components: `TWILIO_CREDENTIALS` dictionary

8. **POST /api/twilio/credentials**
   - Set and validate Twilio credentials
   - Components: `Form()`, `validate_twilio_credentials()`, `TwilioClient()`, `JSONLogger`

## Backend Helper Functions

1. **get_llm_response(messages, model)**
   - Calls Groq LLM API
   - Components: `groq_client`, `chat.completions.create()`

2. **generate_tts_audio(text, call_sid)**
   - Generates TTS audio file
   - Components: `gTTS()`, `AudioSegment`, file I/O

3. **validate_twilio_credentials(account_sid, auth_token, phone_number)**
   - Validates Twilio credential formats
   - Components: String validation, format checks

## Data Structures

### In-Memory Storage
- `conversations` - Dictionary storing conversation history per call
  - Key: `CallSid` (string)
  - Value: List of message dictionaries
  - Format: `[{"role": "system/user/assistant", "content": "text"}]`

- `TWILIO_CREDENTIALS` - Dictionary storing Twilio credentials
  - Keys: `account_sid`, `auth_token`, `phone_number`, `ui_set`

### File Storage
- `logs/app_logs.json` - Structured event logs
- `audio_files/output/` - Generated audio files (WAV format)

## External Services

### Twilio Cloud Platform
- Phone number management
- Webhook handling
- Speech Recognition (STT)
- Text-to-Speech (TTS) - Fallback service
- Call routing and management

### Groq API
- LLM service provider
- Model: llama-3.3-70b-versatile
- Endpoint: chat.completions.create
- Parameters: temperature=1, max_tokens=1024

### Google TTS (via gTTS)
- Text-to-speech service
- Generates MP3 audio files
- Language: English (en)

## Configuration Variables

### Environment Variables (.env)
- `GROQ_API_KEY` - Groq API key
- `GROQ_LLM_MODEL` - LLM model name
- `TWILIO_ACCOUNT_SID` - Twilio account SID
- `TWILIO_AUTH_TOKEN` - Twilio auth token
- `TWILIO_PHONE_NUMBER` - Twilio phone number
- `AUDIO_DIR` - Audio directory path
- `API_HOST` - API host address
- `PORT` - Server port (default: 7860)

### Application Constants
- `SYSTEM_PROMPT` - LLM system prompt
- `LLM_TEMPERATURE` - LLM temperature (1)
- `LLM_MAX_TOKENS` - Max tokens per response (1024)
- `CONVERSATION_HISTORY_LIMIT` - Max conversation messages (10)

## Standard Library Modules Used

### Python Standard Library
- `os` - Operating system interface
- `json` - JSON encoder/decoder
- `logging` - Logging facility
- `datetime` - Date and time handling
- `pathlib` - Path handling

## TwiML Verbs Used

1. **<Say>** - Text-to-speech output
   - Attributes: `voice="alice"`

2. **<Gather>** - Speech input collection
   - Attributes: `input="speech"`, `action`, `method="POST"`, `speech_timeout="auto"`

3. **<Play>** - Audio file playback
   - Attributes: `url` (audio file URL)

4. **<Hangup>** - Call termination

## File Structure

```
project/
├── main.py                 # FastAPI backend
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
├── logs/
│   └── app_logs.json      # Structured logs
├── audio_files/
│   └── output/            # Generated audio files
├── frontend/
│   ├── src/
│   │   ├── App.jsx        # Main React component
│   │   ├── App.css        # Component styles
│   │   ├── index.js       # React entry point
│   │   └── index.css      # Global styles
│   ├── package.json       # Node dependencies
│   └── build/             # Production build
└── ARCHITECTURE_*.md      # Architecture documentation
```

## Summary

### Total Components
- **Frontend**: 4 React components, 3 Browser APIs, 3 React hooks
- **Backend**: 8 API endpoints, 3 helper functions, 9 Python libraries
- **External Services**: 3 services (Twilio, Groq, Google TTS)
- **Data Storage**: 2 in-memory structures, 2 file storage locations

### Technology Stack Summary
- **Frontend**: React 18.2.0 + Web Speech API
- **Backend**: FastAPI 0.104.1 + Uvicorn 0.24.0
- **LLM**: Groq API (llama-3.3-70b-versatile)
- **TTS**: Google TTS (gTTS) + pydub
- **Voice**: Twilio Cloud Platform
- **Language**: Python 3.x, JavaScript (ES6+)

