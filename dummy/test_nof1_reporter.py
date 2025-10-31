#!/usr/bin/env python3
"""
Test script for NoF1 Trading Reporter

This script tests the main functionality with sample data.
"""

import json
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nof1_trading_reporter import (
    filter_account_totals,
    filter_trades_data,
    generate_full_report,
    is_target_model,
    extract_model_name
)


def test_model_filtering():
    """Test model filtering functionality."""
    print("Testing model filtering...")
    
    # Test cases
    test_cases = [
        ("deepseek-chat-v3.1_119", True, "Deepseek"),
        ("qwen3-max_42", True, "Qwen"),
        ("grok-4_1", True, "Grok"),
        ("claude-sonnet-4-5_5", True, "Claude"),
        ("gpt-5_0", False, "gpt-5_0"),
        ("gemini-pro_1", False, "gemini-pro_1"),
        ("unknown-model_1", False, "unknown-model_1"),
    ]
    
    for model_id, should_match, expected_name in test_cases:
        matches = is_target_model(model_id)
        extracted_name = extract_model_name(model_id)
        
        print(f"  {model_id}: matches={matches}, name='{extracted_name}'")
        
        if matches != should_match:
            print(f"    ERROR: Expected match={should_match}, got {matches}")
        elif extracted_name != expected_name:
            print(f"    ERROR: Expected name='{expected_name}', got '{extracted_name}'")
        else:
            print(f"    PASS")


def test_data_filtering():
    """Test data filtering with sample data."""
    print("\nTesting data filtering...")
    
    # Sample account totals data
    sample_account_data = {
        "accountTotals": [
            {
                "id": "deepseek-chat-v3.1_119",
                "realized_pnl": 1000.50,
                "total_unrealized_pnl": 250.75,
                "dollar_equity": 10000.00,
                "sharpe_ratio": 1.25,
                "positions": {
                    "BTC": {
                        "symbol": "BTC",
                        "quantity": 0.05,
                        "entry_price": 45000.00,
                        "current_price": 46000.00,
                        "unrealized_pnl": 50.00,
                        "leverage": 1,
                        "confidence": 0.85
                    }
                }
            },
            {
                "id": "gpt-5_0",
                "realized_pnl": 500.00,
                "total_unrealized_pnl": 100.00,
                "dollar_equity": 5000.00,
                "sharpe_ratio": 0.8,
                "positions": {}
            }
        ]
    }
    
    # Sample trades data
    sample_trades_data = {
        "trades": [
            {
                "model_id": "deepseek-chat-v3.1",
                "symbol": "ETH",
                "side": "long",
                "entry_price": 3000.00,
                "exit_price": 3100.00,
                "realized_net_pnl": 100.00,
                "entry_human_time": "2025-01-25 14:30:00.000000",
                "exit_human_time": "2025-01-25 16:45:00.000000",
                "entry_time": 1737819000,
                "exit_time": 1737827100
            },
            {
                "model_id": "gpt-5",
                "symbol": "BTC",
                "side": "short",
                "entry_price": 45000.00,
                "exit_price": 44000.00,
                "realized_net_pnl": 1000.00,
                "entry_human_time": "2025-01-24 10:00:00.000000",
                "exit_human_time": "2025-01-24 12:00:00.000000",
                "entry_time": 1737720000,
                "exit_time": 1737727200
            }
        ]
    }
    
    # Test filtering
    filtered_accounts = filter_account_totals(sample_account_data)
    filtered_trades = filter_trades_data(sample_trades_data)
    
    print(f"  Filtered accounts: {len(filtered_accounts)} models")
    print(f"  Filtered trades: {len(filtered_trades)} models")
    
    # Check results
    if "Deepseek" in filtered_accounts:
        print("    PASS: Deepseek account data found")
    else:
        print("    ERROR: Deepseek account data missing")
    
    if "Deepseek" in filtered_trades:
        print("    PASS: Deepseek trades data found")
    else:
        print("    ERROR: Deepseek trades data missing")
    
    if "gpt-5" not in filtered_accounts and "gpt-5" not in filtered_trades:
        print("    PASS: GPT-5 data correctly excluded")
    else:
        print("    ERROR: GPT-5 data not excluded")


def test_report_generation():
    """Test report generation."""
    print("\nTesting report generation...")
    
    # Sample filtered data
    sample_accounts = {
        "Deepseek": {
            "realized_pnl": 1000.50,
            "total_unrealized_pnl": 250.75,
            "dollar_equity": 10000.00,
            "sharpe_ratio": 1.25,
            "positions": {
                "BTC": {
                    "symbol": "BTC",
                    "quantity": 0.05,
                    "entry_price": 45000.00,
                    "current_price": 46000.00,
                    "unrealized_pnl": 50.00,
                    "leverage": 1,
                    "confidence": 0.85
                }
            }
        }
    }
    
    sample_trades = {
        "Deepseek": [
            {
                "model_id": "deepseek-chat-v3.1",
                "symbol": "ETH",
                "side": "long",
                "entry_price": 3000.00,
                "exit_price": 3100.00,
                "realized_net_pnl": 100.00,
                "entry_human_time": "2025-01-25 14:30:00.000000",
                "exit_human_time": "2025-01-25 16:45:00.000000"
            }
        ]
    }
    
    # Generate report
    report = generate_full_report(sample_accounts, sample_trades)
    
    print("Generated report preview:")
    print("-" * 50)
    print(report[:500] + "..." if len(report) > 500 else report)
    print("-" * 50)
    
    # Check for key elements
    checks = [
        ("NoF1 AI Trading Update" in report, "Header"),
        ("Deepseek" in report, "Model name"),
        ("Stats:" in report, "Stats section"),
        ("Open Positions:" in report, "Positions section"),
        ("Recent Trades:" in report, "Trades section"),
        ("BTC" in report, "Position data"),
        ("ETH" in report, "Trade data")
    ]
    
    for check, description in checks:
        if check:
            print(f"    PASS: {description}")
        else:
            print(f"    ERROR: {description}")


def main():
    """Run all tests."""
    print("NoF1 Trading Reporter Test Suite")
    print("=" * 50)
    
    try:
        test_model_filtering()
        test_data_filtering()
        test_report_generation()
        
        print("\nAll tests completed!")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
