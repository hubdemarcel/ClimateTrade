#!/usr/bin/env python3
"""
Find London and NYC weather markets on Polymarket
"""

import requests
import json
from typing import List, Dict, Any

# Polymarket Gamma API
GAMMA_API_BASE = "https://gamma-api.polymarket.com"

def search_all_events_for_weather(limit: int = 200) -> List[Dict[str, Any]]:
    """Search through all events for weather-related ones"""
    url = f"{GAMMA_API_BASE}/events/pagination"
    all_weather_events = []

    # Search through multiple pages
    for offset in range(0, limit, 50):
        params = {
            "limit": min(50, limit - offset),
            "offset": offset,
            "closed": "false",
            "active": "true"
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            events = data.get('data', [])

            if not events:
                break

            # Filter for weather events in London/NYC
            weather_keywords = [
                'london', 'nyc', 'new york', 'weather', 'temperature',
                'rain', 'snow', 'storm', 'forecast', 'climate', 'heat',
                'cold', 'precipitation', 'humidity', 'wind'
            ]

            for event in events:
                title = event.get('title', '').lower()
                description = event.get('description', '').lower()
                slug = event.get('slug', '').lower()

                # Check if it's weather-related and mentions London/NYC
                is_weather = any(keyword in title or keyword in description or keyword in slug
                               for keyword in weather_keywords)

                if is_weather:
                    all_weather_events.append(event)

        except Exception as e:
            print(f"Error fetching events at offset {offset}: {str(e)}")
            break

    return all_weather_events

def get_weather_markets_detailed(event_id: str) -> List[Dict[str, Any]]:
    """Get detailed market information for weather events"""
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

        # Filter for actual weather markets
        weather_markets = []
        for market in markets:
            question = market.get('question', '').lower()
            if any(keyword in question for keyword in [
                'temperature', 'weather', 'rain', 'snow', 'storm',
                'forecast', 'heat', 'cold', 'precipitation', 'humidity', 'wind'
            ]):
                weather_markets.append(market)

        return weather_markets

    except Exception as e:
        print(f"Error getting markets for event {event_id}: {str(e)}")
        return []

def search_specific_weather_events() -> List[Dict[str, Any]]:
    """Search for specific known weather event slugs"""
    known_weather_slugs = [
        "highest-temperature-in-london-on-september-2",
        "london-weather",
        "nyc-weather",
        "new-york-weather",
        "london-temperature",
        "nyc-temperature",
        "london-rain",
        "nyc-rain"
    ]

    found_events = []
    for slug in known_weather_slugs:
        try:
            response = requests.get(f"{GAMMA_API_BASE}/events/slug/{slug}")
            if response.status_code == 200:
                event = response.json()
                found_events.append(event)
                print(f"Found event: {slug}")
        except Exception as e:
            print(f"Event {slug} not found")

    return found_events

def display_weather_events(events: List[Dict[str, Any]]):
    """Display weather events in a readable format"""
    print("\n" + "="*100)
    print("LONDON & NYC WEATHER EVENTS ON POLYMARKET")
    print("="*100)

    london_events = []
    nyc_events = []

    for event in events:
        title = event.get('title', '').lower()
        if 'london' in title:
            london_events.append(event)
        elif 'nyc' in title or 'new york' in title:
            nyc_events.append(event)

    print(f"\nLONDON WEATHER EVENTS: {len(london_events)}")
    print("-" * 50)
    for i, event in enumerate(london_events, 1):
        print(f"{i}. {event.get('title', 'N/A')}")
        print(f"   Event ID: {event.get('id', 'N/A')}")
        print(f"   Slug: {event.get('slug', 'N/A')}")

    print(f"\nNYC WEATHER EVENTS: {len(nyc_events)}")
    print("-" * 50)
    for i, event in enumerate(nyc_events, 1):
        print(f"{i}. {event.get('title', 'N/A')}")
        print(f"   Event ID: {event.get('id', 'N/A')}")
        print(f"   Slug: {event.get('slug', 'N/A')}")

    return london_events + nyc_events

def display_trading_tokens(markets: List[Dict[str, Any]]):
    """Display trading tokens for weather markets"""
    print("\n" + "="*100)
    print("WEATHER MARKET TRADING TOKENS")
    print("="*100)

    for i, market in enumerate(markets, 1):
        print(f"\n{i}. {market.get('question', 'N/A')}")
        print(f"   Market ID: {market.get('id', 'N/A')}")

        tokens = market.get('tokens', [])
        if tokens:
            print(f"   Available Tokens: {len(tokens)}")
            for j, token in enumerate(tokens):
                print(f"     {j+1}. Token ID: {token.get('token_id', 'N/A')}")
                print(f"        Outcome: {token.get('outcome', 'N/A')}")
                print(f"        Price: {token.get('price', 'N/A')}")
                print(f"        Winner: {token.get('winner', 'N/A')}")
        else:
            print("   No tokens available for trading yet")

def main():
    """Main function to find London and NYC weather markets"""
    print("London & NYC Weather Markets Search")
    print("=" * 50)

    # First, try specific known weather events
    print("\nSearching for specific weather events...")
    specific_events = search_specific_weather_events()

    # Then search through all events
    print("\nSearching through all events for weather markets...")
    all_weather_events = search_all_events_for_weather(limit=500)

    # Combine and deduplicate
    all_events = specific_events + all_weather_events
    unique_events = []
    seen_ids = set()

    for event in all_events:
        event_id = event.get('id')
        if event_id and event_id not in seen_ids:
            unique_events.append(event)
            seen_ids.add(event_id)

    print(f"\nFound {len(unique_events)} unique weather-related events")

    # Display events
    weather_events = display_weather_events(unique_events)

    # Get markets for weather events
    all_weather_markets = []
    for event in weather_events[:5]:  # Check first 5 events
        event_id = event.get('id')
        markets = get_weather_markets_detailed(event_id)
        all_weather_markets.extend(markets)

    if all_weather_markets:
        print(f"\nFound {len(all_weather_markets)} weather markets with tokens")
        display_trading_tokens(all_weather_markets)

        # Show trading example
        print("\n" + "="*100)
        print("TRADING EXAMPLE")
        print("="*100)

        first_market = all_weather_markets[0]
        tokens = first_market.get('tokens', [])
        if tokens:
            first_token = tokens[0]

            print("Ready to trade on:")
            print(f"Market: {first_market.get('question')}")
            print(f"Token ID: {first_token.get('token_id')}")
            print(f"Outcome: {first_token.get('outcome')}")

            print("\nYour CLOB client is ready! Use this token ID in your trading code.")
    else:
        print("\nNo weather markets with trading tokens found.")
        print("Weather events may not have started trading yet.")

if __name__ == "__main__":
    main()