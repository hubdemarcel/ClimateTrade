#!/usr/bin/env python3
"""
Polymarket Web Scraper for Weather Events

This script scrapes market data from Polymarket weather event pages (focused on London and NYC),
discovers new daily events, and outputs to CSV format with daily scheduling.
Includes error handling, rate limiting, and data validation.

Legal Notice: This scraper is for educational/research purposes only.
Always respect website terms of service and robots.txt.
"""

import time
import logging
import csv
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict

try:
    import schedule
except ImportError:
    schedule = None
    logging.warning("Schedule module not available. Daily scheduling disabled.")

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


@dataclass
class MarketData:
    """Data structure for market information"""
    event_title: str
    event_url: str
    market_id: str
    outcome_name: str
    probability: float
    volume: float
    timestamp: str
    scraped_at: str


class RateLimiter:
    """Simple rate limiter to avoid overwhelming the server"""

    def __init__(self, requests_per_minute: int = 10):  # Reduced from 30 to be more conservative
        self.requests_per_minute = requests_per_minute
        self.last_request_time = 0
        self.min_interval = 60 / requests_per_minute

    def wait_if_needed(self):
        """Wait if necessary to respect rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            logging.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)

        self.last_request_time = time.time()


class PolymarketScraper:
    """Main scraper class for Polymarket data"""

    def __init__(self, use_selenium: bool = False, headless: bool = True):
        self.use_selenium = use_selenium
        self.headless = headless
        self.session = requests.Session()
        self.rate_limiter = RateLimiter()
        self.setup_logging()

        # Setup headers to mimic browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        if self.use_selenium:
            self.setup_selenium()

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('polymarket_scraper.log'),
                logging.StreamHandler()
            ]
        )

    def setup_selenium(self):
        """Setup Selenium WebDriver"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            logging.info("Selenium WebDriver initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Selenium: {e}")
            self.use_selenium = False

    def scrape_event_page(self, url: str) -> List[MarketData]:
        """
        Scrape market data from a Polymarket event page

        Args:
            url: The Polymarket event URL

        Returns:
            List of MarketData objects
        """
        try:
            self.rate_limiter.wait_if_needed()

            if self.use_selenium:
                return self._scrape_with_selenium(url)
            else:
                return self._scrape_with_requests(url)

        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
            return []

    def _scrape_with_requests(self, url: str) -> List[MarketData]:
        """Scrape using requests and BeautifulSoup"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract event title
            title_elem = soup.find('h1') or soup.find('title')
            event_title = title_elem.text.strip() if title_elem else "Unknown Event"

            # Look for market data in script tags or JSON
            market_data = self._extract_market_data_from_html(soup, url, event_title)

            return market_data

        except requests.RequestException as e:
            logging.error(f"Request failed for {url}: {e}")
            return []

    def _scrape_with_selenium(self, url: str) -> List[MarketData]:
        """Scrape using Selenium for dynamic content"""
        try:
            self.driver.get(url)

            # Wait for page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Additional wait for dynamic content
            time.sleep(3)

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Extract event title
            title_elem = self.driver.find_element(By.TAG_NAME, 'h1') if self._element_exists(By.TAG_NAME, 'h1') else None
            event_title = title_elem.text.strip() if title_elem else "Unknown Event"

            # Look for market data
            market_data = self._extract_market_data_from_html(soup, url, event_title)

            return market_data

        except (TimeoutException, WebDriverException) as e:
            logging.error(f"Selenium scraping failed for {url}: {e}")
            return []

    def _element_exists(self, by, value):
        """Check if element exists"""
        try:
            self.driver.find_element(by, value)
            return True
        except:
            return False

    def _extract_market_data_from_html(self, soup: BeautifulSoup, url: str, event_title: str) -> List[MarketData]:
        """Extract market data from HTML content"""
        market_data = []

        # Look for JSON data in script tags
        scripts = soup.find_all('script', type='application/json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                markets = self._parse_market_json(data, url, event_title)
                if markets:
                    market_data.extend(markets)
            except (json.JSONDecodeError, TypeError):
                continue

        # If no JSON found, try to extract from HTML elements
        if not market_data:
            market_data = self._extract_from_html_elements(soup, url, event_title)

        return market_data

    def _parse_market_json(self, data: Dict, url: str, event_title: str) -> List[MarketData]:
        """Parse market data from JSON structure"""
        markets = []

        # This is a placeholder - actual JSON structure would need to be analyzed
        # Look for common patterns in Polymarket's data structure
        if isinstance(data, dict):
            # Try different possible keys for market data
            possible_keys = ['markets', 'market', 'data', 'props', 'pageProps']

            for key in possible_keys:
                if key in data:
                    market_info = data[key]
                    if isinstance(market_info, list):
                        for market in market_info:
                            parsed = self._parse_single_market(market, url, event_title)
                            if parsed:
                                markets.append(parsed)
                    elif isinstance(market_info, dict):
                        parsed = self._parse_single_market(market_info, url, event_title)
                        if parsed:
                            markets.append(parsed)

        return markets

    def _parse_single_market(self, market: Dict, url: str, event_title: str) -> Optional[MarketData]:
        """Parse a single market's data"""
        try:
            # Extract relevant fields - these would need to be adjusted based on actual structure
            market_id = market.get('id') or market.get('market_id') or 'unknown'
            outcome_name = market.get('outcome') or market.get('name') or 'Unknown'
            probability = float(market.get('probability', 0)) / 100 if market.get('probability') else 0.0
            volume = float(market.get('volume', 0))

            return MarketData(
                event_title=event_title,
                event_url=url,
                market_id=str(market_id),
                outcome_name=str(outcome_name),
                probability=probability,
                volume=volume,
                timestamp=datetime.now().isoformat(),
                scraped_at=datetime.now().isoformat()
            )

        except (ValueError, TypeError) as e:
            logging.warning(f"Failed to parse market data: {e}")
            return None

    def _extract_from_html_elements(self, soup: BeautifulSoup, url: str, event_title: str) -> List[MarketData]:
        """Extract market data from HTML elements as fallback"""
        markets = []

        # Look for common patterns in Polymarket's HTML
        # This is a basic implementation - would need refinement based on actual page structure

        # Look for probability displays
        prob_elements = soup.find_all(text=lambda text: '%' in str(text))
        for elem in prob_elements[:10]:  # Limit to avoid noise
            try:
                prob_text = elem.strip()
                if prob_text.replace('%', '').replace('.', '').isdigit():
                    probability = float(prob_text.replace('%', '')) / 100

                    markets.append(MarketData(
                        event_title=event_title,
                        event_url=url,
                        market_id='html_extracted',
                        outcome_name='Extracted from HTML',
                        probability=probability,
                        volume=0.0,
                        timestamp=datetime.now().isoformat(),
                        scraped_at=datetime.now().isoformat()
                    ))
            except (ValueError, AttributeError):
                continue

        return markets

    def save_to_csv(self, market_data: List[MarketData], filename: str):
        """Save market data to CSV file"""
        if not market_data:
            logging.warning("No data to save")
            return

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                if market_data:
                    fieldnames = list(asdict(market_data[0]).keys())
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for data in market_data:
                        writer.writerow(asdict(data))

            logging.info(f"Saved {len(market_data)} records to {filename}")

        except Exception as e:
            logging.error(f"Failed to save CSV: {e}")

    def validate_data(self, market_data: List[MarketData]) -> List[MarketData]:
        """Validate and clean market data"""
        validated = []

        for data in market_data:
            if self._is_valid_market_data(data):
                validated.append(data)
            else:
                logging.warning(f"Invalid data discarded: {data}")

        return validated

    def _is_valid_market_data(self, data: MarketData) -> bool:
        """Check if market data is valid"""
        try:
            # Basic validation rules
            if not data.event_title or data.event_title == "Unknown Event":
                return False

            if data.probability < 0 or data.probability > 1:
                return False

            if data.volume < 0:
                return False

            return True

        except (AttributeError, TypeError):
            return False

    def close(self):
        """Clean up resources"""
        if hasattr(self, 'driver'):
            self.driver.quit()

    def discover_new_events(self, known_urls: Set[str]) -> List[str]:
        """
        Discover new weather events from Polymarket's weather category page

        Args:
            known_urls: Set of already known event URLs

        Returns:
            List of new event URLs
        """
        new_urls = []
        browse_url = "https://polymarket.com/browse/weather"

        try:
            self.rate_limiter.wait_if_needed()

            if self.use_selenium:
                self.driver.get(browse_url)
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                time.sleep(3)
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            else:
                response = self.session.get(browse_url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')

            # Find event links
            event_links = soup.find_all('a', href=re.compile(r'/event/highest-temperature-in-(london|nyc)-on-'))

            for link in event_links:
                url = f"https://polymarket.com{link['href']}"
                if url not in known_urls:
                    new_urls.append(url)
                    logging.info(f"Discovered new event: {url}")

        except Exception as e:
            logging.error(f"Error discovering new events: {e}")

        return new_urls


def run_daily_scrape():
    """Function to run the daily scraping job"""
    # Known URLs for London and NYC
    known_urls = {
        "https://polymarket.com/event/highest-temperature-in-london-on-september-2?tid=1756960430533",
        "https://polymarket.com/event/highest-temperature-in-nyc-on-september-3-891"
    }

    # Initialize scraper
    scraper = PolymarketScraper(use_selenium=True, headless=True)

    try:
        # Discover new events
        logging.info("Discovering new events...")
        new_urls = scraper.discover_new_events(known_urls)
        all_urls = list(known_urls) + new_urls

        all_market_data = []

        # Scrape all events
        for url in all_urls:
            logging.info(f"Starting scrape of {url}")
            market_data = scraper.scrape_event_page(url)
            all_market_data.extend(market_data)

        # Validate data
        validated_data = scraper.validate_data(all_market_data)
        logging.info(f"Validated {len(validated_data)} records from {len(all_urls)} events")

        # Save to CSV
        if validated_data:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"../../data_pipeline/data/polymarket_weather_data_{timestamp}.csv"
            scraper.save_to_csv(validated_data, filename)
        else:
            logging.warning("No valid data to save")

    except Exception as e:
        logging.error(f"Scraping failed: {e}")

    finally:
        scraper.close()


def main():
    """Main function to run the scraper with daily scheduling"""
    logging.info("Starting Polymarket Weather Scraper")

    # Run initial scrape
    run_daily_scrape()

    if schedule:
        # Schedule daily scrape at 2 AM UTC
        schedule.every().day.at("02:00").do(run_daily_scrape)
        logging.info("Scheduled daily scraping at 02:00 UTC. Press Ctrl+C to stop.")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logging.info("Stopping scheduler...")
    else:
        logging.info("Schedule module not available. Run manually for daily scraping.")


if __name__ == "__main__":
    main()