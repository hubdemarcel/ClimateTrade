"""
Example integration of real-time data client with existing Polymarket tools.

This script demonstrates how to use the real-time streaming client alongside
the existing Polymarket API client for comprehensive trading intelligence.
"""

import asyncio
import logging
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Import existing Polymarket tools
from agents.polymarket.polymarket import Polymarket

# Import the new real-time client
from real_time_client import (
    PolymarketRealTimeClient,
    create_market_subscription,
    create_activity_subscription,
    create_crypto_prices_subscription,
    Message
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class RealTimeTradingIntelligence:
    """
    Comprehensive trading intelligence system combining REST API and real-time streaming.

    This class demonstrates how to:
    1. Use existing Polymarket API for market discovery and order execution
    2. Stream real-time data for live updates
    3. Combine both for informed trading decisions
    """

    def __init__(self):
        # Initialize existing Polymarket client
        self.polymarket = Polymarket()

        # Initialize real-time client
        self.rt_client = PolymarketRealTimeClient(self.polymarket)

        # Data storage for real-time updates
        self.live_orderbooks: Dict[str, Dict[str, Any]] = {}
        self.live_prices: Dict[str, float] = {}
        self.recent_trades: list = []
        self.crypto_prices: Dict[str, Dict[str, Any]] = {}

        # Setup message handlers
        self._setup_message_handlers()

    def _setup_message_handlers(self):
        """Setup handlers for different types of real-time messages."""

        # Handle order book updates
        self.rt_client.add_message_handler("clob_market/agg_orderbook", self._handle_orderbook_update)

        # Handle price changes
        self.rt_client.add_message_handler("clob_market/price_change", self._handle_price_change)

        # Handle last trade prices
        self.rt_client.add_message_handler("clob_market/last_trade_price", self._handle_last_trade_price)

        # Handle activity/trades
        self.rt_client.add_message_handler("activity/trades", self._handle_trade_activity)

        # Handle crypto prices
        self.rt_client.add_message_handler("crypto_prices/update", self._handle_crypto_price)

    def _handle_orderbook_update(self, message: Message):
        """Handle real-time order book updates."""
        payload = message.payload
        market_id = payload.get("market")
        asset_id = payload.get("asset_id")

        self.live_orderbooks[asset_id] = {
            "market": market_id,
            "bids": payload.get("bids", []),
            "asks": payload.get("asks", []),
            "timestamp": payload.get("timestamp"),
            "hash": payload.get("hash")
        }

        logger.info(f"Updated orderbook for asset {asset_id}: {len(payload.get('bids', []))} bids, {len(payload.get('asks', []))} asks")

    def _handle_price_change(self, message: Message):
        """Handle real-time price changes."""
        payload = message.payload
        market_id = payload.get("m")  # market
        asset_id = payload.get("a")  # asset_id

        # Update live prices
        price = float(payload.get("p", 0))
        if asset_id:
            self.live_prices[asset_id] = price

        logger.info(f"Price change for asset {asset_id}: ${price}")

    def _handle_last_trade_price(self, message: Message):
        """Handle last trade price updates."""
        payload = message.payload
        asset_id = payload.get("asset_id")
        price = float(payload.get("price", 0))
        side = payload.get("side")

        if asset_id:
            self.live_prices[asset_id] = price

        logger.info(f"Last trade for asset {asset_id}: ${price} ({side})")

    def _handle_trade_activity(self, message: Message):
        """Handle trade activity from the activity stream."""
        payload = message.payload

        trade_info = {
            "asset_id": payload.get("asset"),
            "price": float(payload.get("price", 0)),
            "size": payload.get("size", 0),
            "side": payload.get("side"),
            "timestamp": payload.get("timestamp"),
            "market_slug": payload.get("slug"),
            "user": payload.get("pseudonym") or "Anonymous"
        }

        self.recent_trades.append(trade_info)

        # Keep only last 100 trades
        if len(self.recent_trades) > 100:
            self.recent_trades = self.recent_trades[-100:]

        logger.info(f"Trade: {trade_info['user']} {trade_info['side']} {trade_info['size']} @ ${trade_info['price']}")

    def _handle_crypto_price(self, message: Message):
        """Handle crypto price updates."""
        payload = message.payload
        symbol = payload.get("symbol")
        price = float(payload.get("value", 0))
        timestamp = payload.get("timestamp")

        if symbol:
            self.crypto_prices[symbol] = {
                "price": price,
                "timestamp": timestamp
            }

        logger.info(f"Crypto price update: {symbol} = ${price}")

    async def start_monitoring(self, market_limit: int = 5):
        """
        Start monitoring real-time data for active markets.

        Args:
            market_limit: Maximum number of markets to monitor
        """
        logger.info("Starting real-time market monitoring...")

        # Get active markets using existing API
        markets = self.polymarket.get_all_markets()
        active_markets = [m for m in markets if m.active][:market_limit]

        market_ids = []
        for market in active_markets:
            token_ids = eval(market.clob_token_ids)
            market_ids.extend(token_ids)

        logger.info(f"Monitoring {len(market_ids)} market tokens")

        # Start real-time streaming
        await self.rt_client.start_streaming(
            market_ids=market_ids,
            include_activity=True,
            include_crypto=True,
            crypto_symbols=["btcusdt", "ethusdt"]
        )

    async def stop_monitoring(self):
        """Stop real-time monitoring."""
        logger.info("Stopping real-time monitoring...")
        await self.rt_client.stop_streaming()

    def get_live_orderbook(self, asset_id: str) -> Dict[str, Any]:
        """Get the latest order book for a specific asset."""
        return self.live_orderbooks.get(asset_id, {})

    def get_live_price(self, asset_id: str) -> float:
        """Get the latest price for a specific asset."""
        return self.live_prices.get(asset_id, 0.0)

    def get_recent_trades(self, limit: int = 10) -> list:
        """Get recent trades."""
        return self.recent_trades[-limit:]

    def get_crypto_price(self, symbol: str) -> Dict[str, Any]:
        """Get latest crypto price."""
        return self.crypto_prices.get(symbol, {})

    def analyze_market_opportunity(self, asset_id: str) -> Dict[str, Any]:
        """
        Analyze market opportunity using both real-time and static data.

        This demonstrates how to combine real-time streaming with existing API calls.
        """
        # Get real-time data
        live_ob = self.get_live_orderbook(asset_id)
        live_price = self.get_live_price(asset_id)

        # Get static data from API
        try:
            market_data = self.polymarket.get_market(asset_id)
            static_price = float(eval(market_data.outcome_prices)[0])
        except:
            market_data = None
            static_price = 0.0

        # Simple analysis
        analysis = {
            "asset_id": asset_id,
            "live_price": live_price,
            "static_price": static_price,
            "price_difference": live_price - static_price,
            "orderbook_depth": {
                "bids": len(live_ob.get("bids", [])),
                "asks": len(live_ob.get("asks", []))
            },
            "recent_trades": len([t for t in self.recent_trades if t["asset_id"] == asset_id])
        }

        return analysis

async def main():
    """Main demonstration function."""
    print("🚀 Starting Polymarket Real-Time Trading Intelligence Demo")
    print("=" * 60)

    # Initialize the intelligence system
    intelligence = RealTimeTradingIntelligence()

    try:
        # Start monitoring
        monitoring_task = asyncio.create_task(intelligence.start_monitoring(market_limit=3))

        # Let it run for a while to collect data
        await asyncio.sleep(30)

        # Demonstrate data access
        print("\n📊 Current Market Intelligence:")
        print("-" * 40)

        # Show some analysis
        if intelligence.live_prices:
            asset_id = list(intelligence.live_prices.keys())[0]
            analysis = intelligence.analyze_market_opportunity(asset_id)
            print(f"Asset {asset_id}:")
            print(f"  Live Price: ${analysis['live_price']:.4f}")
            print(f"  Static Price: ${analysis['static_price']:.4f}")
            print(f"  Price Diff: ${analysis['price_difference']:.4f}")
            print(f"  Orderbook: {analysis['orderbook_depth']['bids']} bids, {analysis['orderbook_depth']['asks']} asks")

        # Show recent trades
        recent_trades = intelligence.get_recent_trades(5)
        if recent_trades:
            print(f"\n📈 Recent Trades ({len(recent_trades)}):")
            for trade in recent_trades:
                print(f"  {trade['user']} {trade['side']} {trade['size']} @ ${trade['price']:.4f}")

        # Show crypto prices
        btc_price = intelligence.get_crypto_price("btcusdt")
        if btc_price:
            print(f"\n₿ BTC Price: ${btc_price['price']:.2f}")

    except KeyboardInterrupt:
        print("\n⏹️  Stopping...")
    except Exception as e:
        logger.error(f"Error in demo: {e}")
    finally:
        await intelligence.stop_monitoring()
        print("\n✅ Demo completed")

if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("POLYGON_WALLET_PRIVATE_KEY"):
        print("❌ Please set POLYGON_WALLET_PRIVATE_KEY in your .env file")
        exit(1)

    # Run the demo
    asyncio.run(main())