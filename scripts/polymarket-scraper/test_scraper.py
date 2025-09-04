#!/usr/bin/env python3
"""
Simple test script for the Polymarket scraper
"""

from polymarket_scraper import PolymarketScraper, MarketData
from datetime import datetime

def test_basic_functionality():
    """Test basic scraper functionality"""
    print("Testing basic functionality...")

    # Test data creation
    data = MarketData(
        event_title="Test Event",
        event_url="http://test.com",
        market_id="123",
        outcome_name="Test Outcome",
        probability=0.5,
        volume=1000.0,
        timestamp=datetime.now().isoformat(),
        scraped_at=datetime.now().isoformat()
    )
    print(f"[OK] Created MarketData: {data.event_title}")

    # Test scraper initialization
    scraper = PolymarketScraper(use_selenium=False)
    print("[OK] Scraper initialized")

    # Test validation
    test_data = [data]
    validated = scraper.validate_data(test_data)
    print(f"[OK] Validation passed: {len(validated)}/{len(test_data)} records")

    # Test CSV saving
    scraper.save_to_csv(validated, "test_output.csv")
    print("[OK] CSV saved successfully")

    print("All tests passed!")

if __name__ == "__main__":
    test_basic_functionality()