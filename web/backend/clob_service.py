"""
CLOB Service for Polymarket Trading Integration
"""

from typing import Optional, Dict, List, Any
import logging
from datetime import datetime
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds, OrderArgs, MarketOrderArgs, OrderType
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class CLOBService:
    """Service for interacting with Polymarket CLOB"""

    def __init__(self):
        self.client: Optional[ClobClient] = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the CLOB client with configuration"""
        try:
            # Load configuration from environment
            private_key = os.getenv('POLYGON_WALLET_PRIVATE_KEY')
            api_key = os.getenv('CLOB_API_KEY')
            passphrase = os.getenv('CLOB_PASSPHRASE')
            funder = os.getenv('POLYGON_FUNDER_ADDRESS')

            if not private_key:
                logger.warning("POLYGON_WALLET_PRIVATE_KEY not configured - read-only mode")
                # Initialize read-only client
                self.client = ClobClient("https://clob.polymarket.com")
                return

            if not api_key or not passphrase:
                logger.warning("CLOB credentials incomplete - limited functionality")
                # Initialize with private key but no API auth
                self.client = ClobClient(
                    host="https://clob.polymarket.com",
                    key=private_key,
                    chain_id=137,
                    signature_type=1,
                    funder=funder
                )
                return

            # Full initialization with authentication
            self.client = ClobClient(
                host="https://clob.polymarket.com",
                key=private_key,
                chain_id=137,  # Polygon
                signature_type=1,  # Email/Magic wallet
                funder=funder
            )

            # Set API credentials
            creds = ApiCreds(
                api_key=api_key,
                api_secret="",  # Will be derived
                api_passphrase=passphrase
            )
            self.client.set_api_creds(creds)

            logger.info("CLOB client initialized with full authentication")

        except Exception as e:
            logger.error(f"Failed to initialize CLOB client: {str(e)}")
            # Fallback to read-only
            try:
                self.client = ClobClient("https://clob.polymarket.com")
                logger.info("Fallback to read-only CLOB client")
            except Exception as fallback_error:
                logger.error(f"Failed to initialize read-only client: {str(fallback_error)}")
                self.client = None

    def get_client(self) -> Optional[ClobClient]:
        """Get the CLOB client instance"""
        return self.client

    def is_connected(self) -> bool:
        """Check if client is properly connected"""
        if not self.client:
            return False
        try:
            self.client.get_server_time()
            return True
        except Exception:
            return False

    def is_authenticated(self) -> bool:
        """Check if client has trading authentication"""
        if not self.client:
            return False
        # Check if we have API credentials set
        return hasattr(self.client, 'creds') and self.client.creds is not None

    def get_markets(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get available markets"""
        if not self.client:
            raise Exception("CLOB client not initialized")

        try:
            markets = self.client.get_simplified_markets()
            data = markets.get('data', [])

            # Add some useful fields and limit results
            for market in data[:limit]:
                market['last_updated'] = datetime.now().isoformat()
                market['source'] = 'polymarket'

            return data[:limit]
        except Exception as e:
            logger.error(f"Failed to get markets: {str(e)}")
            raise Exception(f"Failed to retrieve markets: {str(e)}")

    def get_market_details(self, market_id: str) -> Dict[str, Any]:
        """Get detailed market information"""
        if not self.client:
            raise Exception("CLOB client not initialized")

        try:
            market = self.client.get_market(market_id)
            return market
        except Exception as e:
            logger.error(f"Failed to get market details: {str(e)}")
            raise Exception(f"Failed to retrieve market details: {str(e)}")

    def get_order_book(self, token_id: str) -> Dict[str, Any]:
        """Get order book for a specific token"""
        if not self.client:
            raise Exception("CLOB client not initialized")

        try:
            orderbook = self.client.get_order_book(token_id)
            return {
                'token_id': token_id,
                'bids': orderbook.bids or [],
                'asks': orderbook.asks or [],
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get order book: {str(e)}")
            raise Exception(f"Failed to retrieve order book: {str(e)}")

    def get_price(self, token_id: str, side: str = "BUY") -> Dict[str, Any]:
        """Get current market price for a token"""
        if not self.client:
            raise Exception("CLOB client not initialized")

        try:
            price = self.client.get_price(token_id, side)
            return {
                'token_id': token_id,
                'side': side,
                'price': float(price),
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get price: {str(e)}")
            raise Exception(f"Failed to retrieve price: {str(e)}")

    def get_balance(self) -> Dict[str, Any]:
        """Get user balance and allowance"""
        if not self.client:
            raise Exception("CLOB client not initialized")

        if not self.is_authenticated():
            raise Exception("Authentication required for balance information")

        try:
            balance = self.client.get_balance_allowance()
            return balance
        except Exception as e:
            logger.error(f"Failed to get balance: {str(e)}")
            raise Exception(f"Failed to retrieve balance: {str(e)}")

    def get_open_orders(self) -> List[Dict[str, Any]]:
        """Get user's open orders"""
        if not self.client:
            raise Exception("CLOB client not initialized")

        if not self.is_authenticated():
            raise Exception("Authentication required for order information")

        try:
            orders = self.client.get_orders()
            return orders
        except Exception as e:
            logger.error(f"Failed to get orders: {str(e)}")
            raise Exception(f"Failed to retrieve orders: {str(e)}")

    def place_limit_order(self, token_id: str, price: float, size: float, side: str) -> Dict[str, Any]:
        """Place a limit order"""
        if not self.client:
            raise Exception("CLOB client not initialized")

        if not self.is_authenticated():
            raise Exception("Authentication required for trading")

        try:
            # Create order arguments
            order_args = OrderArgs(
                token_id=token_id,
                price=price,
                size=size,
                side=side.upper()
            )

            # Create and post order
            signed_order = self.client.create_order(order_args)
            result = self.client.post_order(signed_order)

            return {
                'order_id': result.get('orderID'),
                'status': 'placed',
                'token_id': token_id,
                'price': price,
                'size': size,
                'side': side,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to place limit order: {str(e)}")
            raise Exception(f"Failed to place order: {str(e)}")

    def place_market_order(self, token_id: str, amount: float, side: str) -> Dict[str, Any]:
        """Place a market order"""
        if not self.client:
            raise Exception("CLOB client not initialized")

        if not self.is_authenticated():
            raise Exception("Authentication required for trading")

        try:
            # Create market order arguments
            order_args = MarketOrderArgs(
                token_id=token_id,
                amount=amount,
                side=side.upper(),
                order_type=OrderType.FOK  # Fill or Kill
            )

            # Create and post order
            signed_order = self.client.create_market_order(order_args)
            result = self.client.post_order(signed_order, OrderType.FOK)

            return {
                'order_id': result.get('orderID'),
                'status': 'placed',
                'token_id': token_id,
                'amount': amount,
                'side': side,
                'type': 'market',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to place market order: {str(e)}")
            raise Exception(f"Failed to place market order: {str(e)}")

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        if not self.client:
            raise Exception("CLOB client not initialized")

        if not self.is_authenticated():
            raise Exception("Authentication required for order management")

        try:
            result = self.client.cancel(order_id)
            return {
                'order_id': order_id,
                'status': 'cancelled',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to cancel order: {str(e)}")
            raise Exception(f"Failed to cancel order: {str(e)}")

    def cancel_all_orders(self) -> Dict[str, Any]:
        """Cancel all open orders"""
        if not self.client:
            raise Exception("CLOB client not initialized")

        if not self.is_authenticated():
            raise Exception("Authentication required for order management")

        try:
            result = self.client.cancel_all()
            return {
                'status': 'all_orders_cancelled',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {str(e)}")
            raise Exception(f"Failed to cancel all orders: {str(e)}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get system status and capabilities"""
        return {
            'connected': self.is_connected(),
            'authenticated': self.is_authenticated(),
            'server_time': self.client.get_server_time() if self.client else None,
            'last_check': datetime.now().isoformat()
        }

# Global service instance
clob_service = CLOBService()