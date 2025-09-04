# Polymarket Real-Time Data Integration

This document describes the integration of Polymarket's real-time data streaming capabilities with the existing Polymarket trading tools for comprehensive real-time trading intelligence.

## Overview

The integration consists of:

1. **Real-Time Data Client** (`real_time_client.py`): A Python WebSocket client that connects to Polymarket's real-time streaming service
2. **Integration Layer** (`PolymarketRealTimeClient`): Combines the real-time client with existing Polymarket API tools
3. **Example Implementation** (`example_real_time_integration.py`): Demonstrates practical usage

## Architecture

### Real-Time Data Client

The `RealTimeDataClient` class provides:

- **WebSocket Connection**: Connects to `wss://ws-live-data.polymarket.com`
- **Subscription Management**: Subscribe/unsubscribe to various data streams
- **Authentication Support**: Handles CLOB API authentication for user-specific data
- **Auto-Reconnection**: Maintains connection with automatic reconnection
- **Message Handling**: Processes incoming real-time messages

### Integration with Existing Tools

The `PolymarketRealTimeClient` class integrates with:

- **Polymarket API Client**: Uses existing `Polymarket` class for REST API calls
- **Authentication**: Leverages existing API credentials
- **Market Discovery**: Discovers active markets via existing API
- **Unified Interface**: Single class for both real-time and static data

## Data Streams Available

### Market Data (clob_market)

- `price_change`: Real-time price updates
- `agg_orderbook`: Aggregated order book snapshots
- `last_trade_price`: Latest trade prices
- `tick_size_change`: Tick size updates
- `market_created/resolved`: Market lifecycle events

### Activity Data (activity)

- `trades`: Real-time trade executions
- `orders_matched`: Order matching events

### User Data (clob_user) - Requires Authentication

- `order`: User order updates
- `trade`: User trade executions

### Comments (comments)

- `comment_created/removed`: Comment activity
- `reaction_created/removed`: Reaction activity

### RFQ (Request for Quote)

- `request_created/edited/canceled/expired`: RFQ lifecycle
- `quote_created/edited/canceled/expired`: Quote responses

### Crypto Prices (crypto_prices)

- `update`: Real-time cryptocurrency price updates

## Installation

### Dependencies

Install the required Python packages:

```bash
pip install -r requirements-real-time.txt
```

Required packages:

- `websockets>=11.0.0`: WebSocket client library
- `python-dotenv>=0.19.0`: Environment variable management

### Existing Dependencies

The integration uses existing Polymarket tools which require:

```bash
pip install -r requirements.txt  # Existing Polymarket agent requirements
pip install py-clob-client      # Polymarket CLOB client
```

## Usage

### Basic Real-Time Client

```python
import asyncio
from real_time_client import RealTimeDataClient, create_market_subscription

async def main():
    def on_message(client, message):
        print(f"Received: {message.topic}/{message.type}")
        print(f"Payload: {message.payload}")

    def on_connect(client):
        print("Connected to real-time stream!")

    # Create client
    client = RealTimeDataClient(on_message=on_message, on_connect=on_connect)

    # Subscribe to market data
    subscription = create_market_subscription(["100", "200"])  # Market IDs
    await client.subscribe(subscription)

    # Connect and start streaming
    await client.connect()

asyncio.run(main())
```

### Integrated Trading Intelligence

```python
import asyncio
from example_real_time_integration import RealTimeTradingIntelligence

async def main():
    # Initialize intelligence system
    intelligence = RealTimeTradingIntelligence()

    try:
        # Start monitoring active markets
        await intelligence.start_monitoring(market_limit=5)

        # Let it collect data
        await asyncio.sleep(60)

        # Access real-time data
        asset_id = "some_asset_id"
        orderbook = intelligence.get_live_orderbook(asset_id)
        price = intelligence.get_live_price(asset_id)
        trades = intelligence.get_recent_trades(10)

        # Analyze opportunities
        analysis = intelligence.analyze_market_opportunity(asset_id)

    finally:
        await intelligence.stop_monitoring()

asyncio.run(main())
```

## Message Formats

### Order Book Update

```json
{
  "topic": "clob_market",
  "type": "agg_orderbook",
  "timestamp": 1640995200000,
  "payload": {
    "market": "0x123...",
    "asset_id": "456...",
    "bids": [
      { "price": "0.50", "size": "100" },
      { "price": "0.49", "size": "200" }
    ],
    "asks": [
      { "price": "0.51", "size": "150" },
      { "price": "0.52", "size": "300" }
    ],
    "timestamp": 1640995200000,
    "hash": "abc123..."
  }
}
```

### Trade Activity

```json
{
  "topic": "activity",
  "type": "trades",
  "timestamp": 1640995200000,
  "payload": {
    "asset": "456...",
    "price": "0.50",
    "size": 100,
    "side": "BUY",
    "timestamp": 1640995200000,
    "slug": "market-slug",
    "pseudonym": "Trader123"
  }
}
```

### Price Change

```json
{
  "topic": "clob_market",
  "type": "price_change",
  "timestamp": 1640995200000,
  "payload": {
    "m": "0x123...", // market
    "a": "456...", // asset_id
    "p": "0.50", // price
    "s": "BUY", // side
    "si": "100", // size
    "ba": "0.49", // best_ask
    "bb": "0.48" // best_bid
  }
}
```

## Authentication

For user-specific data streams, provide CLOB API credentials:

```python
from real_time_client import ClobApiKeyCreds, create_user_subscription

# Create auth credentials
clob_auth = ClobApiKeyCreds(
    key="your_api_key",
    secret="your_api_secret",
    passphrase="your_passphrase"
)

# Subscribe to user data
subscription = create_user_subscription(clob_auth)
await client.subscribe(subscription)
```

## Integration Benefits

### Real-Time vs Polling

| Aspect         | Polling (Existing)  | Real-Time (New) |
| -------------- | ------------------- | --------------- |
| Latency        | 1-5 seconds         | <100ms          |
| Server Load    | High                | Low             |
| Data Freshness | Stale between polls | Always current  |
| Event-Driven   | No                  | Yes             |

### Use Cases

1. **High-Frequency Trading**: React instantly to price changes
2. **Order Book Analysis**: Monitor liquidity changes in real-time
3. **Trade Signal Generation**: Immediate response to market events
4. **Risk Management**: Real-time position monitoring
5. **Arbitrage Detection**: Spot price discrepancies instantly

### Combined Strategy

```python
class SmartTrader:
    def __init__(self):
        self.polymarket = Polymarket()  # REST API
        self.rt_client = PolymarketRealTimeClient(self.polymarket)

    async def trade_strategy(self):
        # Use REST API for market discovery
        markets = self.polymarket.get_all_markets()

        # Use real-time for live monitoring
        await self.rt_client.start_streaming(market_ids=[...])

        # Combine both for informed decisions
        for market in markets:
            live_price = self.rt_client.get_live_price(market.id)
            static_data = self.polymarket.get_market(market.id)

            if self.should_trade(live_price, static_data):
                self.execute_trade(market.id, live_price)
```

## Configuration

### Environment Variables

```bash
# Required for Polymarket API
POLYGON_WALLET_PRIVATE_KEY=your_private_key

# Optional: CLOB API credentials for user data
CLOB_API_KEY=your_api_key
CLOB_SECRET=your_api_secret
CLOB_PASS_PHRASE=your_passphrase
```

### Client Configuration

```python
client = RealTimeDataClient(
    host="wss://ws-live-data.polymarket.com",  # Default
    ping_interval=30,  # Seconds between ping messages
    auto_reconnect=True,  # Auto reconnect on disconnection
    on_message=message_handler,
    on_connect=connect_handler,
    on_status_change=status_handler
)
```

## Error Handling

### Connection Issues

```python
def on_status_change(status):
    if status == ConnectionStatus.DISCONNECTED:
        logger.warning("Real-time connection lost")
        # Implement reconnection logic or fallback to polling
    elif status == ConnectionStatus.CONNECTED:
        logger.info("Real-time connection established")
```

### Message Parsing Errors

```python
async def safe_message_handler(client, message):
    try:
        # Process message
        process_message(message)
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        # Continue processing other messages
```

## Performance Considerations

### Memory Management

- Limit stored historical data
- Use circular buffers for recent trades
- Clean up old order book snapshots

### Rate Limiting

- WebSocket handles rate limiting automatically
- Implement message filtering to reduce processing load
- Use sampling for high-frequency data

### Connection Stability

- Auto-reconnection is enabled by default
- Implement exponential backoff for reconnection attempts
- Monitor connection health and implement fallbacks

## Testing

### Unit Tests

```python
import pytest
from real_time_client import RealTimeDataClient, create_market_subscription

def test_subscription_creation():
    subscription = create_market_subscription(["100", "200"])
    assert len(subscription.subscriptions) == 2
    assert subscription.subscriptions[0].topic == "clob_market"

def test_message_parsing():
    # Test message parsing logic
    pass
```

### Integration Tests

```python
async def test_real_time_connection():
    client = RealTimeDataClient()
    await client.connect()

    # Verify connection
    assert client.connection_status == ConnectionStatus.CONNECTED

    await client.disconnect()
```

## Troubleshooting

### Common Issues

1. **Connection Failed**

   - Check internet connectivity
   - Verify WebSocket URL
   - Check firewall settings

2. **Authentication Errors**

   - Verify API credentials
   - Check credential format
   - Ensure credentials have required permissions

3. **No Messages Received**

   - Verify subscription format
   - Check market IDs exist
   - Ensure proper filters

4. **High Latency**
   - Check network connection
   - Monitor server load
   - Consider data sampling

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### Planned Features

1. **Message Persistence**: Store streaming data to database
2. **Advanced Analytics**: Real-time technical indicators
3. **Alert System**: Custom price/trade alerts
4. **Multi-Market Support**: Cross-market arbitrage detection
5. **Machine Learning Integration**: Real-time prediction models

### API Improvements

1. **Batch Subscriptions**: Subscribe to multiple topics efficiently
2. **Filtered Streams**: Server-side message filtering
3. **Compression**: Message compression for bandwidth efficiency
4. **Authentication**: Enhanced auth methods

## Contributing

To contribute to the real-time integration:

1. Follow existing code patterns
2. Add comprehensive tests
3. Update documentation
4. Ensure backward compatibility
5. Test with existing Polymarket tools

## License

This integration follows the same license as the original Polymarket tools.

## Support

For issues with the real-time integration:

1. Check this documentation
2. Review existing Polymarket documentation
3. Check GitHub issues
4. Contact Polymarket support

---

_This integration provides a powerful combination of real-time streaming data with comprehensive trading tools, enabling sophisticated automated trading strategies on the Polymarket platform._
