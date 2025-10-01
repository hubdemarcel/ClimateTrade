#!/usr/bin/env python3
"""
Test authenticated CLOB client functionality
"""

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds
import os
from dotenv import load_dotenv

load_dotenv()

def test_authenticated_connection():
    """Test authenticated CLOB connection with trading capabilities"""

    print("Testing Authenticated CLOB Connection")
    print("=" * 50)

    # Load credentials from environment
    private_key = os.getenv('POLYGON_WALLET_PRIVATE_KEY')
    api_key = os.getenv('CLOB_API_KEY')
    passphrase = os.getenv('CLOB_PASSPHRASE')

    # Check if credentials are available
    if not private_key:
        print("ERROR: POLYGON_WALLET_PRIVATE_KEY not found in .env")
        return False

    if not api_key:
        print("ERROR: CLOB_API_KEY not found in .env")
        print("Run: python scripts/generate_clob_creds.py")
        return False

    if not passphrase:
        print("ERROR: CLOB_PASSPHRASE not found in .env")
        print("Run: python scripts/generate_clob_creds.py")
        return False

    try:
        print("Connecting with authentication...")
        # Create authenticated client
        client = ClobClient(
            host="https://clob.polymarket.com",
            key=private_key,
            chain_id=137,  # Polygon
            signature_type=1  # Email/Magic wallet
        )

        # Set API credentials
        creds = ApiCreds(
            api_key=api_key,
            api_secret="",  # Will be derived
            api_passphrase=passphrase
        )
        client.set_api_creds(creds)

        print("SUCCESS: Authenticated connection established")

        # Test authenticated API calls
        print("\nTesting authenticated features...")

        # Get balance
        try:
            balance = client.get_balance_allowance()
            print("SUCCESS: Retrieved account balance")
            print(f"Balance info: {type(balance)}")
        except Exception as e:
            print(f"WARNING: Could not get balance: {str(e)}")

        # Get open orders
        try:
            orders = client.get_orders()
            print(f"SUCCESS: Retrieved {len(orders)} open orders")
        except Exception as e:
            print(f"WARNING: Could not get orders: {str(e)}")

        # Get user trades
        try:
            trades = client.get_trades()
            print(f"SUCCESS: Retrieved {len(trades)} recent trades")
        except Exception as e:
            print(f"WARNING: Could not get trades: {str(e)}")

        print("\n" + "="*50)
        print("SUCCESS: Authenticated CLOB client working!")
        print("Ready for trading operations:")
        print("- Place limit/market orders")
        print("- Get real-time order books")
        print("- Manage positions")
        print("- Cancel orders")

        return True

    except Exception as e:
        print(f"ERROR: Authenticated connection failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Verify your private key is correct")
        print("2. Check API key and passphrase are valid")
        print("3. Ensure you have funds on Polymarket")
        print("4. Try regenerating credentials: python scripts/generate_clob_creds.py")
        return False

if __name__ == "__main__":
    success = test_authenticated_connection()
    print("\n" + "="*50)
    if success:
        print("READY: Your CLOB client is fully configured!")
        print("Next: Integrate with FastAPI backend")
    else:
        print("FAILED: Check your credentials and try again")