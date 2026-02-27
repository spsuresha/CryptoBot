"""
Exchange connector using CCXT library.
Handles connection to cryptocurrency exchanges with retry logic and rate limiting.
"""
import time
import logging
from typing import Dict, List, Optional, Any
import ccxt
from ccxt.base.errors import (
    NetworkError,
    ExchangeError,
    RequestTimeout,
    ExchangeNotAvailable,
    RateLimitExceeded,
)

from ..config.settings import Settings
from ..config.constants import (
    DEFAULT_RETRY_ATTEMPTS,
    DEFAULT_RETRY_DELAY,
    DEFAULT_MAX_RETRY_DELAY,
)

logger = logging.getLogger(__name__)


class ExchangeConnector:
    """
    Wrapper around CCXT exchange with retry logic and rate limiting.
    """

    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize exchange connector.

        Args:
            settings: Application settings instance
        """
        self.settings = settings or Settings()
        self.exchange: Optional[ccxt.Exchange] = None
        self._connected = False

    def connect(self) -> None:
        """
        Initialize connection to the exchange.

        Raises:
            ValueError: If exchange configuration is invalid
            ExchangeError: If connection fails
        """
        try:
            # Get exchange class
            exchange_class = getattr(ccxt, self.settings.exchange_name)

            # Configure exchange options
            config = {
                'enableRateLimit': self.settings.enable_rate_limit,
                'rateLimit': int(self.settings.rate_limit_delay * 1000),  # ms
            }

            # Add API keys if not in dry run mode
            if not self.settings.is_dry_run_mode():
                config['apiKey'] = self.settings.binance_api_key
                config['secret'] = self.settings.binance_secret_key

            # Set testnet if configured
            if self.settings.exchange_testnet:
                config['options'] = {'defaultType': 'future'}
                if self.settings.exchange_name == 'binance':
                    config['options']['testnet'] = True

            # Initialize exchange
            self.exchange = exchange_class(config)

            # Load markets
            self.exchange.load_markets()

            self._connected = True
            logger.info(
                f"Connected to {self.settings.exchange_name} "
                f"(testnet={self.settings.exchange_testnet})"
            )

        except Exception as e:
            logger.error(f"Failed to connect to exchange: {e}")
            raise

    def _retry_on_error(
        self,
        func,
        *args,
        max_retries: int = DEFAULT_RETRY_ATTEMPTS,
        **kwargs
    ) -> Any:
        """
        Execute a function with exponential backoff retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            max_retries: Maximum number of retry attempts
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function call

        Raises:
            Exception: If all retry attempts fail
        """
        retry_delay = DEFAULT_RETRY_DELAY

        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)

            except RateLimitExceeded as e:
                logger.warning(f"Rate limit exceeded: {e}")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, DEFAULT_MAX_RETRY_DELAY)

            except (RequestTimeout, ExchangeNotAvailable, NetworkError) as e:
                logger.warning(
                    f"Network error (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, DEFAULT_MAX_RETRY_DELAY)
                else:
                    logger.error(f"Failed after {max_retries} attempts")
                    raise

            except ExchangeError as e:
                logger.error(f"Exchange error: {e}")
                raise

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise

        raise Exception(f"Failed after {max_retries} retry attempts")

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        since: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[List]:
        """
        Fetch OHLCV (candlestick) data.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            timeframe: Timeframe (e.g., '1m', '5m', '1h', '1d')
            since: Timestamp in milliseconds to start from
            limit: Maximum number of candles to fetch

        Returns:
            List of OHLCV data [[timestamp, open, high, low, close, volume], ...]

        Raises:
            ExchangeError: If fetch fails
        """
        self._ensure_connected()

        logger.debug(
            f"Fetching OHLCV for {symbol} {timeframe} "
            f"(since={since}, limit={limit})"
        )

        return self._retry_on_error(
            self.exchange.fetch_ohlcv,
            symbol,
            timeframe,
            since,
            limit
        )

    def fetch_balance(self) -> Dict[str, Any]:
        """
        Fetch account balance.

        Returns:
            Dictionary with balance information

        Raises:
            ExchangeError: If fetch fails
        """
        self._ensure_connected()

        if self.settings.is_dry_run_mode():
            logger.debug("Dry run mode: returning mock balance")
            return {
                'free': {'USDT': 10000.0},
                'used': {'USDT': 0.0},
                'total': {'USDT': 10000.0},
            }

        logger.debug("Fetching account balance")
        return self._retry_on_error(self.exchange.fetch_balance)

    def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Create an order on the exchange.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            order_type: Order type ('market' or 'limit')
            side: Order side ('buy' or 'sell')
            amount: Amount to buy/sell
            price: Price for limit orders
            params: Additional parameters

        Returns:
            Order information dictionary

        Raises:
            ExchangeError: If order creation fails
        """
        self._ensure_connected()

        if self.settings.is_dry_run_mode():
            logger.info(
                f"DRY RUN: Would create {side} {order_type} order for "
                f"{amount} {symbol} at {price}"
            )
            return {
                'id': 'dry_run_order',
                'symbol': symbol,
                'type': order_type,
                'side': side,
                'amount': amount,
                'price': price,
                'status': 'closed',
            }

        logger.info(
            f"Creating {side} {order_type} order: {amount} {symbol}"
            + (f" at {price}" if price else "")
        )

        return self._retry_on_error(
            self.exchange.create_order,
            symbol,
            order_type,
            side,
            amount,
            price,
            params or {}
        )

    def fetch_open_orders(
        self,
        symbol: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch open orders.

        Args:
            symbol: Optional trading pair symbol to filter by

        Returns:
            List of open orders

        Raises:
            ExchangeError: If fetch fails
        """
        self._ensure_connected()

        if self.settings.is_dry_run_mode():
            logger.debug("Dry run mode: returning empty orders list")
            return []

        logger.debug(f"Fetching open orders for {symbol or 'all pairs'}")
        return self._retry_on_error(self.exchange.fetch_open_orders, symbol)

    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Cancel an open order.

        Args:
            order_id: Order ID to cancel
            symbol: Trading pair symbol

        Returns:
            Cancelled order information

        Raises:
            ExchangeError: If cancellation fails
        """
        self._ensure_connected()

        if self.settings.is_dry_run_mode():
            logger.info(f"DRY RUN: Would cancel order {order_id} for {symbol}")
            return {'id': order_id, 'status': 'canceled'}

        logger.info(f"Cancelling order {order_id} for {symbol}")
        return self._retry_on_error(
            self.exchange.cancel_order,
            order_id,
            symbol
        )

    def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch current ticker information.

        Args:
            symbol: Trading pair symbol

        Returns:
            Ticker information including last price, bid, ask, etc.

        Raises:
            ExchangeError: If fetch fails
        """
        self._ensure_connected()

        logger.debug(f"Fetching ticker for {symbol}")
        return self._retry_on_error(self.exchange.fetch_ticker, symbol)

    def fetch_order_book(
        self,
        symbol: str,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fetch order book (bids and asks).

        Args:
            symbol: Trading pair symbol
            limit: Number of orders to fetch

        Returns:
            Order book with bids and asks

        Raises:
            ExchangeError: If fetch fails
        """
        self._ensure_connected()

        logger.debug(f"Fetching order book for {symbol}")
        return self._retry_on_error(
            self.exchange.fetch_order_book,
            symbol,
            limit
        )

    def _ensure_connected(self) -> None:
        """
        Ensure exchange is connected.

        Raises:
            ConnectionError: If exchange is not connected
        """
        if not self._connected or self.exchange is None:
            raise ConnectionError(
                "Exchange not connected. Call connect() first."
            )

    def is_connected(self) -> bool:
        """Check if exchange is connected."""
        return self._connected and self.exchange is not None

    def close(self) -> None:
        """Close exchange connection and cleanup."""
        if self.exchange:
            self.exchange.close()
            self._connected = False
            logger.info("Exchange connection closed")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
