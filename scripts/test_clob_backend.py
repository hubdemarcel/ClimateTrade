#!/usr/bin/env python3
"""
Test script for CLOB backend API integration
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Backend URL
BACKEND_URL = "http://localhost:8001"

def test_backend_connection():
    """Test basic backend connection"""
    print("Testing Backend Connection")
    print("=" * 50)

    try:
        response = requests.get(f"{BACKEND_URL}/")
        if response.status_code == 200:
            print("SUCCESS: Backend is running")
            return True
        else:
            print(f"ERROR: Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to backend. Is it running?")
        print("Start the backend with: python -m uvicorn web.backend.main:app --reload")
        return False

def test_clob_status():
    """Test CLOB status endpoint"""
    print("\nTesting CLOB Status Endpoint")
    print("=" * 50)

    try:
        response = requests.get(f"{BACKEND_URL}/api/clob/status")
        if response.status_code == 200:
            status = response.json()
            print("SUCCESS: CLOB status retrieved")
            print(f"Connected: {status.get('connected', 'Unknown')}")
            print(f"Authenticated: {status.get('authenticated', 'Unknown')}")
            if status.get('server_time'):
                print(f"Server Time: {status.get('server_time')}")
            return True
        else:
            print(f"ERROR: Status endpoint returned {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: Failed to get CLOB status: {str(e)}")
        return False

def test_clob_markets():
    """Test markets endpoint"""
    print("\nTesting CLOB Markets Endpoint")
    print("=" * 50)

    try:
        response = requests.get(f"{BACKEND_URL}/api/clob/markets?limit=5")
        if response.status_code == 200:
            data = response.json()
            markets = data.get('markets', [])
            print(f"SUCCESS: Retrieved {len(markets)} markets")
            if markets:
                # Show first market as example
                market = markets[0]
                question = market.get('question', 'N/A')[:50]
                print(f"Sample market: {question}...")
            return True
        else:
            print(f"ERROR: Markets endpoint returned {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: Failed to get markets: {str(e)}")
        return False

def test_clob_orderbook():
    """Test order book endpoint (if we have a market)"""
    print("\nTesting CLOB Order Book Endpoint")
    print("=" * 50)

    try:
        # First get a market to test order book
        response = requests.get(f"{BACKEND_URL}/api/clob/markets?limit=1")
        if response.status_code == 200:
            data = response.json()
            markets = data.get('markets', [])
            if markets:
                market = markets[0]
                # Try to get tokens from market data
                tokens = market.get('tokens', [])
                if tokens:
                    token_id = tokens[0].get('token_id')
                    if token_id:
                        print(f"Testing order book for token: {token_id}")
                        ob_response = requests.get(f"{BACKEND_URL}/api/clob/orderbook/{token_id}")
                        if ob_response.status_code == 200:
                            orderbook = ob_response.json()
                            print("SUCCESS: Order book retrieved")
                            bids = orderbook.get('bids', [])
                            asks = orderbook.get('asks', [])
                            print(f"Bids: {len(bids)}, Asks: {len(asks)}")
                            return True
                        else:
                            print(f"Order book request failed: {ob_response.status_code}")
                            return False
                else:
                    print("No tokens found in market data")
                    return False
            else:
                print("No markets available for testing")
                return False
        else:
            print("Could not get markets for order book test")
            return False
    except Exception as e:
        print(f"ERROR: Order book test failed: {str(e)}")
        return False

def test_authenticated_endpoints():
    """Test authenticated endpoints if credentials are available"""
    print("\nTesting Authenticated Endpoints")
    print("=" * 50)

    private_key = os.getenv('POLYGON_WALLET_PRIVATE_KEY')
    api_key = os.getenv('CLOB_API_KEY')

    if not private_key or not api_key:
        print("Skipping authenticated tests - credentials not configured")
        print("Configure POLYGON_WALLET_PRIVATE_KEY and CLOB_API_KEY in .env")
        return True

    # Test balance endpoint
    try:
        response = requests.get(f"{BACKEND_URL}/api/clob/balance")
        if response.status_code == 200:
            print("SUCCESS: Balance endpoint working")
        else:
            print(f"Balance endpoint returned {response.status_code}")
    except Exception as e:
        print(f"Balance test failed: {str(e)}")

    # Test orders endpoint
    try:
        response = requests.get(f"{BACKEND_URL}/api/clob/orders")
        if response.status_code == 200:
            print("SUCCESS: Orders endpoint working")
        else:
            print(f"Orders endpoint returned {response.status_code}")
    except Exception as e:
        print(f"Orders test failed: {str(e)}")

    return True

def main():
    """Run all backend tests"""
    print("CLOB Backend Integration Test")
    print("=" * 60)

    tests = [
        ("Backend Connection", test_backend_connection),
        ("CLOB Status", test_clob_status),
        ("CLOB Markets", test_clob_markets),
        ("CLOB Order Book", test_clob_orderbook),
        ("Authenticated Endpoints", test_authenticated_endpoints),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"TEST ERROR: {str(e)}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print("20")
        if result:
            passed += 1

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("SUCCESS: All backend tests passed!")
        print("\nNext steps:")
        print("1. Start the React frontend")
        print("2. Test the complete integration")
        print("3. Build trading components")
    else:
        print("Some tests failed. Check the errors above.")

    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)