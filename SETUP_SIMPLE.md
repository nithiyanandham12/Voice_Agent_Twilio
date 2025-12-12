# Simple Setup Guide

## Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set environment variables:**
Create a `.env` file with:
```env
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890
GROQ_API_KEY=your_groq_api_key
```

3. **Run the server:**
```bash
python main.py
```

4. **Configure Twilio webhook:**
- Use ngrok: `ngrok http 8000`
- Set Twilio webhook to: `https://your-ngrok-url.ngrok.io/api/voice/incoming`

5. **Call your Twilio number and speak!**

## Simple Flow

```
User speaks → Twilio STT → Text → Groq LLM → Response Text → TTS → Audio → User hears
```

That's it! The system handles everything automatically.

