# Backend Installation Guide

Complete installation and setup guide for the Voice AI Assistant backend server.

## Prerequisites

- **Python 3.8 or higher** - [Download Python](https://www.python.org/downloads/)
- **pip** - Python package manager (usually comes with Python)
- **Groq API Key** - Get from [Groq Console](https://console.groq.com/)
- **Twilio Account** (optional, for voice calls) - Sign up at [Twilio](https://www.twilio.com/try-twilio)

## Step 1: Install Python Dependencies

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Step 2: Configure Environment Variables

Create a `.env` file in the `backend` directory:

```env
# Groq API Configuration (Required)
GROQ_API_KEY=your_groq_api_key_here
GROQ_LLM_MODEL=llama-3.3-70b-versatile

# Server Configuration
PORT=8000
API_HOST=0.0.0.0
AUDIO_DIR=audio_files

# Twilio Configuration (Optional - can be set via UI)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

### Getting Your Groq API Key

1. Go to [Groq Console](https://console.groq.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key and paste it in your `.env` file

## Step 3: Twilio Setup (For Voice Calls)

### 3.1 Create Twilio Account

1. Sign up at [Twilio](https://www.twilio.com/try-twilio)
2. Verify your email and phone number
3. Complete account setup

### 3.2 Get Twilio Credentials

1. Log in to [Twilio Console](https://console.twilio.com/)
2. Find your **Account SID** and **Auth Token** on the dashboard
3. Copy these values to your `.env` file:
   ```env
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token_here
   ```

### 3.3 Get a Twilio Phone Number

1. In Twilio Console, go to **Phone Numbers** → **Manage** → **Buy a number**
2. Choose a phone number (or use a trial number)
3. Copy the phone number (with country code, e.g., +1234567890)
4. Add it to your `.env` file:
   ```env
   TWILIO_PHONE_NUMBER=+1234567890
   ```

### 3.4 Configure Twilio Webhook

1. In Twilio Console, go to **Phone Numbers** → **Manage** → **Active numbers**
2. Click on your phone number
3. Scroll down to **Voice & Fax** section
4. Under **A CALL COMES IN**, set:
   - **Webhook URL**: `https://your-domain.com/api/voice/incoming`
   - **HTTP Method**: `POST`
5. Click **Save**

**Note**: For local development, use a tunneling service like:
- [ngrok](https://ngrok.com/) - `ngrok http 8000`
- [localtunnel](https://localtunnel.github.io/www/) - `lt --port 8000`

Then use the provided URL: `https://your-ngrok-url.ngrok.io/api/voice/incoming`

### 3.5 Alternative: Set Credentials via API

You can also set Twilio credentials via the API endpoint after starting the server:

```bash
curl -X POST http://localhost:8000/api/twilio/credentials \
  -F "account_sid=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" \
  -F "auth_token=your_auth_token" \
  -F "phone_number=+1234567890"
```

## Step 4: Run the Server

### Development Mode

```bash
python main.py
```

The server will start on `http://localhost:8000` (or the port specified in `.env`)

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Step 5: Verify Installation

1. Check if the server is running:
```bash
curl http://localhost:8000/api/status
```

Expected response:
```json
{
  "status": "running",
  "model": "llama-3.3-70b-versatile",
  "endpoints": { ... }
}
```

2. Test the chat endpoint:
```bash
curl "http://localhost:8000/api/chat?message=Hello"
```

## Directory Structure

After installation, your backend directory should look like:

```
backend/
├── main.py              # Main application file
├── requirements.txt     # Python dependencies
├── INSTALLATION.md      # This file
├── .env                 # Environment variables (create this)
├── logs/                # Auto-created log directory
│   └── app_logs.json   # Application logs
└── audio_files/         # Auto-created audio directory
    └── output/         # Generated audio files
```

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:
```bash
# Change PORT in .env file
PORT=8001

# Or specify port when running
uvicorn main:app --port 8001
```

### Module Not Found Error

Make sure you've activated your virtual environment and installed dependencies:
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Groq API Key Error

- Verify your API key is correct in `.env` file
- Check if you have API credits/quota in Groq Console
- Ensure `GROQ_API_KEY` variable name is correct (case-sensitive)

### Twilio Connection Issues

1. **Verify credentials format**:
   - Account SID should start with "AC" and be ~34 characters
   - Auth Token should be ~32 characters
   - Phone number should start with "+" and include country code

2. **Test credentials**:
```bash
curl -X POST http://localhost:8000/api/twilio/credentials \
  -F "account_sid=YOUR_SID" \
  -F "auth_token=YOUR_TOKEN" \
  -F "phone_number=YOUR_NUMBER"
```

3. **Check webhook URL**:
   - Must be publicly accessible (use ngrok for local testing)
   - Must use HTTPS in production
   - Must point to `/api/voice/incoming` endpoint

### Audio File Issues

- Ensure `audio_files/output/` directory exists and is writable
- Check disk space for audio file storage
- Verify `AUDIO_DIR` path in `.env` is correct

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | Yes | - | Your Groq API key |
| `GROQ_LLM_MODEL` | No | `llama-3.3-70b-versatile` | LLM model to use |
| `PORT` | No | `8000` | Server port |
| `API_HOST` | No | `0.0.0.0` | Server host |
| `AUDIO_DIR` | No | `audio_files` | Audio files directory |
| `TWILIO_ACCOUNT_SID` | No* | - | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | No* | - | Twilio Auth Token |
| `TWILIO_PHONE_NUMBER` | No* | - | Twilio Phone Number |

*Required only for voice call functionality

## Next Steps

- Configure your frontend to connect to this backend
- Test voice calls using your Twilio phone number
- Check logs in `logs/app_logs.json` for debugging
- Review API endpoints in main README.md

## Support

For issues or questions:
- Check the main README.md for API documentation
- Review logs in `logs/app_logs.json`
- Verify all environment variables are set correctly

