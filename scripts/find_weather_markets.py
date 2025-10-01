#!/usr/bin/env python3
"""
Find weather-related markets on Polymarket
"""

import requests
import json
from typing import List, Dict, Any

# Polymarket Gamma API
GAMMA_API_BASE = "https://gamma-api.polymarket.com"

def search_weather_events(query: str = "weather", limit: int = 50) -> List[Dict[str, Any]]:
    """Search for weather-related events"""
    url = f"{GAMMA_API_BASE}/events/pagination"

    # Search parameters
    params = {
        "limit": limit,
        "offset": 0,
        "closed": "false",
        "active": "true"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        all_events = data.get('data', [])

        # Filter for weather-related events
        weather_keywords = [
            'weather', 'temperature', 'rain', 'snow', 'storm', 'hurricane',
            'flood', 'drought', 'heat', 'cold', 'climate', 'forecast',
            'precipitation', 'humidity', 'wind', 'london', 'paris', 'nyc',
            'september', 'october', 'winter', 'summer', 'spring', 'fall'
        ]

        weather_events = []
        for event in all_events:
            title = event.get('title', '').lower()
            description = event.get('description', '').lower()

            # Check if event contains weather-related keywords
            if any(keyword in title or keyword in description for keyword in weather_keywords):
                weather_events.append(event)

        print(f"Found {len(weather_events)} weather-related events out of {len(all_events)} total events")
        return weather_events

    except Exception as e:
        print(f"Error searching weather events: {str(e)}")
        return []

def get_event_by_slug(slug: str) -> Dict[str, Any]:
    """Get event details by slug"""
    url = f"{GAMMA_API_BASE}/events/slug/{slug}"

    try:
        response = requests.get(url)
        response.raise_for_status()

        event_data = response.json()
        return event_data

    except Exception as e:
        print(f"Error getting event by slug {slug}: {str(e)}")
        return {}

def get_weather_markets_for_event(event_id: str) -> List[Dict[str, Any]]:
    """Get weather markets for a specific event"""
    url = f"{GAMMA_API_BASE}/markets"
    params = {
        "event_id": event_id,
        "closed": "false",
        "active": "true"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        # Handle different response formats
        if isinstance(data, list):
            markets = data
        else:
            markets = data.get('data', [])

        print(f"Event {event_id}: Found {len(markets)} markets")
        return markets

    except Exception as e:
        print(f"Error getting markets for event {event_id}: {str(e)}")
        return []

def display_weather_events(events: List[Dict[str, Any]]):
    """Display weather events in a readable format"""
    print("\n" + "="*100)
    print("WEATHER-RELATED POLYMARKET EVENTS")
    print("="*100)

    for i, event in enumerate(events, 1):
        print(f"\n{i}. Event ID: {event.get('id', 'N/A')}")
        print(f"   Slug: {event.get('slug', 'N/A')}")
        print(f"   Title: {event.get('title', 'N/A')}")
        print(f"   Description: {event.get('description', 'N/A')[:120]}...")
        print(f"   Start Date: {event.get('start_date', 'N/A')}")
        print(f"   End Date: {event.get('end_date', 'N/A')}")

def display_weather_markets(markets: List[Dict[str, Any]]):
    """Display weather markets with token details"""
    print("\n" + "="*100)
    print("WEATHER MARKETS & TRADING TOKENS")
    print("="*100)

    for i, market in enumerate(markets, 1):
        print(f"\n{i}. Market ID: {market.get('id', 'N/A')}")
        print(f"   Question: {market.get('question', 'N/A')}")
        print(f"   Active: {market.get('active', 'N/A')}")
        print(f"   Closed: {market.get('closed', 'N/A')}")

        # Show tokens for trading
        tokens = market.get('tokens', [])
        if tokens:
            print(f"   Trading Tokens: {len(tokens)}")
            for j, token in enumerate(tokens):
                print(f"     {j+1}. Token ID: {token.get('token_id', 'N/A')}")
                print(f"        Outcome: {token.get('outcome', 'N/A')}")
                print(f"        Price: {token.get('price', 'N/A')}")
                print(f"        Winner: {token.get('winner', 'N/A')}")
        else:
            print("   No tokens available")

def main():
    """Main function to find weather markets"""
    print("Weather Markets Finder for Polymarket")
    print("=" * 50)

    # First, try the specific weather event the user mentioned
    print("\nLooking for specific weather event...")
    specific_event = get_event_by_slug("highest-temperature-in-london-on-september-2")

    if specific_event:
        print("Found the specific weather event!")
        weather_events = [specific_event]
    else:
        print("Specific weather event not found. Searching for weather-related events...")
        weather_events = search_weather_events()

    if not weather_events:
        print("No weather events found at all.")
        return

    # Display weather events
    display_weather_events(weather_events)

    # Try to find actual weather markets
    print("\n" + "="*50)
    print("SEARCHING FOR ACTUAL WEATHER MARKETS")
    print("="*50)

    # Search through all markets for weather-related ones
    weather_markets = []
    for event in weather_events:
        event_id = event.get('id')
        markets = get_weather_markets_for_event(event_id)

        # Filter for actual weather markets
        for market in markets:
            question = market.get('question', '').lower()
            if any(keyword in question for keyword in ['temperature', 'weather', 'rain', 'snow', 'storm', 'climate', 'hot', 'cold', 'heat']):
                weather_markets.append(market)

    if weather_markets:
        print(f"\nFound {len(weather_markets)} actual weather markets!")
        display_weather_markets(weather_markets)

        # Show trading example for first weather market
        first_weather_market = weather_markets[0]
        show_trading_example(first_weather_market)
    else:
        print("\nNo specific weather markets found in current events.")
        print("Try searching for markets with keywords like 'temperature', 'weather', etc.")

        # Show general trading example
        if weather_events:
            first_event = weather_events[0]
            event_id = first_event.get('id')
            markets = get_weather_markets_for_event(event_id)

            if markets:
                first_market = markets[0]
                show_trading_example(first_market)

def show_trading_example(market: Dict[str, Any]):
    """Show trading example for a market"""
    print("\n" + "="*100)
    print("TRADING EXAMPLE")
    print("="*100)

    tokens = market.get('tokens', [])
    if tokens:
        first_token = tokens[0]

        print("Market Details:")
        print(f"Question: {market.get('question', 'N/A')}")
        print(f"Market ID: {market.get('id', 'N/A')}")
        print(f"Token ID: {first_token.get('token_id', 'N/A')}")
        print(f"Outcome: {first_token.get('outcome', 'N/A')}")
        print(f"Current Price: {first_token.get('price', 'N/A')}")

        print("\nPython Trading Code:")
        print(f"""
from py_clob_client.client import ClobClient

# Initialize client (add your credentials to .env first)
client = ClobClient(
    "https://clob.polymarket.com",
    key=os.getenv('POLYGON_WALLET_PRIVATE_KEY'),
    chain_id=137,
    signature_type=1
)

# Set API credentials
from py_clob_client.clob_types import ApiCreds
creds = ApiCreds(
    api_key=os.getenv('CLOB_API_KEY'),
    api_secret="",
    api_passphrase=os.getenv('CLOB_PASSPHRASE')
)
client.set_api_creds(creds)

# Place a limit order
order = client.create_order({{
    "token_id": "{first_token.get('token_id')}",
    "price": 0.5,  # Adjust price as needed
    "size": 10,    # Adjust size as needed
    "side": "BUY"  # or "SELL"
}})

result = client.post_order(order)
print(f"Order placed: {{result}}")
""")
    else:
        print("No tokens available for trading in this market.")

if __name__ == "__main__":
    main()