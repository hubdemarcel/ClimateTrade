#!/usr/bin/env python3
"""
Get Polymarket events and markets for trading
"""

import requests
import json
from typing import List, Dict, Any

# Polymarket Gamma API endpoints
GAMMA_API_BASE = "https://gamma-api.polymarket.com"

def get_events(limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """Get events from Polymarket Gamma API"""
    url = f"{GAMMA_API_BASE}/events/pagination"
    params = {
        "limit": limit,
        "offset": offset,
        "closed": "false",  # Only active events
        "active": "true"    # Only active events
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        events = data.get('data', [])

        print(f"Retrieved {len(events)} events")
        return events

    except Exception as e:
        print(f"Error getting events: {str(e)}")
        return []

def get_event_markets(event_id: str) -> List[Dict[str, Any]]:
    """Get markets for a specific event"""
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

def get_market_tokens(market_id: str) -> Dict[str, Any]:
    """Get token IDs for a market"""
    url = f"{GAMMA_API_BASE}/markets/{market_id}"

    try:
        response = requests.get(url)
        response.raise_for_status()

        market_data = response.json()
        tokens = market_data.get('tokens', [])

        print(f"Market {market_id}: Found {len(tokens)} tokens")
        return {
            'market_id': market_id,
            'tokens': tokens,
            'question': market_data.get('question', ''),
            'description': market_data.get('description', '')
        }

    except Exception as e:
        print(f"Error getting market details for {market_id}: {str(e)}")
        return {}

def display_events(events: List[Dict[str, Any]]):
    """Display events in a readable format"""
    print("\n" + "="*80)
    print("POLYMARKET EVENTS")
    print("="*80)

    for i, event in enumerate(events, 1):
        print(f"\n{i}. Event ID: {event.get('id', 'N/A')}")
        print(f"   Title: {event.get('title', 'N/A')}")
        print(f"   Description: {event.get('description', 'N/A')[:100]}...")
        print(f"   Start Date: {event.get('start_date', 'N/A')}")
        print(f"   End Date: {event.get('end_date', 'N/A')}")

def display_markets(markets: List[Dict[str, Any]]):
    """Display markets in a readable format"""
    print("\n" + "="*80)
    print("POLYMARKET MARKETS")
    print("="*80)

    for i, market in enumerate(markets, 1):
        print(f"\n{i}. Market ID: {market.get('id', 'N/A')}")
        print(f"   Question: {market.get('question', 'N/A')}")
        print(f"   Active: {market.get('active', 'N/A')}")
        print(f"   Closed: {market.get('closed', 'N/A')}")
        print(f"   End Date: {market.get('end_date', 'N/A')}")

        # Show tokens if available
        tokens = market.get('tokens', [])
        if tokens:
            print(f"   Tokens: {len(tokens)}")
            for j, token in enumerate(tokens[:2]):  # Show first 2 tokens
                print(f"     {j+1}. Token ID: {token.get('token_id', 'N/A')}")
                print(f"        Outcome: {token.get('outcome', 'N/A')}")

def main():
    """Main function to demonstrate Polymarket event and market retrieval"""
    print("Polymarket Events and Markets Explorer")
    print("=" * 50)

    # Get events
    print("\nFetching events...")
    events = get_events(limit=10)

    if not events:
        print("No events found")
        return

    # Display events
    display_events(events)

    # Get markets for first event
    if events:
        first_event = events[0]
        event_id = first_event.get('id')

        print(f"\n\nFetching markets for event: {event_id}")
        markets = get_event_markets(event_id)

        if markets:
            display_markets(markets)

            # Get detailed info for first market
            first_market = markets[0]
            market_id = first_market.get('id')

            print(f"\n\nGetting detailed info for market: {market_id}")
            market_details = get_market_tokens(market_id)

            if market_details:
                print("\nMarket Details:")
                print(f"Question: {market_details.get('question', 'N/A')}")
                print(f"Tokens: {len(market_details.get('tokens', []))}")

                tokens = market_details.get('tokens', [])
                for i, token in enumerate(tokens):
                    print(f"  {i+1}. Token ID: {token.get('token_id', 'N/A')}")
                    print(f"     Outcome: {token.get('outcome', 'N/A')}")
                    print(f"     Price: {token.get('price', 'N/A')}")

if __name__ == "__main__":
    main()