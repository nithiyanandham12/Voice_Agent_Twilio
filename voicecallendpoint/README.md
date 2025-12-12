---
title: Voice AI Assistant
emoji: 🎙️
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
---

# Voice AI Assistant

Intelligent voice-powered conversation system with Twilio integration, Groq LLM, and real-time speech processing.

## Features

- 🎤 Real-time voice conversation
- 🤖 Groq LLM integration (Llama 3.3 70B)
- 📞 Twilio telephony support
- 🔊 Text-to-Speech (gTTS)
- 🎯 Barge-in interruption support
- 📊 Comprehensive logging

## API Endpoints

- `POST /api/voice/incoming` - Twilio webhook for incoming calls
- `POST /api/voice/process` - Process speech from Twilio
- `GET /api/voice/audio/{filename}` - Serve audio files
- `GET /api/chat` - Chat endpoint for frontend
- `POST /api/chat` - Chat endpoint (POST)
- `GET /api/status` - API status
- `GET /api/twilio/credentials` - Get Twilio credentials status
- `POST /api/twilio/credentials` - Set Twilio credentials

## Environment Variables

- `GROQ_API_KEY` - Your Groq API key
- `GROQ_LLM_MODEL` - LLM model (default: llama-3.3-70b-versatile)
- `TWILIO_ACCOUNT_SID` - Twilio Account SID (optional)
- `TWILIO_AUTH_TOKEN` - Twilio Auth Token (optional)
- `TWILIO_PHONE_NUMBER` - Twilio Phone Number (optional)

## Setup

1. Set your environment variables in Hugging Face Space settings
2. Configure Twilio webhook to point to your Space URL
3. Start making voice calls!
