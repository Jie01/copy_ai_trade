# Copy AI Trades

A Flask-based API application for processing and analyzing AI-generated trading data from the nof1.ai platform. This application fetches trade data, calculates profit/loss summaries, and prepares structured data for Telegram notifications.

## Features

- Parse and analyze completed trades from nof1.ai API
- Analyze current account positions and unrealized P&L
- Calculate total realized and unrealized P&L across all symbols
- RESTful API endpoints for accessing trade summaries
- Structured data preparation for Telegram bot integration

## Installation

1. Clone or navigate to the project directory:
   ```bash
   cd /mnt/c/Users/aukit/PycharmProjects/copy_ai_trades/test
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

Start the Flask development server:
```bash
python run.py
```

The API will be available at `http://localhost:5000`

### API Endpoints

#### GET /trades/summary
Returns summary statistics for completed trades.

**Response:**
```json
{
  "total_trades": 20,
  "total_realized_pnl": -467.48,
  "total_commission": 95.62,
  "total_gross_pnl": -378.97,
  "symbol_breakdown": {
    "SOL": {"realized_pnl": 106.83, "count": 4},
    "ETH": {"realized_pnl": -352.20, "count": 6}
  }
}
```

#### GET /account/summary
Returns summary of current account positions.

**Response:**
```json
{
  "realized_pnl": -32.91,
  "total_unrealized_pnl": 337.89,
  "total_margin": 5666.14,
  "total_commission": 65.82,
  "symbol_positions": {
    "XRP": {
      "unrealized_pnl": 174.34,
      "margin": 1670.58,
      "quantity": -7716,
      "current_price": 2.32,
      "entry_price": 2.34
    }
  },
  "total_positions": 5
}
```

#### GET /overall/summary
Returns combined summary of trades and account data.

**Response:**
```json
{
  "trades_summary": {...},
  "account_summary": {...},
  "overall": {
    "total_pnl": -162.50,
    "total_commission": 161.44
  }
}
```

#### GET /health
Health check endpoint.

**Response:**
```json
{"status": "healthy"}
```

## Data Flow

### 1. API Data Fetching
The application expects JSON responses from nof1.ai API endpoints:
- `/api/trades` - Completed trade history
- `/api/account-totals` - Current account positions and totals

Data files should be saved with the first two lines containing the request information:
```
request get https://nof1.ai/api/trades

{...json data...}
```

### 2. Data Processing
- **Trade Processing**: Parse completed trades, calculate realized P&L, commissions, and group by symbol
- **Account Processing**: Parse current positions, calculate unrealized P&L, margin usage
- **Summary Calculation**: Combine realized and unrealized P&L for overall portfolio performance

### 3. Telegram Integration Preparation
Before sending to Telegram, structure the data as follows:

**Trade Alert Format:**
```
🚀 New Trade Signal

Symbol: SOL
Side: Long
Quantity: 21.14
Entry Price: 189.28
Exit Price: 197.71
Realized P&L: $176.11
Commission: $2.10

Model: gpt-5
Timestamp: 2025-10-26 11:52:01
```

**Daily Summary Format:**
```
📊 Daily Trading Summary

Total Trades: 20
Realized P&L: $-467.48
Total Commission: $95.62

Top Performers:
SOL: +$106.83 (4 trades)
BTC: +$110.01 (2 trades)

Worst Performers:
ETH: -$352.20 (6 trades)
BNB: -$207.07 (3 trades)
```

**Position Update Format:**
```
📈 Current Positions

XRP: -7716 @ 2.32 (P&L: +$174.34)
BTC: -0.13 @ 106969.50 (P&L: +$12.73)
ETH: -6.21 @ 3854.15 (P&L: +$37.26)

Total Unrealized P&L: +$337.89
Used Margin: $5666.14
```

### 4. Telegram Bot Integration
1. Use Telegram Bot API to send messages
2. Format data using the structures above
3. Include emojis and clear formatting for readability
4. Send alerts for new trades, daily summaries, and position updates

## File Structure

```
.
├── app/
│   ├── __init__.py      # Flask app factory
│   └── routes.py        # API route definitions
├── trade_analyzer.py    # Standalone data analysis script
├── run.py              # Application entry point
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Dependencies

- Flask: Web framework
- Flask-RESTful: REST API support
- Flask-SQLAlchemy: Database ORM (for future extensions)
- Flask-Migrate: Database migrations
- Marshmallow: Data serialization
- Flask-JWT-Extended: Authentication (for future extensions)

## Development

### Running Tests
```bash
pytest
```

### Code Style
Follow PEP 8 guidelines and use type hints for all function signatures.

## License

This project is for educational and personal use only.