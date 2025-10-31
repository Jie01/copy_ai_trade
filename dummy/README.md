# NoF1 AI Trading Data Reporter

A production-ready Python script that automates fetching, processing, and reporting trading data from the NoF1 AI platform for specific AI models (Deepseek, Qwen, Grok, Claude).

## Features

- 🔄 **Automated Data Fetching**: Retrieves data from NoF1 APIs (account totals and trades)
- 🎯 **Smart Filtering**: Focuses on target models while excluding unwanted ones
- 📊 **Comprehensive Reporting**: Generates detailed trading reports with positions and recent trades
- 📱 **Telegram Integration**: Sends formatted reports directly to Telegram
- 🛡️ **Robust Error Handling**: Retry logic, graceful degradation, and comprehensive logging
- ⚙️ **Flexible Configuration**: Command-line arguments and environment variables
- 🧪 **Dry Run Mode**: Test the script without sending messages

## Quick Start

### 1. Setup Environment

```powershell
# Run the setup script
.\setup.ps1
```

### 2. Configure Telegram

Get your Telegram credentials:

1. **Bot Token**: Message @BotFather on Telegram and create a new bot
2. **Chat ID**: Send a message to your bot, then visit:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
   Find your chat ID in the response

### 3. Set Environment Variables

```powershell
$env:TELEGRAM_BOT_TOKEN = "your_bot_token_here"
$env:TELEGRAM_CHAT_ID = "your_chat_id_here"
```

### 4. Run the Script

```powershell
# Test with dry run
python nof1_trading_reporter.py --dry-run

# Send to Telegram
python nof1_trading_reporter.py
```

## Usage

### Command Line Options

```bash
python nof1_trading_reporter.py [options]

Options:
  --dry-run              Print report to console instead of sending to Telegram
  --models MODEL [MODEL ...]  Override target models (space-separated)
  --log-level LEVEL      Set logging level (DEBUG, INFO, WARNING, ERROR)
  -h, --help             Show help message
```

### Examples

```bash
# Basic usage
python nof1_trading_reporter.py

# Test without sending messages
python nof1_trading_reporter.py --dry-run

# Use only specific models
python nof1_trading_reporter.py --models deepseek qwen

# Debug mode
python nof1_trading_reporter.py --log-level DEBUG
```

## Scheduled Execution

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., every 30 minutes)
4. Set action to start program: `python`
5. Add arguments: `C:\path\to\nof1_trading_reporter.py`
6. Set start in: `C:\path\to\script\directory`

### Cron (Linux/Mac)

```bash
# Add to crontab (runs every 30 minutes)
*/30 * * * * /usr/bin/python3 /path/to/nof1_trading_reporter.py
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | Yes (unless --dry-run) |
| `TELEGRAM_CHAT_ID` | Target chat ID | Yes (unless --dry-run) |

### Target Models

By default, the script monitors these models:
- **Deepseek** (e.g., 'deepseek-chat-v3.1')
- **Qwen** (e.g., 'qwen3-max')
- **Grok** (e.g., 'grok-4')
- **Claude** (e.g., 'claude-sonnet-4-5')

Excluded models:
- **Gemini** (any variant)
- **GPT-5** (any variant)

## Report Format

The script generates Markdown-formatted reports with:

### Header
```
🚀 NoF1 AI Trading Update - 2025-01-26 15:30:00
Models: Deepseek, Qwen, Grok, Claude
```

### Per-Model Sections
```
*Deepseek*
Stats: PnL: $1,234.56 | Equity: $10,000.00 | Unrealized: $567.89 | Sharpe: 1.23
Open Positions:
- BTC Long | Qty: 0.05 | Entry: $45,000.00 | Current: $46,000.00 | PnL: $50.00 | Lev: 1x | Conf: 0.85
Recent Trades:
- ETH Long | Entry: $3,000.00 (01/25 14:30) | Exit: $3,100.00 (01/25 16:45) | PnL: $100.00
```

## API Endpoints

The script fetches data from these public NoF1 APIs:

- **Account Totals**: `https://nof1.ai/api/account-totals`
- **Trades**: `https://nof1.ai/api/trades`

No authentication is required for these endpoints.

## Error Handling

The script includes comprehensive error handling:

- **Network Issues**: Automatic retries with exponential backoff
- **API Failures**: Graceful degradation if one API fails
- **Data Validation**: Handles malformed JSON and missing fields
- **Telegram Issues**: Logs errors and continues execution
- **Logging**: Detailed logs for debugging and monitoring

## Logging

Logs are written to both console and `nof1_reporter.log` file with timestamps and severity levels.

## Dependencies

- Python 3.8+
- requests >= 2.31.0
- urllib3 >= 2.0.0

## File Structure

```
├── nof1_trading_reporter.py  # Main script
├── requirements.txt           # Python dependencies
├── setup.ps1                # Windows setup script
├── README.md                # This file
└── nof1_reporter.log       # Log file (created on first run)
```

## Troubleshooting

### Common Issues

1. **"Telegram credentials not found"**
   - Set the environment variables correctly
   - Use `--dry-run` to test without Telegram

2. **"Failed to fetch data from APIs"**
   - Check internet connection
   - Verify API endpoints are accessible
   - Check logs for specific error messages

3. **"No data found for target models"**
   - Verify model names in the data
   - Use `--log-level DEBUG` to see filtering details
   - Check if models are active in NoF1

### Debug Mode

Run with debug logging to see detailed information:

```bash
python nof1_trading_reporter.py --log-level DEBUG --dry-run
```

## Contributing

This script is designed to be easily extensible:

- Add new models by updating `TARGET_MODELS`
- Modify report format in `generate_model_report()`
- Add new data sources by extending `fetch_api_data()`

## License

This script is provided as-is for educational and personal use. Please respect NoF1's API terms of service.

