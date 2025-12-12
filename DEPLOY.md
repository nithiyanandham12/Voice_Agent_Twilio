# Deploy to Hugging Face Spaces

## Prerequisites

1. Install Git (if not already installed)
2. Install Hugging Face CLI (if not already installed)
3. Get your Hugging Face access token with write permissions

## Step 1: Install Hugging Face CLI

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://hf.co/cli/install.ps1 | iex"
```

## Step 2: Login to Hugging Face

```powershell
hf login
```

Enter your access token when prompted.

## Step 3: Clone the Space Repository

```powershell
# When prompted for a password, use an access token with write permissions.
# Generate one from your settings: https://huggingface.co/settings/tokens
git clone https://huggingface.co/spaces/Nithiyanandham15/voicecallendpoint
```

## Step 4: Copy Files to Space Directory

Copy these files to the cloned space directory:
- `main.py`
- `requirements.txt`
- `Dockerfile`
- `.dockerignore`
- `README.md`

## Step 5: Commit and Push

```powershell
cd voicecallendpoint
git add main.py requirements.txt Dockerfile .dockerignore README.md
git commit -m "Add Voice AI Assistant backend"
git push
```

## Step 6: Set Environment Variables

1. Go to your Space settings: https://huggingface.co/spaces/Nithiyanandham15/voicecallendpoint/settings
2. Add these secrets:
   - `GROQ_API_KEY` - Your Groq API key
   - `GROQ_LLM_MODEL` - (Optional) Default: llama-3.3-70b-versatile
   - `TWILIO_ACCOUNT_SID` - (Optional) Your Twilio Account SID
   - `TWILIO_AUTH_TOKEN` - (Optional) Your Twilio Auth Token
   - `TWILIO_PHONE_NUMBER` - (Optional) Your Twilio Phone Number

## Step 7: Configure Twilio Webhook

Once your Space is running, update your Twilio webhook URL to:
```
https://Nithiyanandham15-voicecallendpoint.hf.space/api/voice/incoming
```

## Notes

- The app will run on port 7860 (required by Hugging Face Spaces)
- Make sure your Space is set to "Docker" SDK type
- The frontend React app should be deployed separately or integrated

