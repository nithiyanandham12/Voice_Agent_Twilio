# Voice AI Assistant with Twilio

Intelligent voice-powered conversation system with Twilio integration, Groq LLM, and real-time speech processing.

## Features

- 🎤 Real-time voice conversation
- 🤖 Groq LLM integration (Llama 3.3 70B)
- 📞 Twilio telephony support
- 🔊 Text-to-Speech (gTTS)
- 🎯 Barge-in interruption support
- 📊 Comprehensive logging
- 💬 Web-based chat interface

## Project Structure

```
Voice_Agent_Twilio/
├── backend/           # FastAPI backend server
│   ├── main.py       # Main application file
│   └── requirements.txt
├── frontend/         # React frontend application
│   ├── src/          # React source files
│   └── package.json
└── README.md         # This file
```

## Backend Setup

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the backend directory:
```env
GROQ_API_KEY=your_groq_api_key
GROQ_LLM_MODEL=llama-3.3-70b-versatile
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890
PORT=8000
```

4. Run the server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## Frontend Setup

### Prerequisites

- Node.js 14+
- npm or yarn

### Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file in the frontend directory (optional):
```env
REACT_APP_API_URL=http://localhost:8000
```

4. Start the development server:
```bash
npm start
```

The frontend will be available at `http://localhost:3000`

## API Endpoints

### Voice Endpoints

- `POST /api/voice/incoming` - Twilio webhook for incoming calls
- `POST /api/voice/process` - Process speech from Twilio
- `GET /api/voice/audio/{filename}` - Serve audio files

### Chat Endpoints

- `GET /api/chat?message={text}` - Chat endpoint (GET)
- `POST /api/chat` - Chat endpoint (POST)

### Status & Configuration

- `GET /api/status` - API status check
- `GET /api/twilio/credentials` - Get Twilio credentials status
- `POST /api/twilio/credentials` - Set Twilio credentials

## Twilio Configuration

1. Get your Twilio credentials from [Twilio Console](https://console.twilio.com/)
2. Configure your Twilio phone number webhook:
   - **Webhook URL**: `https://your-domain.com/api/voice/incoming`
   - **Method**: POST
3. Set credentials via API endpoint or environment variables

## Environment Variables

### Backend

- `GROQ_API_KEY` - Your Groq API key (required)
- `GROQ_LLM_MODEL` - LLM model (default: llama-3.3-70b-versatile)
- `TWILIO_ACCOUNT_SID` - Twilio Account SID (optional)
- `TWILIO_AUTH_TOKEN` - Twilio Auth Token (optional)
- `TWILIO_PHONE_NUMBER` - Twilio Phone Number (optional)
- `PORT` - Server port (default: 8000)
- `AUDIO_DIR` - Audio files directory (default: audio_files)

### Frontend

- `REACT_APP_API_URL` - Backend API URL (default: production URL)

## Technology Stack

### Backend
- FastAPI 0.104.1
- Groq LLM SDK
- Twilio SDK
- Google TTS (gTTS)
- pydub (audio processing)

### Frontend
- React 18.2.0
- Web Speech API
- Fetch API

## Browser Support

- **Chrome/Edge**: Full support for speech recognition and synthesis
- **Firefox**: Limited speech recognition support
- **Safari**: Limited speech recognition support

For best results, use Chrome or Edge browser.

## Documentation

- [UI Architecture](./ARCHITECTURE_UI.md) - Frontend architecture details
- [Twilio Architecture](./ARCHITECTURE_TWILIO.md) - Twilio integration details
- [Components List](./COMPONENTS_LIST.md) - Complete component reference

## License

MIT
