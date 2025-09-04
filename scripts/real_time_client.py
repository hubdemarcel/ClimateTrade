"""
Real-time data client for Polymarket WebSocket streaming.

This module provides a Python implementation of the Polymarket real-time data client,
enabling streaming of live market data, order book updates, and price feeds.

Based on the TypeScript client from: https://github.com/Polymarket/real-time-data-client
"""

import json
import asyncio
import websockets
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ConnectionStatus(Enum):
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"

@dataclass
class ClobApiKeyCreds:
    """API key credentials for CLOB authentication."""
    key: str
    secret: str
    passphrase: str

@dataclass
class GammaAuth:
    """Authentication details for Gamma authentication."""
    address: str

@dataclass
class Subscription:
    """Represents a single subscription."""
    topic: str
    type: str
    filters: Optional[str] = None
    clob_auth: Optional[ClobApiKeyCreds] = None
    gamma_auth: Optional[GammaAuth] = None

@dataclass
class SubscriptionMessage:
    """Message structure for subscription requests."""
    subscriptions: List[Subscription]

@dataclass
class Message:
    """Represents a real-time message received from the WebSocket server."""
    topic: str
    type: str
    timestamp: int
    payload: Dict[str, Any]
    connection_id: str

class RealTimeDataClient:
    """
    A client for managing real-time WebSocket connections to Polymarket's streaming service.

    This client provides real-time streaming of:
    - Market trades and order book updates
    - Price changes and aggregated order books
    - User-specific order and trade data
    - Comments and other activity
    """

    DEFAULT_HOST = "wss://ws-live-data.polymarket.com"
    DEFAULT_PING_INTERVAL = 30  # seconds

    def __init__(
        self,
        on_message: Optional[Callable[['RealTimeDataClient', Message], None]] = None,
        on_connect: Optional[Callable[['RealTimeDataClient'], None]] = None,
        on_status_change: Optional[Callable[[ConnectionStatus], None]] = None,
        host: Optional[str] = None,
        ping_interval: Optional[int] = None,
        auto_reconnect: bool = True
    ):
        self.host = host or self.DEFAULT_HOST
        self.ping_interval = ping_interval or self.DEFAULT_PING_INTERVAL
        self.auto_reconnect = auto_reconnect

        self.on_message = on_message
        self.on_connect = on_connect
        self.on_status_change = on_status_change

        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.connection_status = ConnectionStatus.DISCONNECTED
        self._running = False
        self._ping_task: Optional[asyncio.Task] = None

    async def connect(self) -> None:
        """Establish WebSocket connection to the server."""
        self._running = True
        while self._running:
            try:
                self._set_status(ConnectionStatus.CONNECTING)
                async with websockets.connect(self.host) as websocket:
                    self.websocket = websocket
                    self._set_status(ConnectionStatus.CONNECTED)

                    if self.on_connect:
                        self.on_connect(self)

                    # Start ping task
                    self._ping_task = asyncio.create_task(self._ping_loop())

                    # Message handling loop
                    async for message in websocket:
                        await self._handle_message(message)

            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                self._set_status(ConnectionStatus.DISCONNECTED)
                if self._ping_task:
                    self._ping_task.cancel()
                    self._ping_task = None

                if self.auto_reconnect and self._running:
                    logger.info("Attempting to reconnect...")
                    await asyncio.sleep(5)  # Wait before reconnecting
                else:
                    break

    async def disconnect(self) -> None:
        """Close the WebSocket connection."""
        self._running = False
        self.auto_reconnect = False
        if self.websocket:
            await self.websocket.close()
        if self._ping_task:
            self._ping_task.cancel()

    async def subscribe(self, subscription_msg: SubscriptionMessage) -> None:
        """Subscribe to data streams."""
        if not self.websocket or self.connection_status != ConnectionStatus.CONNECTED:
            logger.warning("Not connected, cannot subscribe")
            return

        message = {
            "action": "subscribe",
            "subscriptions": [
                {
                    "topic": sub.topic,
                    "type": sub.type,
                    **({"filters": sub.filters} if sub.filters else {}),
                    **({"clob_auth": {
                        "key": sub.clob_auth.key,
                        "secret": sub.clob_auth.secret,
                        "passphrase": sub.clob_auth.passphrase
                    }} if sub.clob_auth else {}),
                    **({"gamma_auth": {"address": sub.gamma_auth.address}} if sub.gamma_auth else {})
                }
                for sub in subscription_msg.subscriptions
            ]
        }

        await self.websocket.send(json.dumps(message))
        logger.info(f"Subscribed to {len(subscription_msg.subscriptions)} topics")

    async def unsubscribe(self, subscription_msg: SubscriptionMessage) -> None:
        """Unsubscribe from data streams."""
        if not self.websocket or self.connection_status != ConnectionStatus.CONNECTED:
            logger.warning("Not connected, cannot unsubscribe")
            return

        message = {
            "action": "unsubscribe",
            "subscriptions": [
                {
                    "topic": sub.topic,
                    "type": sub.type,
                    **({"filters": sub.filters} if sub.filters else {}),
                    **({"clob_auth": {
                        "key": sub.clob_auth.key,
                        "secret": sub.clob_auth.secret,
                        "passphrase": sub.clob_auth.passphrase
                    }} if sub.clob_auth else {}),
                    **({"gamma_auth": {"address": sub.gamma_auth.address}} if sub.gamma_auth else {})
                }
                for sub in subscription_msg.subscriptions
            ]
        }

        await self.websocket.send(json.dumps(message))
        logger.info(f"Unsubscribed from {len(subscription_msg.subscriptions)} topics")

    async def _ping_loop(self) -> None:
        """Send periodic ping messages to keep connection alive."""
        while self._running and self.connection_status == ConnectionStatus.CONNECTED:
            try:
                if self.websocket:
                    await self.websocket.send("ping")
                await asyncio.sleep(self.ping_interval)
            except Exception as e:
                logger.error(f"Ping error: {e}")
                break

    async def _handle_message(self, raw_message: str) -> None:
        """Handle incoming WebSocket messages."""
        try:
            if raw_message and raw_message.strip():
                data = json.loads(raw_message)
                if "payload" in data and self.on_message:
                    message = Message(
                        topic=data.get("topic", ""),
                        type=data.get("type", ""),
                        timestamp=data.get("timestamp", 0),
                        payload=data.get("payload", {}),
                        connection_id=data.get("connection_id", "")
                    )
                    self.on_message(self, message)
                else:
                    logger.debug(f"Received non-data message: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    def _set_status(self, status: ConnectionStatus) -> None:
        """Update connection status and notify callback."""
        self.connection_status = status
        if self.on_status_change:
            self.on_status_change(status)
        logger.info(f"Connection status: {status.value}")

# Convenience functions for common subscriptions

def create_market_subscription(
    market_ids: List[str],
    types: Optional[List[str]] = None
) -> SubscriptionMessage:
    """
    Create subscription for market-related data.

    Args:
        market_ids: List of market/condition IDs
        types: Types to subscribe to (default: all market types)
    """
    if types is None:
        types = ["price_change", "agg_orderbook", "last_trade_price", "tick_size_change"]

    subscriptions = []
    for market_id in market_ids:
        for msg_type in types:
            subscriptions.append(Subscription(
                topic="clob_market",
                type=msg_type,
                filters=json.dumps([market_id])
            ))

    return SubscriptionMessage(subscriptions=subscriptions)

def create_activity_subscription(
    event_slugs: Optional[List[str]] = None,
    market_slugs: Optional[List[str]] = None
) -> SubscriptionMessage:
    """
    Create subscription for activity data (trades, orders matched).

    Args:
        event_slugs: List of event slugs to filter by
        market_slugs: List of market slugs to filter by
    """
    subscriptions = []

    for msg_type in ["trades", "orders_matched"]:
        filters = {}
        if event_slugs:
            filters["event_slug"] = event_slugs[0] if len(event_slugs) == 1 else event_slugs
        if market_slugs:
            filters["market_slug"] = market_slugs[0] if len(market_slugs) == 1 else market_slugs

        subscriptions.append(Subscription(
            topic="activity",
            type=msg_type,
            filters=json.dumps(filters) if filters else None
        ))

    return SubscriptionMessage(subscriptions=subscriptions)

def create_user_subscription(
    clob_auth: ClobApiKeyCreds,
    types: Optional[List[str]] = None
) -> SubscriptionMessage:
    """
    Create subscription for user-specific data.

    Args:
        clob_auth: CLOB API credentials
        types: Types to subscribe to (default: all user types)
    """
    if types is None:
        types = ["order", "trade"]

    subscriptions = []
    for msg_type in types:
        subscriptions.append(Subscription(
            topic="clob_user",
            type=msg_type,
            clob_auth=clob_auth
        ))

    return SubscriptionMessage(subscriptions=subscriptions)

def create_crypto_prices_subscription(symbols: List[str]) -> SubscriptionMessage:
    """
    Create subscription for crypto price updates.

    Args:
        symbols: List of crypto symbols (e.g., ["btcusdt", "ethusdt"])
    """
    subscriptions = []
    for symbol in symbols:
        subscriptions.append(Subscription(
            topic="crypto_prices",
            type="update",
            filters=json.dumps({"symbol": symbol})
        ))

    return SubscriptionMessage(subscriptions=subscriptions)

# Integration with existing Polymarket class

class PolymarketRealTimeClient:
    """
    Integration class that combines Polymarket API client with real-time streaming.

    This class provides a unified interface for both REST API calls and real-time streaming.
    """

    def __init__(self, polymarket_client):
        self.polymarket = polymarket_client
        self.rt_client: Optional[RealTimeDataClient] = None
        self._subscriptions: List[SubscriptionMessage] = []
        self._message_handlers: Dict[str, Callable] = {}

    async def start_streaming(
        self,
        market_ids: Optional[List[str]] = None,
        include_activity: bool = True,
        include_crypto: bool = False,
        crypto_symbols: Optional[List[str]] = None,
        include_user_data: bool = False
    ) -> None:
        """
        Start real-time streaming for specified markets and data types.

        Args:
            market_ids: List of market IDs to stream (if None, uses active markets)
            include_activity: Whether to include activity data (trades, etc.)
            include_crypto: Whether to include crypto price data
            crypto_symbols: List of crypto symbols to track
            include_user_data: Whether to include user-specific data (requires auth)
        """
        if not self.rt_client:
            self.rt_client = RealTimeDataClient(
                on_message=self._handle_message,
                on_connect=self._handle_connect,
                on_status_change=self._handle_status_change
            )

        # Determine market IDs
        if market_ids is None:
            # Get active markets from Polymarket client
            markets = self.polymarket.get_all_markets()
            active_markets = [m for m in markets if m.active]
            market_ids = []
            for market in active_markets[:10]:  # Limit to first 10 for demo
                token_ids = eval(market.clob_token_ids)
                market_ids.extend(token_ids)

        # Create subscriptions
        subscriptions = []

        if market_ids:
            subscriptions.append(create_market_subscription(market_ids))

        if include_activity:
            subscriptions.append(create_activity_subscription())

        if include_crypto and crypto_symbols:
            subscriptions.append(create_crypto_prices_subscription(crypto_symbols))

        if include_user_data and hasattr(self.polymarket, 'credentials'):
            # Create CLOB auth from existing credentials
            clob_auth = ClobApiKeyCreds(
                key=self.polymarket.credentials.api_key,
                secret=self.polymarket.credentials.api_secret,
                passphrase=self.polymarket.credentials.api_passphrase
            )
            subscriptions.append(create_user_subscription(clob_auth))

        self._subscriptions = subscriptions

        # Start the client
        await self.rt_client.connect()

    async def stop_streaming(self) -> None:
        """Stop real-time streaming."""
        if self.rt_client:
            await self.rt_client.disconnect()
            self.rt_client = None

    def add_message_handler(self, topic_type: str, handler: Callable) -> None:
        """
        Add a custom message handler for specific topic/type combinations.

        Args:
            topic_type: String in format "topic/type" (e.g., "clob_market/price_change")
            handler: Function to call when message received
        """
        self._message_handlers[topic_type] = handler

    async def _handle_connect(self, client: RealTimeDataClient) -> None:
        """Handle WebSocket connection established."""
        logger.info("Connected to Polymarket real-time stream")

        # Subscribe to all configured subscriptions
        for subscription in self._subscriptions:
            await client.subscribe(subscription)

    async def _handle_message(self, client: RealTimeDataClient, message: Message) -> None:
        """Handle incoming real-time messages."""
        topic_type = f"{message.topic}/{message.type}"

        # Call specific handler if registered
        if topic_type in self._message_handlers:
            self._message_handlers[topic_type](message)
        else:
            # Default handling
            self._default_message_handler(message)

    def _handle_status_change(self, status: ConnectionStatus) -> None:
        """Handle connection status changes."""
        logger.info(f"Real-time client status: {status.value}")

    def _default_message_handler(self, message: Message) -> None:
        """Default message handler - logs the message."""
        logger.info(f"Received {message.topic}/{message.type}: {message.payload}")

# Example usage and testing functions

async def example_usage():
    """Example of how to use the real-time client."""
    # This would be integrated with the existing Polymarket class
    # For now, just demonstrate the client

    def on_message(client, message):
        print(f"[{message.topic}/{message.type}] {message.payload}")

    def on_connect(client):
        print("Connected!")

    client = RealTimeDataClient(on_message=on_message, on_connect=on_connect)

    # Subscribe to some market data
    subscription = create_market_subscription(["100", "200"])  # Example market IDs

    # In a real scenario, this would run in an event loop
    # await client.connect()

if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())