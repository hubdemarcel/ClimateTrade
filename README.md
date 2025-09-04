# ClimaTrade AI

Weather-informed trading intelligence for Polymarket.

## Status

Project setup in progress.

## Folders

- data/ : Raw and processed data
- scripts/ : Data collection (includes Weather2Geo for geolocation from weather data)
- analysis/ : Research & notebooks
- web/ : Dashboard

## Weather2Geo Integration

The project includes Weather2Geo, a tool for geolocating based on weather widget screenshots.

### Setup Requirements

- Python 3.x
- Dependencies: typer, rich, pytz, timezonefinder, requests
- Install with: `pip install -r scripts/Weather2Geo/requirements.txt`

### Usage

Navigate to `scripts/Weather2Geo/` and run:

```
python main.py run --time "YYYY-MM-DD HH:MM" --condition "weather condition" --temp temperature
```

For example:

```
python main.py run --time "2025-05-22 22:09" --condition "Mostly clear" --temp 13
```

This can provide additional weather data points for the trading intelligence system.

## Polymarket API Integration

The project integrates the official Polymarket Python CLOB Client for accessing market data and executing trades on Polymarket.

### Setup Requirements

- Python 3.9+
- Private key for a wallet with funds on Polygon
- API credentials (optional, for authenticated requests)
- Install the client: `pip install -e scripts/polymarket-client/`
- Dependencies: eth-account, eth-utils, poly_eip712_structs, py-order-utils, python-dotenv, requests, websockets

### Environment Variables

Set the following in your `.env` file:

- `POLYGON_WALLET_PRIVATE_KEY`: Your wallet's private key
- `CLOB_API_KEY`: API key (optional)
- `CLOB_SECRET`: API secret (optional)
- `CLOB_PASS_PHRASE`: API passphrase (optional)

### Benefits over Scraping

Using the official API client provides:

- **Reliability**: Official API endpoints ensure consistent data access
- **Rate Limits**: Proper rate limiting prevents blocking
- **Authentication**: Secure access to trading and private data
- **Real-time Data**: Direct access to order books, prices, and market data
- **Trading Operations**: Execute limit and market orders programmatically
- **Compliance**: Official integration avoids terms of service violations

### Usage

The integration is handled through `scripts/agents/agents/polymarket/polymarket.py` and `gamma.py` modules, which provide:

- Market data retrieval
- Order book access
- Trade execution
- Balance management

For examples, see `scripts/polymarket-client/examples/`.

## Resolution Subgraph Integration

The project integrates Polymarket's resolution subgraph for accessing historical market resolution data and outcome information. This provides crucial historical context that complements real-time trading capabilities.

### What is the Resolution Subgraph?

The resolution subgraph is a The Graph protocol subgraph that indexes historical data about Polymarket market resolutions, including:

- **Market Resolution Status**: Tracks the complete lifecycle from initialization to final resolution
- **Dispute Data**: Records when markets are disputed and how disputes are resolved
- **Price History**: Captures proposed prices, disputed prices, and final resolution prices
- **Timestamp Data**: Provides precise timing for all resolution events
- **Ancillary Data**: Stores additional market context and conditions

### Setup Requirements

- Node.js and npm/yarn (for subgraph development)
- Python 3.9+ with requests library
- Access to Polygon RPC endpoint
- Install dependencies: `pip install -r scripts/requirements-resolution.txt`

### Environment Variables

For subgraph development, set in `scripts/resolution-subgraph/.env`:

- `MATIC_RPC_URL`: Polygon RPC endpoint (e.g., `https://polygon-rpc.com/`)

### Integration Benefits

The resolution subgraph complements existing Polymarket tools in several key ways:

#### 1. **Enhanced Backtesting with Polymarket Agents**

The resolution subgraph provides historical resolution data that enables sophisticated backtesting:

```python
from scripts.resolution_client import ResolutionSubgraphClient

# Get historical resolution data for strategy testing
client = ResolutionSubgraphClient()
historical_resolutions = client.get_market_resolutions(first=1000)

# Analyze patterns for AI model training
stats = calculate_resolution_stats(historical_resolutions)
```

**Key Benefits:**

- Train AI models on actual market resolution patterns
- Validate trading strategies against historical outcomes
- Identify dispute-prone market conditions
- Optimize agent behavior based on resolution success rates

#### 2. **Risk Assessment with Py-clob-client**

Real-time trading decisions can be enhanced with historical resolution context:

```python
# Combine real-time data with historical patterns
market_data = clob_client.get_market_data(market_id)
resolution_history = resolution_client.get_market_resolution_by_id(market_id)

# Assess market risk based on historical dispute rates
risk_level = assess_market_risk(resolution_history)
```

**Key Benefits:**

- Evaluate market reliability before placing orders
- Adjust position sizes based on historical dispute patterns
- Identify markets with clean resolution histories
- Make informed decisions about market participation

#### 3. **Comprehensive Market Analysis**

The combination enables end-to-end market analysis:

- **Real-time Monitoring**: Py-clob-client for current market state
- **Historical Context**: Resolution subgraph for past performance
- **AI Insights**: Agents for pattern recognition and strategy optimization
- **Weather Integration**: Weather2Geo for additional market context

### Usage Examples

#### Basic Resolution Data Access

```python
from scripts.resolution_client import ResolutionSubgraphClient

client = ResolutionSubgraphClient()

# Get recent market resolutions
recent_resolutions = client.get_market_resolutions(first=50)

# Get specific market resolution
market_resolution = client.get_market_resolution_by_id("market_id")

# Get disputed markets
disputed_markets = client.get_disputed_markets()
```

#### Advanced Integration Example

See `scripts/example_resolution_integration.py` for a comprehensive example that demonstrates:

- Market pattern analysis over time periods
- Risk assessment for individual markets
- Backtesting framework integration
- Strategy performance evaluation

#### Running the Integration

```bash
# Install dependencies
pip install -r scripts/requirements-resolution.txt

# Run the integration example
python scripts/example_resolution_integration.py
```

### Data Schema

The resolution subgraph provides the following key entities:

- **MarketResolution**: Core resolution data with status, prices, and timestamps
- **AncillaryDataHashToQuestionId**: Maps market data to question identifiers
- **Moderator**: Tracks moderator permissions and actions
- **Revision**: Audit trail of all market updates and changes

### Local Development

For local subgraph development:

```bash
cd scripts/resolution-subgraph

# Install dependencies
npm install

# Generate types
npm run codegen

# Start local Graph node
docker compose up

# Deploy subgraph locally
npm run create-local
npm run deploy-local
```

Access the local GraphQL playground at `http://localhost:8000/subgraphs/name/resolutions-subgraph/graphql`

### Production Deployment

The subgraph can be deployed to The Graph's hosted service or Goldsky for production use. Update the endpoint in `ResolutionSubgraphClient` accordingly.

### Best Practices

1. **Caching**: Cache frequently accessed resolution data to reduce API calls
2. **Rate Limiting**: Respect GraphQL endpoint rate limits
3. **Error Handling**: Implement robust error handling for network issues
4. **Data Validation**: Validate resolution data integrity before using in strategies
5. **Historical Depth**: Consider data freshness requirements for different use cases

This integration transforms the project from real-time trading to comprehensive market intelligence, enabling data-driven strategies that learn from historical patterns while operating in live markets.
