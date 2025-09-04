#!/usr/bin/env python3
"""
Unit Tests for Real-Time Data Client

Comprehensive unit tests for the Polymarket real-time WebSocket client,
including connection handling, subscription management, and message processing.
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from unittest.mock import AsyncMock as AsyncMockType

from ..real_time_client import (
    RealTimeDataClient,
    ConnectionStatus,
    ClobApiKeyCreds,
    GammaAuth,
    Subscription,
    SubscriptionMessage,
    Message,
    create_market_subscription,
    create_activity_subscription,
    create_user_subscription,
    create_crypto_prices_subscription,
    PolymarketRealTimeClient
)


@pytest.fixture
def sample_credentials():
    """Sample API credentials for testing"""
    return ClobApiKeyCreds(
        key="test_key_123",
        secret="test_secret_456",
        passphrase="test_passphrase"
    )


@pytest.fixture
def sample_gamma_auth():
    """Sample Gamma authentication for testing"""
    return GammaAuth(address="0x1234567890abcdef")


@pytest.fixture
def sample_subscription():
    """Sample subscription for testing"""
    return Subscription(
        topic="clob_market",
        type="price_change",
        filters='["market1"]',
        clob_auth=None,
        gamma_auth=None
    )


@pytest.fixture
def sample_subscription_message(sample_subscription):
    """Sample subscription message for testing"""
    return SubscriptionMessage(subscriptions=[sample_subscription])


@pytest.fixture
def sample_message():
    """Sample message for testing"""
    return Message(
        topic="clob_market",
        type="price_change",
        timestamp=1640995200,
        payload={"market_id": "market1", "price": 0.6},
        connection_id="conn_123"
    )


class TestRealTimeDataClient:
    """Test cases for RealTimeDataClient"""

    def test_initialization(self):
        """Test client initialization with default parameters"""
        client = RealTimeDataClient()

        assert client.host == "wss://ws-live-data.polymarket.com"
        assert client.ping_interval == 30
        assert client.auto_reconnect == True
        assert client.connection_status == ConnectionStatus.DISCONNECTED
        assert client.websocket is None
        assert client._running == False

    def test_initialization_custom_params(self):
        """Test client initialization with custom parameters"""
        def on_message(c, m): pass
        def on_connect(c): pass
        def on_status(s): pass

        client = RealTimeDataClient(
            on_message=on_message,
            on_connect=on_connect,
            on_status_change=on_status,
            host="wss://custom-host.com",
            ping_interval=60,
            auto_reconnect=False
        )

        assert client.host == "wss://custom-host.com"
        assert client.ping_interval == 60
        assert client.auto_reconnect == False
        assert client.on_message == on_message
        assert client.on_connect == on_connect
        assert client.on_status_change == on_status

    @patch('websockets.connect', new_callable=AsyncMock)
    async def test_connect_success(self, mock_websocket_connect):
        """Test successful WebSocket connection"""
        # Mock WebSocket connection
        mock_websocket = AsyncMock()
        mock_websocket_connect.return_value.__aenter__.return_value = mock_websocket
        mock_websocket_connect.return_value.__aexit__.return_value = None

        # Mock message handling
        mock_websocket.__aiter__.return_value = []

        client = RealTimeDataClient(auto_reconnect=False)

        # Start connection in background task
        connect_task = asyncio.create_task(client.connect())

        # Wait a bit for connection to establish
        await asyncio.sleep(0.1)

        # Check connection status
        assert client.connection_status == ConnectionStatus.CONNECTED

        # Stop the client
        await client.disconnect()
        connect_task.cancel()

        try:
            await connect_task
        except asyncio.CancelledError:
            pass

    @patch('websockets.connect', new_callable=AsyncMock)
    async def test_connect_with_reconnection(self, mock_websocket_connect):
        """Test connection with auto-reconnection"""
        # Mock WebSocket that fails initially then succeeds
        mock_websocket = AsyncMock()
        mock_websocket_connect.side_effect = [
            Exception("Connection failed"),  # First attempt fails
            mock_websocket  # Second attempt succeeds
        ]

        # Mock context manager for successful connection
        mock_websocket_connect.return_value.__aenter__.return_value = mock_websocket
        mock_websocket_connect.return_value.__aexit__.return_value = None
        mock_websocket.__aiter__.return_value = []

        client = RealTimeDataClient(auto_reconnect=True)

        # Start connection
        connect_task = asyncio.create_task(client.connect())

        # Wait for reconnection
        await asyncio.sleep(0.2)

        # Should eventually connect
        assert client.connection_status == ConnectionStatus.CONNECTED

        # Clean up
        await client.disconnect()
        connect_task.cancel()

        try:
            await connect_task
        except asyncio.CancelledError:
            pass

    async def test_subscribe_not_connected(self, sample_subscription_message):
        """Test subscription attempt when not connected"""
        client = RealTimeDataClient()
        client.connection_status = ConnectionStatus.DISCONNECTED

        # Should not raise exception, just log warning
        await client.subscribe(sample_subscription_message)

        # WebSocket should be None
        assert client.websocket is None

    async def test_unsubscribe_not_connected(self, sample_subscription_message):
        """Test unsubscription attempt when not connected"""
        client = RealTimeDataClient()
        client.connection_status = ConnectionStatus.DISCONNECTED

        # Should not raise exception, just log warning
        await client.unsubscribe(sample_subscription_message)

        # WebSocket should be None
        assert client.websocket is None

    @patch('websockets.connect', new_callable=AsyncMock)
    async def test_subscribe_success(self, mock_websocket_connect, sample_subscription_message):
        """Test successful subscription"""
        mock_websocket = AsyncMock()
        mock_websocket_connect.return_value.__aenter__.return_value = mock_websocket
        mock_websocket_connect.return_value.__aexit__.return_value = None
        mock_websocket.__aiter__.return_value = []

        client = RealTimeDataClient(auto_reconnect=False)

        # Start connection
        connect_task = asyncio.create_task(client.connect())
        await asyncio.sleep(0.1)  # Let connection establish

        # Subscribe
        await client.subscribe(sample_subscription_message)

        # Verify WebSocket send was called
        mock_websocket.send.assert_called_once()
        call_args = mock_websocket.send.call_args[0][0]
        sent_data = json.loads(call_args)

        assert sent_data['action'] == 'subscribe'
        assert 'subscriptions' in sent_data
        assert len(sent_data['subscriptions']) == 1

        # Clean up
        await client.disconnect()
        connect_task.cancel()

        try:
            await connect_task
        except asyncio.CancelledError:
            pass

    @patch('websockets.connect', new_callable=AsyncMock)
    async def test_unsubscribe_success(self, mock_websocket_connect, sample_subscription_message):
        """Test successful unsubscription"""
        mock_websocket = AsyncMock()
        mock_websocket_connect.return_value.__aenter__.return_value = mock_websocket
        mock_websocket_connect.return_value.__aexit__.return_value = None
        mock_websocket.__aiter__.return_value = []

        client = RealTimeDataClient(auto_reconnect=False)

        # Start connection
        connect_task = asyncio.create_task(client.connect())
        await asyncio.sleep(0.1)  # Let connection establish

        # Unsubscribe
        await client.unsubscribe(sample_subscription_message)

        # Verify WebSocket send was called
        mock_websocket.send.assert_called_once()
        call_args = mock_websocket.send.call_args[0][0]
        sent_data = json.loads(call_args)

        assert sent_data['action'] == 'unsubscribe'
        assert 'subscriptions' in sent_data
        assert len(sent_data['subscriptions']) == 1

        # Clean up
        await client.disconnect()
        connect_task.cancel()

        try:
            await connect_task
        except asyncio.CancelledError:
            pass

    @patch('websockets.connect', new_callable=AsyncMock)
    async def test_message_handling(self, mock_websocket_connect, sample_message):
        """Test incoming message handling"""
        mock_websocket = AsyncMock()
        mock_websocket_connect.return_value.__aenter__.return_value = mock_websocket
        mock_websocket_connect.return_value.__aexit__.return_value = None

        # Mock message data
        message_data = {
            "topic": sample_message.topic,
            "type": sample_message.type,
            "timestamp": sample_message.timestamp,
            "payload": sample_message.payload,
            "connection_id": sample_message.connection_id
        }

        # WebSocket returns messages then stops
        mock_websocket.__aiter__.return_value = [json.dumps(message_data), None]

        on_message_called = False
        received_message = None

        def on_message(client, message):
            nonlocal on_message_called, received_message
            on_message_called = True
            received_message = message

        client = RealTimeDataClient(on_message=on_message, auto_reconnect=False)

        # Start connection
        connect_task = asyncio.create_task(client.connect())

        # Wait for message processing
        await asyncio.sleep(0.1)

        # Check that message handler was called
        assert on_message_called
        assert received_message is not None
        assert received_message.topic == sample_message.topic
        assert received_message.type == sample_message.type
        assert received_message.payload == sample_message.payload

        # Clean up
        await client.disconnect()
        connect_task.cancel()

        try:
            await connect_task
        except asyncio.CancelledError:
            pass

    async def test_disconnect(self):
        """Test client disconnection"""
        client = RealTimeDataClient()

        # Should not raise exception even when not connected
        await client.disconnect()

        assert client._running == False
        assert client.auto_reconnect == False


class TestSubscriptionFunctions:
    """Test cases for subscription creation functions"""

    def test_create_market_subscription(self):
        """Test market subscription creation"""
        market_ids = ["market1", "market2"]
        subscription_msg = create_market_subscription(market_ids)

        assert isinstance(subscription_msg, SubscriptionMessage)
        assert len(subscription_msg.subscriptions) == 4  # 2 markets * 4 types

        # Check subscription details
        for sub in subscription_msg.subscriptions:
            assert sub.topic == "clob_market"
            assert sub.type in ["price_change", "agg_orderbook", "last_trade_price", "tick_size_change"]
            assert sub.filters == json.dumps(market_ids)

    def test_create_market_subscription_custom_types(self):
        """Test market subscription with custom types"""
        market_ids = ["market1"]
        types = ["price_change", "last_trade_price"]
        subscription_msg = create_market_subscription(market_ids, types)

        assert len(subscription_msg.subscriptions) == 2  # 1 market * 2 types

        for sub in subscription_msg.subscriptions:
            assert sub.type in types

    def test_create_activity_subscription(self):
        """Test activity subscription creation"""
        subscription_msg = create_activity_subscription()

        assert isinstance(subscription_msg, SubscriptionMessage)
        assert len(subscription_msg.subscriptions) == 2  # trades and orders_matched

        for sub in subscription_msg.subscriptions:
            assert sub.topic == "activity"
            assert sub.type in ["trades", "orders_matched"]
            assert sub.filters is None

    def test_create_activity_subscription_with_filters(self):
        """Test activity subscription with event and market filters"""
        event_slugs = ["event1"]
        market_slugs = ["market1"]
        subscription_msg = create_activity_subscription(event_slugs, market_slugs)

        assert len(subscription_msg.subscriptions) == 2

        for sub in subscription_msg.subscriptions:
            filters = json.loads(sub.filters)
            assert filters["event_slug"] == event_slugs
            assert filters["market_slug"] == market_slugs

    def test_create_user_subscription(self, sample_credentials):
        """Test user subscription creation"""
        subscription_msg = create_user_subscription(sample_credentials)

        assert isinstance(subscription_msg, SubscriptionMessage)
        assert len(subscription_msg.subscriptions) == 2  # order and trade

        for sub in subscription_msg.subscriptions:
            assert sub.topic == "clob_user"
            assert sub.type in ["order", "trade"]
            assert sub.clob_auth == sample_credentials

    def test_create_user_subscription_custom_types(self, sample_credentials):
        """Test user subscription with custom types"""
        types = ["order"]
        subscription_msg = create_user_subscription(sample_credentials, types)

        assert len(subscription_msg.subscriptions) == 1
        assert subscription_msg.subscriptions[0].type == "order"

    def test_create_crypto_prices_subscription(self):
        """Test crypto prices subscription creation"""
        symbols = ["btcusdt", "ethusdt"]
        subscription_msg = create_crypto_prices_subscription(symbols)

        assert isinstance(subscription_msg, SubscriptionMessage)
        assert len(subscription_msg.subscriptions) == 2

        for sub in subscription_msg.subscriptions:
            assert sub.topic == "crypto_prices"
            assert sub.type == "update"
            filters = json.loads(sub.filters)
            assert filters["symbol"] in symbols


class TestPolymarketRealTimeClient:
    """Test cases for PolymarketRealTimeClient"""

    def test_initialization(self):
        """Test PolymarketRealTimeClient initialization"""
        mock_polymarket = Mock()
        client = PolymarketRealTimeClient(mock_polymarket)

        assert client.polymarket == mock_polymarket
        assert client.rt_client is None
        assert client._subscriptions == []
        assert client._message_handlers == {}

    def test_add_message_handler(self):
        """Test adding message handlers"""
        mock_polymarket = Mock()
        client = PolymarketRealTimeClient(mock_polymarket)

        def handler(message):
            pass

        client.add_message_handler("clob_market/price_change", handler)

        assert "clob_market/price_change" in client._message_handlers
        assert client._message_handlers["clob_market/price_change"] == handler

    @patch('scripts.real_time_client.RealTimeDataClient', new_callable=AsyncMock)
    async def test_start_streaming_basic(self, mock_rt_client_class):
        """Test basic streaming start"""
        mock_polymarket = Mock()
        mock_rt_client = AsyncMock()
        mock_rt_client_class.return_value = mock_rt_client

        client = PolymarketRealTimeClient(mock_polymarket)

        await client.start_streaming(market_ids=["market1"])

        # Verify RealTimeDataClient was created
        mock_rt_client_class.assert_called_once()
        # Verify connect was called
        mock_rt_client.connect.assert_called_once()

    async def test_stop_streaming(self):
        """Test streaming stop"""
        mock_polymarket = Mock()
        client = PolymarketRealTimeClient(mock_polymarket)

        # Set up mock rt_client
        mock_rt_client = AsyncMock()
        client.rt_client = mock_rt_client

        await client.stop_streaming()

        # Verify disconnect was called
        mock_rt_client.disconnect.assert_called_once()
        # Verify rt_client was cleared
        assert client.rt_client is None


class TestDataClasses:
    """Test cases for data classes"""

    def test_clob_api_key_creds(self, sample_credentials):
        """Test ClobApiKeyCreds dataclass"""
        assert sample_credentials.key == "test_key_123"
        assert sample_credentials.secret == "test_secret_456"
        assert sample_credentials.passphrase == "test_passphrase"

    def test_gamma_auth(self, sample_gamma_auth):
        """Test GammaAuth dataclass"""
        assert sample_gamma_auth.address == "0x1234567890abcdef"

    def test_subscription(self, sample_subscription):
        """Test Subscription dataclass"""
        assert sample_subscription.topic == "clob_market"
        assert sample_subscription.type == "price_change"
        assert sample_subscription.filters == '["market1"]'
        assert sample_subscription.clob_auth is None
        assert sample_subscription.gamma_auth is None

    def test_subscription_message(self, sample_subscription_message):
        """Test SubscriptionMessage dataclass"""
        assert len(sample_subscription_message.subscriptions) == 1
        assert sample_subscription_message.subscriptions[0].topic == "clob_market"

    def test_message(self, sample_message):
        """Test Message dataclass"""
        assert sample_message.topic == "clob_market"
        assert sample_message.type == "price_change"
        assert sample_message.timestamp == 1640995200
        assert sample_message.payload == {"market_id": "market1", "price": 0.6}
        assert sample_message.connection_id == "conn_123"


if __name__ == '__main__':
    pytest.main([__file__])