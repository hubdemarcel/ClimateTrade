#!/usr/bin/env python3
"""
Get London temperature market tokens for trading
"""

import requests
import json

def main():
    print("Getting London Temperature Markets...")
    print("=" * 50)

    # Get markets for the London temperature event
    response = requests.get('https://gamma-api.polymarket.com/markets?event_id=40662&closed=false&active=true')

    if response.status_code == 200:
        data = response.json()

        if isinstance(data, list):
            markets = data
        else:
            markets = data.get('data', [])

        print(f"Total markets found: {len(markets)}")

        # Look for temperature-related markets
        temp_markets = []
        for market in markets:
            question = market.get('question', '').lower()
            if 'temperature' in question or 'temp' in question or 'celsius' in question or 'fahrenheit' in question or '°' in question:
                temp_markets.append(market)

        print(f"Temperature markets found: {len(temp_markets)}")

        for i, market in enumerate(temp_markets[:10]):  # Show first 10
            print(f"\nMarket {i+1}:")
            print(f"  Question: {market.get('question')}")
            print(f"  Market ID: {market.get('id')}")
            print(f"  Active: {market.get('active')}")

            tokens = market.get('tokens', [])
            print(f"  Tokens: {len(tokens)}")

            if tokens:
                print("  TRADING TOKENS:")
                for j, token in enumerate(tokens):
                    print(f"    Token {j+1}:")
                    print(f"      Outcome: {token.get('outcome')}")
                    print(f"      Token ID: {token.get('token_id')}")
                    print(f"      Price: {token.get('price')}")
                    print(f"      Winner: {token.get('winner')}")

                    # This is what you need for trading!
                    if token.get('token_id'):
                        print(f"      *** READY TO TRADE: {token.get('token_id')} ***")
            else:
                print("    No tokens available for trading yet")
        if not temp_markets:
            print("\nNo temperature markets found in this event.")
            print("The markets might not be active yet or might be structured differently.")

            # Show a few non-temperature markets to see the structure
            print("\nShowing first few markets for reference:")
            for i, market in enumerate(markets[:3]):
                print(f"Market {i+1}: {market.get('question')}")
                tokens = market.get('tokens', [])
                print(f"  Tokens: {len(tokens)}")
                if tokens:
                    print(f"  First token ID: {tokens[0].get('token_id')}")

    else:
        print(f"API request failed with status: {response.status_code}")
        print(f"Response: {response.text[:200]}")

if __name__ == "__main__":
    main()