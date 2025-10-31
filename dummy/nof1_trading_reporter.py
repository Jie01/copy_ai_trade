#!/usr/bin/env python3
"""
NoF1 AI Trading Data Reporter

A standalone script that fetches, deduplicates, reports, and sends updates
for NoF1 AI trading data (Deepseek, Qwen, Grok, Claude), excluding Gemini and GPT-5.

Features:
- Robust HTTP retries for API calls
- Persistent JSON record to avoid duplicate Telegram updates
- Markdown-formatted report with only new/updated positions/trades
- Telegram sending via python-telegram-bot
- Runs every minute, graceful shutdown

Author: AI Assistant
Version: 2.0
"""

import argparse
import asyncio
import hashlib
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from telegram import Bot  # python-telegram-bot v20+
except Exception as _e:  # pragma: no cover
    Bot = None  # type: ignore


# Constants and configuration
API_ACCOUNT_TOTALS = 'https://nof1.ai/api/account-totals'
API_TRADES = 'https://nof1.ai/api/trades'

TARGET_MODELS = ['deepseek', 'qwen', 'grok', 'claude']
EXCLUDED_MODELS = ['gemini', 'gpt-5']

RECORD_FILE = 'nof1_data_record.json'
LOG_FILE = 'nof1_reporter.log'

MAX_RETRIES = 3
RETRY_BACKOFF = 1.0  # seconds, exponential backoff factor
HTTP_TIMEOUT = 30

# Telegram placeholders (can be overridden by env vars or CLI flags)
BOT_TOKEN = '8244913614:AAFZMf0hWvlEUWy0BXMcV8vy_UKIV3RCOp8'
CHAT_ID = '@copy_ai_trade_group'


def setup_logging(log_level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_FILE)
        ],
    )


def create_http_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_BACKOFF,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def normalize_model_name(raw_name: str) -> str:
    if not raw_name:
        return ''
    lower = raw_name.lower()
    if any(ex in lower for ex in EXCLUDED_MODELS):
        return ''
    for t in TARGET_MODELS:
        if t in lower:
            return t.capitalize()
    return ''


def fetch_data(session: requests.Session, url: str) -> Optional[Dict[str, Any]]:
    try:
        logging.info(f"Fetching: {url}")
        res = session.get(url, timeout=HTTP_TIMEOUT)
        res.raise_for_status()
        data = res.json()
        logging.info(f"Fetch OK: {url}")
        return data
    except requests.RequestException as e:
        logging.error(f"HTTP error for {url}: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"JSON error for {url}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error for {url}: {e}")
        return None


def load_record() -> Dict[str, Any]:
    if not os.path.exists(RECORD_FILE):
        return {}
    try:
        with open(RECORD_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load record file: {e}")
        return {}


def save_record(data: Dict[str, Any]) -> None:
    try:
        tmp_path = RECORD_FILE + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, RECORD_FILE)
    except Exception as e:
        logging.error(f"Failed to save record file: {e}")


def stable_hash(value: Any) -> str:
    try:
        serialized = json.dumps(value, sort_keys=True, ensure_ascii=False)
    except Exception:
        serialized = str(value)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def parse_account_totals(raw: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    if not raw:
        return result

    # Support multiple possible shapes
    models = []
    if isinstance(raw.get('models'), list):
        models = raw['models']
    elif isinstance(raw.get('accountTotals'), list):
        models = raw['accountTotals']

    for item in models:
        # Try to detect model name keys
        raw_name = (
            item.get('name')
            or item.get('id')
            or item.get('model')
            or item.get('model_id')
            or ''
        )
        model_name = normalize_model_name(str(raw_name))
        if not model_name:
            continue

        pnl = item.get('pnl') or item.get('realized_pnl') or 0.0
        equity = item.get('equity') or item.get('dollar_equity') or 0.0
        unreal = item.get('unrealized') or item.get('total_unrealized_pnl') or 0.0
        sharpe = item.get('sharpe') or item.get('sharpe_ratio') or 0.0

        result[model_name] = {
            'pnl': float(pnl) if isinstance(pnl, (int, float)) else 0.0,
            'equity': float(equity) if isinstance(equity, (int, float)) else 0.0,
            'unrealized': float(unreal) if isinstance(unreal, (int, float)) else 0.0,
            'sharpe': float(sharpe) if isinstance(sharpe, (int, float)) else 0.0,
        }
    return result


def parse_trades(raw: Dict[str, Any]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    result: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    if not raw:
        return result

    models = []
    if isinstance(raw.get('models'), list):
        models = raw['models']
    elif isinstance(raw.get('trades'), list):
        # Some APIs may return a flat list; group by model
        for t in raw['trades']:
            name = normalize_model_name(str(t.get('model_id') or t.get('model') or t.get('name') or ''))
            if not name:
                continue
            if name not in result:
                result[name] = {'open_positions': [], 'recent_trades': []}
            result[name]['recent_trades'].append({
                'asset': t.get('symbol') or t.get('asset') or 'Unknown',
                'side': (t.get('side') or '').capitalize() or 'Unknown',
                'entry': t.get('entry_price') or t.get('entry') or 0.0,
                'entry_time': t.get('entry_human_time') or t.get('entry_time') or '',
                'exit': t.get('exit_price') or t.get('exit') or 0.0,
                'exit_time': t.get('exit_human_time') or t.get('exit_time') or '',
                'pnl': t.get('realized_net_pnl') or t.get('pnl') or 0.0,
            })
        return result

    for item in models:
        raw_name = (
            item.get('name')
            or item.get('model')
            or item.get('model_id')
            or ''
        )
        model_name = normalize_model_name(str(raw_name))
        if not model_name:
            continue

        open_positions_raw = item.get('open_positions') or item.get('positions') or []
        recent_trades_raw = item.get('recent_trades') or item.get('trades') or []

        open_positions: List[Dict[str, Any]] = []
        for p in open_positions_raw or []:
            qty_val = p.get('qty') if p.get('qty') is not None else p.get('quantity')
            qty = float(qty_val) if isinstance(qty_val, (int, float)) else 0.0
            side = (p.get('side') or '').capitalize() or ('Long' if qty > 0 else 'Short')
            lev_val = p.get('lev') or p.get('leverage') or '1x'
            lev = f"{lev_val}" if isinstance(lev_val, str) else f"{lev_val}x"
            open_positions.append({
                'asset': p.get('asset') or p.get('symbol') or 'Unknown',
                'side': side,
                'qty': qty,
                'entry': p.get('entry') or p.get('entry_price') or 0.0,
                'current': p.get('current') or p.get('current_price') or 0.0,
                'pnl': p.get('pnl') or p.get('unrealized_pnl') or 0.0,
                'lev': lev,
                'conf': float(p.get('conf') or p.get('confidence') or 0.0),
            })

        recent_trades: List[Dict[str, Any]] = []
        for t in recent_trades_raw or []:
            recent_trades.append({
                'asset': t.get('asset') or t.get('symbol') or 'Unknown',
                'side': (t.get('side') or '').capitalize() or 'Unknown',
                'entry': t.get('entry') or t.get('entry_price') or 0.0,
                'entry_time': t.get('entry_time') or t.get('entry_human_time') or '',
                'exit': t.get('exit') or t.get('exit_price') or 0.0,
                'exit_time': t.get('exit_time') or t.get('exit_human_time') or '',
                'pnl': t.get('pnl') or t.get('realized_net_pnl') or 0.0,
            })

        result[model_name] = {
            'open_positions': open_positions,
            'recent_trades': recent_trades,
        }

    return result


def detect_new_data(
    new_accounts: Dict[str, Dict[str, Any]],
    new_trades: Dict[str, Dict[str, List[Dict[str, Any]]]],
    recorded: Dict[str, Any],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, List[Dict[str, Any]]]], bool]:
    updated_accounts: Dict[str, Dict[str, Any]] = {}
    updated_trades: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    has_changes = False

    recorded_accounts = recorded.get('accounts', {})
    recorded_trades = recorded.get('trades', {})

    # Accounts: include always for the report header per model, but changes don't gate sending
    for model, acc in new_accounts.items():
        updated_accounts[model] = acc

    # Trades and positions: deduplicate by stable hashes
    for model, blocks in new_trades.items():
        prev_model_block = recorded_trades.get(model, {}) if isinstance(recorded_trades, dict) else {}
        prev_positions = prev_model_block.get('open_positions', [])
        prev_trades_list = prev_model_block.get('recent_trades', [])

        prev_pos_hashes = {stable_hash(p) for p in prev_positions}
        prev_trade_hashes = {stable_hash(t) for t in prev_trades_list}

        new_positions_filtered: List[Dict[str, Any]] = []
        for p in blocks.get('open_positions', []):
            h = stable_hash(p)
            if h not in prev_pos_hashes:
                has_changes = True
                p2 = dict(p)
                p2['_change_prefix'] = 'New/Updated: '
                new_positions_filtered.append(p2)

        new_trades_filtered: List[Dict[str, Any]] = []
        for t in blocks.get('recent_trades', []):
            h = stable_hash(t)
            if h not in prev_trade_hashes:
                has_changes = True
                t2 = dict(t)
                t2['_change_prefix'] = 'New/Updated: '
                new_trades_filtered.append(t2)

        updated_trades[model] = {
            'open_positions': new_positions_filtered,
            'recent_trades': new_trades_filtered,
        }

    return updated_accounts, updated_trades, has_changes


def fmt_money(value: float) -> str:
    try:
        return f"${value:,.2f}"
    except Exception:
        return "$0.00"


def generate_report(
    accounts: Dict[str, Dict[str, Any]],
    trades_delta: Dict[str, Dict[str, List[Dict[str, Any]]]],
) -> str:
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lines: List[str] = []
    lines.append(f"NoF1 AI Trading Update - {now_str}")
    lines.append("Models: Deepseek, Qwen, Grok, Claude")
    lines.append("")

    for model in sorted(accounts.keys()):
        acc = accounts.get(model, {})
        lines.append(f"*{model}*")
        stats = (
            f"Stats: PnL: {fmt_money(acc.get('pnl', 0.0))} | "
            f"Equity: {fmt_money(acc.get('equity', 0.0))} | "
            f"Unrealized: {fmt_money(acc.get('unrealized', 0.0))} | "
            f"Sharpe: {acc.get('sharpe', 0.0):.2f}"
        )
        lines.append(stats)

        delta = trades_delta.get(model, {})

        lines.append("")
        lines.append("Open Positions:")
        positions = delta.get('open_positions', [])
        if positions:
            for p in positions:
                prefix = p.get('_change_prefix', '')
                lines.append(
                    f"- {prefix}{p.get('asset', 'Unknown')} {p.get('side', 'Unknown')} | "
                    f"Qty: {p.get('qty', 0)} | "
                    f"Entry: {fmt_money(float(p.get('entry', 0.0)))} | "
                    f"Current: {fmt_money(float(p.get('current', 0.0)))} | "
                    f"PnL: {fmt_money(float(p.get('pnl', 0.0)))} | "
                    f"Lev: {p.get('lev', '1x')} | Conf: {float(p.get('conf', 0.0)):.2f}"
                )
        else:
            lines.append("- No new/updated open positions")

        lines.append("")
        lines.append("Recent Trades:")
        trades_list = delta.get('recent_trades', [])
        if trades_list:
            for t in trades_list:
                prefix = t.get('_change_prefix', '')
                entry_time = t.get('entry_time') or ''
                exit_time = t.get('exit_time') or ''
                lines.append(
                    f"- {prefix}{t.get('asset', 'Unknown')} {t.get('side', 'Unknown')} | "
                    f"Entry: {fmt_money(float(t.get('entry', 0.0)))} ({entry_time}) | "
                    f"Exit: {fmt_money(float(t.get('exit', 0.0)))} ({exit_time}) | "
                    f"PnL: {fmt_money(float(t.get('pnl', 0.0)))}"
                )
        else:
            lines.append("- No new/updated trades")

        lines.append("")

    return "\n".join(lines).strip()


def _chunk_text(text: str, max_len: int = 4000) -> List[str]:
    if len(text) <= max_len:
        return [text]
    chunks: List[str] = []
    remaining = text
    while len(remaining) > max_len:
        # Prefer splitting on paragraph boundary
        split_idx = remaining.rfind("\n\n", 0, max_len)
        if split_idx == -1:
            # fallback to line boundary
            split_idx = remaining.rfind("\n", 0, max_len)
        if split_idx == -1:
            # hard split
            split_idx = max_len
        chunks.append(remaining[:split_idx].rstrip())
        remaining = remaining[split_idx:].lstrip()
    if remaining:
        chunks.append(remaining)
    return chunks


async def send_to_telegram(report: str, bot_token: str, chat_id: str) -> bool:
    if not Bot:
        logging.error("python-telegram-bot is not installed; cannot send Telegram message.")
        return False
    try:
        bot = Bot(token=bot_token)
        parts = _chunk_text(report, max_len=4000)
        for idx, part in enumerate(parts, start=1):
            suffix = f" (part {idx}/{len(parts)})" if len(parts) > 1 else ""
            await bot.send_message(
                chat_id=chat_id,
                text=(part + suffix) if len(parts) > 1 else part,
                parse_mode='Markdown',
                disable_web_page_preview=True,
            )
        logging.info(f"Telegram message sent in {len(parts)} part(s)")
        return True
    except Exception as e:
        logging.error(f"Telegram send failed: {e}")
        return False


def loop_once(
    session: requests.Session,
    bot_token: str,
    chat_id: str,
    dry_run: bool,
) -> None:
    account_raw = fetch_data(session, API_ACCOUNT_TOTALS)
    trades_raw = fetch_data(session, API_TRADES)

    if not account_raw and not trades_raw:
        logging.error("Both API calls failed; skipping this cycle")
        return

    accounts = parse_account_totals(account_raw or {})
    trades = parse_trades(trades_raw or {})

    recorded = load_record()
    updated_accounts, updated_trades, has_changes = detect_new_data(accounts, trades, recorded)

    if not has_changes:
        logging.info("No new or updated items detected; not sending Telegram message")
        # Still update the record with latest snapshot for future comparisons
        save_record({'accounts': accounts, 'trades': trades})
        return

    report = generate_report(updated_accounts, updated_trades)

    if dry_run:
        print(report)
        logging.info("Dry-run: report printed to console")
    else:
        sent = asyncio.run(send_to_telegram(report, bot_token, chat_id))
        if not sent:
            logging.error("Failed to send Telegram message this cycle")

    # Persist the fresh snapshot only after a successful cycle
    save_record({'accounts': accounts, 'trades': trades})


def main() -> None:
    parser = argparse.ArgumentParser(description='NoF1 AI Trading Data Reporter')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    parser.add_argument('--dry-run', action='store_true', help='Print report instead of sending to Telegram')
    parser.add_argument('--bot-token', default=os.getenv('TELEGRAM_BOT_TOKEN', BOT_TOKEN))
    parser.add_argument('--chat-id', default=os.getenv('TELEGRAM_CHAT_ID', CHAT_ID))
    args = parser.parse_args()

    setup_logging(args.log_level)

    if not args.dry_run and (not args.bot_token or not args.chat_id):
        logging.error('Missing Telegram credentials: set --bot-token/--chat-id or TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID')
        sys.exit(1)

    session = create_http_session()

    stop_flag = {'stop': False}

    def _signal_handler(signum: int, frame: Any) -> None:
        logging.info(f"Signal {signum} received; preparing to stop...")
        stop_flag['stop'] = True

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    logging.info('Starting NoF1 reporter loop (every 60s)')
    try:
        while not stop_flag['stop']:
            start_ts = time.time()
            try:
                loop_once(session, args.bot_token, args.chat_id, args.dry_run)
            except Exception as e:
                logging.error(f"Unexpected error in loop_once: {e}")

            elapsed = time.time() - start_ts
            sleep_s = max(0, 60 - elapsed)
            if sleep_s > 0:
                time.sleep(sleep_s)
    finally:
        logging.info('Reporter stopped')


if __name__ == '__main__':
    main()
