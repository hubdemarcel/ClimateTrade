#!/usr/bin/env python3
"""
Test script for CLOB client basic functionality
"""

from py_clob_client.client import ClobClient
import os
from dotenv import load_dotenv

load_dotenv()

def test_basic_connection():
    """Test basic CLOB connection"""

    print("Testing CLOB Client Installation")
    print("=" * 50)
    print(f"Python version: {__import__('sys').version}")
    print("py_clob_client version: 0.25.0")

    try:
        # Test read-only connection first
        print("Connecting to Polymarket API...")
        client = ClobClient("https://clob.polymarket.com")

        # Test basic API call
        server_time = client.get_server_time()
        print(f"SUCCESS: Connected! Server time: {server_time}")

        # Test getting markets
        markets = client.get_simplified_markets()
        market_count = len(markets.get('data', []))
        print(f"SUCCESS: Retrieved {market_count} markets")

        if market_count > 0:
            # Show a sample market
            sample_market = markets['data'][0]
            question = sample_market.get('question', 'N/A')[:60]
            print(f"Sample market: {question}...")

        return True

    except Exception as e:
        print(f"ERROR: Connection failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_connection()
    print("\n" + "="*50)
    if success:
        print("SUCCESS: py-clob-client installation working!")
        print("Package imported correctly")
        print("API connection working")
        print("\nNext: Configure your wallet credentials in .env")
    else:
        print("FAILED: Installation test failed.")
        print("Check your internet connection and try again.")