# NoF1 Trading Reporter Setup Script
# Run this script to set up the environment and test the reporter

Write-Host "🚀 Setting up NoF1 Trading Reporter..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8+ first." -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Test the script
Write-Host "🧪 Testing the script with dry-run..." -ForegroundColor Yellow
python nof1_trading_reporter.py --dry-run

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Script test completed successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Script test failed" -ForegroundColor Red
    exit 1
}

# Setup instructions
Write-Host "`n📋 Setup Instructions:" -ForegroundColor Cyan
Write-Host "1. Get a Telegram Bot Token from @BotFather" -ForegroundColor White
Write-Host "2. Get your Chat ID (send a message to your bot and visit:" -ForegroundColor White
Write-Host "   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates" -ForegroundColor White
Write-Host "3. Set environment variables:" -ForegroundColor White
Write-Host "   `$env:TELEGRAM_BOT_TOKEN = 'your_bot_token_here'" -ForegroundColor White
Write-Host "   `$env:TELEGRAM_CHAT_ID = 'your_chat_id_here'" -ForegroundColor White
Write-Host "4. Run the script:" -ForegroundColor White
Write-Host "   python nof1_trading_reporter.py" -ForegroundColor White
Write-Host "`n🔄 To run periodically, add to Windows Task Scheduler or use cron" -ForegroundColor Yellow

Write-Host "`n🎉 Setup completed! The script is ready to use." -ForegroundColor Green

