# Polymarket Web Scraper

A Python-based web scraper for collecting market data from Polymarket event pages, with a focus on the NYC temperature prediction market.

## Features

- **Dual Scraping Methods**: Supports both requests/BeautifulSoup and Selenium for dynamic content
- **Rate Limiting**: Built-in rate limiting to respect server resources
- **Error Handling**: Comprehensive error handling and logging
- **Data Validation**: Validates scraped data for consistency
- **CSV Output**: Exports data to CSV format for analysis
- **Configurable**: Headless browser option and customizable settings

## Legal Considerations

⚠️ **Important**: This scraper is provided for educational and research purposes only.

- Always respect Polymarket's Terms of Service
- Check robots.txt before scraping
- Implement appropriate delays between requests
- Consider the legal implications of web scraping in your jurisdiction
- This tool includes rate limiting and ethical scraping practices

## Installation

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. For Selenium (recommended for dynamic content):
   - Chrome browser must be installed
   - WebDriver Manager will automatically handle ChromeDriver

## Usage

### Basic Usage

```python
from polymarket_scraper import PolymarketScraper

# Initialize scraper
scraper = PolymarketScraper(use_selenium=True, headless=True)

# Scrape a specific event
url = "https://polymarket.com/event/highest-temperature-in-nyc-on-september-3-891?tid=1756943550565"
market_data = scraper.scrape_event_page(url)

# Save to CSV
scraper.save_to_csv(market_data, "nyc_temperature_data.csv")

# Clean up
scraper.close()
```

### Command Line Usage

```bash
python polymarket_scraper.py
```

This will scrape the default NYC temperature event and save results to a timestamped CSV file.

## Configuration

### Rate Limiting

The scraper includes a built-in rate limiter (default: 30 requests per minute). You can customize this:

```python
from polymarket_scraper import RateLimiter

# Custom rate limiter
rate_limiter = RateLimiter(requests_per_minute=20)
```

### Scraping Methods

- **Requests + BeautifulSoup**: Faster, good for static content
- **Selenium**: Better for dynamic JavaScript-heavy pages (recommended)

```python
# Use requests only (faster but may miss dynamic content)
scraper = PolymarketScraper(use_selenium=False)

# Use Selenium (recommended for Polymarket)
scraper = PolymarketScraper(use_selenium=True, headless=True)
```

## Data Structure

The scraper collects the following data points:

- `event_title`: Title of the prediction market event
- `event_url`: URL of the scraped page
- `market_id`: Unique identifier for the market
- `outcome_name`: Name of the outcome (e.g., temperature range)
- `probability`: Current probability (0.0 to 1.0)
- `volume`: Trading volume
- `timestamp`: When the data was recorded
- `scraped_at`: When the scraping occurred

## Output Format

Data is saved as CSV with the following structure:

```csv
event_title,event_url,market_id,outcome_name,probability,volume,timestamp,scraped_at
"Highest Temperature in NYC on September 3","https://polymarket.com/...","market_123","70-75°F",0.25,15000.50,"2025-09-04T15:00:00","2025-09-04T15:00:00"
```

## Error Handling

The scraper includes comprehensive error handling:

- Network timeouts and connection errors
- Invalid HTML/JSON parsing
- Selenium WebDriver failures
- Data validation errors
- Rate limiting violations

All errors are logged to `polymarket_scraper.log`.

## Customization

### Adding New Markets

To scrape different Polymarket events, simply change the URL:

```python
url = "https://polymarket.com/event/your-event-here"
market_data = scraper.scrape_event_page(url)
```

### Custom Data Extraction

Modify the `_extract_market_data_from_html` and `_parse_market_json` methods to handle different page structures or extract additional data fields.

## Troubleshooting

### Common Issues

1. **Selenium WebDriver Error**: Ensure Chrome browser is installed and up to date
2. **Rate Limiting**: If blocked, increase delays in the RateLimiter class
3. **No Data Extracted**: The page structure may have changed; inspect the HTML manually
4. **Timeout Errors**: Increase timeout values in the scraping methods

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Dependencies

- `requests`: HTTP requests
- `beautifulsoup4`: HTML parsing
- `pandas`: Data manipulation and CSV export
- `selenium`: Browser automation
- `webdriver-manager`: Automatic WebDriver management
- `lxml`: Fast XML/HTML parser

## Contributing

When modifying the scraper:

1. Test with multiple event URLs
2. Update error handling for new edge cases
3. Maintain rate limiting best practices
4. Document any new configuration options

## License

This project is for educational purposes. Check Polymarket's terms of service before use.
