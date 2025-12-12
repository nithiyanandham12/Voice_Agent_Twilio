# Deployment script for Hugging Face Spaces
# Run this script to deploy the backend

Write-Host "🚀 Deploying Voice AI Assistant to Hugging Face Spaces" -ForegroundColor Green
Write-Host ""

# Check if git is available
try {
    git --version | Out-Null
    Write-Host "✅ Git is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Git is not installed. Please install Git first." -ForegroundColor Red
    Write-Host "Download from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# Check if hf CLI is available
try {
    hf --version | Out-Null
    Write-Host "✅ Hugging Face CLI is installed" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Hugging Face CLI not found. Installing..." -ForegroundColor Yellow
    powershell -ExecutionPolicy ByPass -c "irm https://hf.co/cli/install.ps1 | iex"
}

Write-Host ""
Write-Host "Step 1: Clone the Space repository..." -ForegroundColor Cyan
Write-Host "If the directory already exists, it will be skipped." -ForegroundColor Yellow

$spaceDir = "voicecallendpoint"
if (Test-Path $spaceDir) {
    Write-Host "Directory exists, skipping clone. Use 'cd $spaceDir' to continue." -ForegroundColor Yellow
} else {
    Write-Host "Cloning repository..." -ForegroundColor Cyan
    Write-Host "When prompted for password, use your Hugging Face access token" -ForegroundColor Yellow
    Write-Host "Get token from: https://huggingface.co/settings/tokens" -ForegroundColor Yellow
    git clone https://huggingface.co/spaces/Nithiyanandham15/voicecallendpoint
}

Write-Host ""
Write-Host "Step 2: Copy files to space directory..." -ForegroundColor Cyan

if (Test-Path $spaceDir) {
    Copy-Item -Path "main.py" -Destination "$spaceDir\main.py" -Force
    Copy-Item -Path "requirements.txt" -Destination "$spaceDir\requirements.txt" -Force
    Copy-Item -Path "Dockerfile" -Destination "$spaceDir\Dockerfile" -Force
    Copy-Item -Path ".dockerignore" -Destination "$spaceDir\.dockerignore" -Force
    Copy-Item -Path "README.md" -Destination "$spaceDir\README.md" -Force
    
    Write-Host "✅ Files copied successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Space directory not found. Please clone the repository first." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 3: Navigate to space directory and commit..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Run these commands:" -ForegroundColor Yellow
Write-Host "  cd $spaceDir" -ForegroundColor White
Write-Host "  git add main.py requirements.txt Dockerfile .dockerignore README.md" -ForegroundColor White
Write-Host "  git commit -m 'Add Voice AI Assistant backend'" -ForegroundColor White
Write-Host "  git push" -ForegroundColor White
Write-Host ""
Write-Host "Don't forget to set environment variables in Space settings!" -ForegroundColor Yellow
Write-Host "Required: GROQ_API_KEY" -ForegroundColor Yellow
Write-Host "Optional: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER" -ForegroundColor Yellow

