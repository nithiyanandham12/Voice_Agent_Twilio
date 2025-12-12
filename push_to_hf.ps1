# Script to push backend to Hugging Face Spaces
# This script will help you deploy the Voice AI Assistant backend

Write-Host "🚀 Deploying Voice AI Assistant to Hugging Face Spaces" -ForegroundColor Green
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "main.py")) {
    Write-Host "❌ Error: main.py not found. Please run this script from the project root." -ForegroundColor Red
    exit 1
}

# Check if git is available
$gitAvailable = $false
try {
    $gitVersion = git --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $gitAvailable = $true
        Write-Host "✅ Git is available" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Git check failed, will try anyway..." -ForegroundColor Yellow
}

if (-not $gitAvailable) {
    Write-Host "❌ Git is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "After installing Git, run this script again." -ForegroundColor Yellow
    exit 1
}

# Check if space directory exists
$spaceDir = "voicecallendpoint"
if (Test-Path $spaceDir) {
    Write-Host "✅ Space directory exists: $spaceDir" -ForegroundColor Green
    Set-Location $spaceDir
} else {
    Write-Host "📦 Cloning Hugging Face Space repository..." -ForegroundColor Cyan
    Write-Host "When prompted for password, use your Hugging Face access token" -ForegroundColor Yellow
    Write-Host "Get token from: https://huggingface.co/settings/tokens" -ForegroundColor Yellow
    Write-Host ""
    
    git clone https://huggingface.co/spaces/Nithiyanandham15/voicecallendpoint
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to clone repository. Please check:" -ForegroundColor Red
        Write-Host "   1. You have access to the repository" -ForegroundColor Yellow
        Write-Host "   2. You're logged in with: hf login" -ForegroundColor Yellow
        Write-Host "   3. You have the correct access token" -ForegroundColor Yellow
        exit 1
    }
    
    Set-Location $spaceDir
}

Write-Host ""
Write-Host "📋 Copying files to space directory..." -ForegroundColor Cyan

# Copy files
Copy-Item -Path "..\main.py" -Destination "main.py" -Force
Copy-Item -Path "..\requirements.txt" -Destination "requirements.txt" -Force
Copy-Item -Path "..\Dockerfile" -Destination "Dockerfile" -Force
Copy-Item -Path "..\.dockerignore" -Destination ".dockerignore" -Force
Copy-Item -Path "..\README.md" -Destination "README.md" -Force

Write-Host "✅ Files copied successfully" -ForegroundColor Green

Write-Host ""
Write-Host "📝 Checking git status..." -ForegroundColor Cyan
git status

Write-Host ""
Write-Host "➕ Adding files to git..." -ForegroundColor Cyan
git add main.py requirements.txt Dockerfile .dockerignore README.md

Write-Host ""
Write-Host "💾 Committing changes..." -ForegroundColor Cyan
git commit -m "Add Voice AI Assistant backend - Production ready"

Write-Host ""
Write-Host "🚀 Pushing to Hugging Face Spaces..." -ForegroundColor Cyan
Write-Host "This may prompt for your Hugging Face credentials." -ForegroundColor Yellow
git push

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Successfully pushed to Hugging Face Spaces!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📌 Next steps:" -ForegroundColor Cyan
    Write-Host "   1. Go to: https://huggingface.co/spaces/Nithiyanandham15/voicecallendpoint/settings" -ForegroundColor Yellow
    Write-Host "   2. Add environment variables:" -ForegroundColor Yellow
    Write-Host "      - GROQ_API_KEY (required)" -ForegroundColor White
    Write-Host "      - GROQ_LLM_MODEL (optional, default: llama-3.3-70b-versatile)" -ForegroundColor White
    Write-Host "      - TWILIO_ACCOUNT_SID (optional)" -ForegroundColor White
    Write-Host "      - TWILIO_AUTH_TOKEN (optional)" -ForegroundColor White
    Write-Host "      - TWILIO_PHONE_NUMBER (optional)" -ForegroundColor White
    Write-Host "   3. Wait for the Space to build (usually 2-5 minutes)" -ForegroundColor Yellow
    Write-Host "   4. Your API will be available at:" -ForegroundColor Yellow
    Write-Host "      https://Nithiyanandham15-voicecallendpoint.hf.space" -ForegroundColor White
    Write-Host "   5. Update Twilio webhook to:" -ForegroundColor Yellow
    Write-Host "      https://Nithiyanandham15-voicecallendpoint.hf.space/api/voice/incoming" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "❌ Push failed. Please check:" -ForegroundColor Red
    Write-Host "   1. You're authenticated: hf login" -ForegroundColor Yellow
    Write-Host "   2. You have write access to the repository" -ForegroundColor Yellow
    Write-Host "   3. Your access token has write permissions" -ForegroundColor Yellow
}

Set-Location ..

