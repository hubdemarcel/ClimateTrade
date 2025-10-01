#!/usr/bin/env python3
"""
Get NYC weather markets for trading
"""

import requests
import json

def main():
    print("Getting NYC Weather Markets...")
    print("=" * 50)

    # Get markets for NYC temperature event (ID: 41805)
    response = requests.get('https://gamma-api.polymarket.com/markets?event_id=41805&closed=false&active=true')

    if response.status_code == 200:
        data = response.json()

        if isinstance(data, list):
            markets = data
        else:
            markets = data.get('data', [])

        print(f"Total NYC markets found: {len(markets)}")

        # Look for temperature-related markets
        temp_markets = []
        for market in markets:
            question = market.get('question', '').lower()
            if 'temperature' in question or 'temp' in question or '°' in question or 'fahrenheit' in question:
                temp_markets.append(market)

        print(f"Temperature markets found: {len(temp_markets)}")

        for i, market in enumerate(temp_markets[:10]):  # Show first 10
            print(f"\nNYC Market {i+1}:")
            print(f"  Question: {market.get('question')}")
            print(f"  Market ID: {market.get('id')}")
            print(f"  Active: {market.get('active')}")
            print(f"  Closed: {market.get('closed')}")
            print(f"  Volume: {market.get('volume', 'N/A')}")

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

        # Summary
        if temp_markets:
            print("\n" + "="*50)
            print("NYC WEATHER TRADING SUMMARY")
            print("="*50)
            print(f"Total temperature markets: {len(temp_markets)}")
            total_volume = sum(float(m.get('volume', 0)) for m in temp_markets)
            print(f"Total trading volume: ${total_volume:,.2f}")

            # Show temperature ranges available
            print("\nTemperature ranges available:")
            for market in temp_markets:
                question = market.get('question', '')
                if 'temperature' in question.lower():
                    # Extract temperature range from question
                    if 'or below' in question:
                        temp_range = question.split('temperature')[1].split('or below')[0].strip()
                        print(f"  - {temp_range} or below")
                    elif 'or higher' in question:
                        temp_range = question.split('temperature')[1].split('or higher')[0].strip()
                        print(f"  - {temp_range} or higher")
                    elif '-' in question:
                        # Look for temperature range in question
                        import re
                        temp_match = re.search(r'(\d+)-(\d+)°F', question)
                        if temp_match:
                            low, high = temp_match.groups()
                            print(f"  - {low}-{high}°F")
        else:
            print("\nNo temperature markets found in this event.")
            print("The markets might not be active yet or might be structured differently.")

            # Show a few non-temperature markets for reference
            print("\nShowing first few markets for reference:")
            for i, market in enumerate(markets[:3]):
                print(f"Market {i+1}: {market.get('question')}")
                tokens = market.get('tokens', [])
                print(f"  Tokens: {len(tokens)}")
                if tokens and tokens[0].get('token_id'):
                    print(f"  Sample Token ID: {tokens[0]['token_id'][:50]}...")

    else:
        print(f"API request failed with status: {response.status_code}")
        print(f"Response: {response.text[:200]}")

if __name__ == "__main__":
    main()