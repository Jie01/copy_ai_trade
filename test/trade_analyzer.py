import json
import os
from typing import Dict, List, Any

def load_json_from_file(file_path: str) -> Dict[str, Any]:
    """Load JSON data from a file, skipping the first two lines which contain the request."""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    # Skip the first two lines: "request get ..." and empty line
    json_content = ''.join(lines[2:])
    return json.loads(json_content)

def analyze_trades(trades_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze the trades data and return summary statistics."""
    trades = trades_data.get('trades', [])
    total_realized_pnl = sum(trade['realized_net_pnl'] for trade in trades)
    total_commission = sum(trade['total_commission_dollars'] for trade in trades)
    total_gross_pnl = sum(trade['realized_gross_pnl'] for trade in trades)

    # Group by symbol
    symbol_pnl = {}
    for trade in trades:
        symbol = trade['symbol']
        if symbol not in symbol_pnl:
            symbol_pnl[symbol] = {'realized_pnl': 0, 'count': 0}
        symbol_pnl[symbol]['realized_pnl'] += trade['realized_net_pnl']
        symbol_pnl[symbol]['count'] += 1

    return {
        'total_trades': len(trades),
        'total_realized_pnl': total_realized_pnl,
        'total_commission': total_commission,
        'total_gross_pnl': total_gross_pnl,
        'symbol_breakdown': symbol_pnl
    }

def analyze_account_totals(account_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze the account totals data and return summary statistics."""
    account_totals = account_data.get('accountTotals', [])
    if not account_totals:
        return {}

    # Assuming single account total for simplicity
    account = account_totals[0]
    realized_pnl = account.get('realized_pnl', 0)
    positions = account.get('positions', {})

    total_unrealized_pnl = sum(pos['unrealized_pnl'] for pos in positions.values())
    total_margin = sum(pos['margin'] for pos in positions.values())
    total_commission = sum(pos['commission'] for pos in positions.values())

    # Group by symbol
    symbol_positions = {}
    for symbol, pos in positions.items():
        symbol_positions[symbol] = {
            'unrealized_pnl': pos['unrealized_pnl'],
            'margin': pos['margin'],
            'quantity': pos['quantity'],
            'current_price': pos['current_price'],
            'entry_price': pos['entry_price']
        }

    return {
        'realized_pnl': realized_pnl,
        'total_unrealized_pnl': total_unrealized_pnl,
        'total_margin': total_margin,
        'total_commission': total_commission,
        'symbol_positions': symbol_positions,
        'total_positions': len(positions)
    }

def main():
    # File paths
    trades_file = '/mnt/c/Users/aukit/PycharmProjects/copy_ai_trades/web_response.txt'
    account_file = '/mnt/c/Users/aukit/PycharmProjects/copy_ai_trades/account_total.txt'

    # Load data
    trades_data = load_json_from_file(trades_file)
    account_data = load_json_from_file(account_file)

    # Analyze
    trades_summary = analyze_trades(trades_data)
    account_summary = analyze_account_totals(account_data)

    # Combine summaries
    total_pnl = trades_summary['total_realized_pnl'] + account_summary.get('realized_pnl', 0) + account_summary.get('total_unrealized_pnl', 0)

    summary = {
        'trades_summary': trades_summary,
        'account_summary': account_summary,
        'overall': {
            'total_pnl': total_pnl,
            'total_commission': trades_summary['total_commission'] + account_summary.get('total_commission', 0)
        }
    }

    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()