"""
Data fetcher for OHLCV (candlestick) data with caching support.
"""
import logging
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
import pandas as pd

from .connector import ExchangeConnector
from ..config.settings import Settings
from ..config.constants import TIMEFRAME_MINUTES

logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Fetches and caches OHLCV data from exchange.
    """

    def __init__(
        self,
        connector: ExchangeConnector,
        settings: Optional[Settings] = None
    ):
        """
        Initialize data fetcher.

        Args:
            connector: Exchange connector instance
            settings: Application settings
        """
        self.connector = connector
        self.settings = settings or Settings()
        self.cache_dir = Path(self.settings.project_root) / "data"
        self.cache_dir.mkdir(exist_ok=True)

    def fetch_ohlcv_dataframe(
        self,
        symbol: str,
        timeframe: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data and return as pandas DataFrame.

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Timeframe (e.g., '1m', '5m', '1h')
            since: Start datetime (optional)
            until: End datetime (optional)
            limit: Maximum number of candles (optional)

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        # Convert datetime to milliseconds
        since_ms = int(since.timestamp() * 1000) if since else None
        until_ms = int(until.timestamp() * 1000) if until else None

        # Fetch data in chunks if date range is large
        if since_ms and until_ms:
            all_data = self._fetch_date_range(
                symbol, timeframe, since_ms, until_ms
            )
        else:
            all_data = self.connector.fetch_ohlcv(
                symbol, timeframe, since_ms, limit
            )

        # Convert to DataFrame
        df = self._ohlcv_to_dataframe(all_data)

        # Filter by until date if specified
        if until_ms and not df.empty:
            df = df[df['timestamp'] <= until_ms]

        logger.info(
            f"Fetched {len(df)} candles for {symbol} {timeframe}"
        )

        return df

    def _fetch_date_range(
        self,
        symbol: str,
        timeframe: str,
        since_ms: int,
        until_ms: int,
    ) -> List[List]:
        """
        Fetch OHLCV data for a date range in chunks.

        Args:
            symbol: Trading pair
            timeframe: Timeframe
            since_ms: Start timestamp in milliseconds
            until_ms: End timestamp in milliseconds

        Returns:
            List of OHLCV candles
        """
        all_data = []
        current_since = since_ms

        # Calculate chunk size based on timeframe
        timeframe_minutes = TIMEFRAME_MINUTES.get(timeframe, 1)
        chunk_size = 1000  # Maximum candles per request
        chunk_duration_ms = chunk_size * timeframe_minutes * 60 * 1000

        while current_since < until_ms:
            logger.debug(
                f"Fetching chunk starting from "
                f"{datetime.fromtimestamp(current_since / 1000)}"
            )

            try:
                chunk = self.connector.fetch_ohlcv(
                    symbol,
                    timeframe,
                    current_since,
                    chunk_size
                )

                if not chunk:
                    break

                all_data.extend(chunk)

                # Update starting point for next chunk
                last_timestamp = chunk[-1][0]
                current_since = last_timestamp + 1

                # Break if we've reached the end date
                if last_timestamp >= until_ms:
                    break

            except Exception as e:
                logger.error(f"Error fetching chunk: {e}")
                break

        return all_data

    def _ohlcv_to_dataframe(self, ohlcv_data: List[List]) -> pd.DataFrame:
        """
        Convert OHLCV list to pandas DataFrame.

        Args:
            ohlcv_data: List of OHLCV candles

        Returns:
            DataFrame with proper column names and types
        """
        if not ohlcv_data:
            return pd.DataFrame(
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )

        df = pd.DataFrame(
            ohlcv_data,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )

        # Convert timestamp to datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Set datetime as index
        df.set_index('datetime', inplace=True)

        # Ensure numeric types
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    def save_to_cache(
        self,
        symbol: str,
        timeframe: str,
        df: pd.DataFrame
    ) -> None:
        """
        Save DataFrame to cache file.

        Args:
            symbol: Trading pair
            timeframe: Timeframe
            df: DataFrame to save
        """
        cache_file = self._get_cache_filename(symbol, timeframe)

        try:
            df.to_pickle(cache_file)
            logger.debug(f"Saved {len(df)} candles to cache: {cache_file}")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def load_from_cache(
        self,
        symbol: str,
        timeframe: str
    ) -> Optional[pd.DataFrame]:
        """
        Load DataFrame from cache file.

        Args:
            symbol: Trading pair
            timeframe: Timeframe

        Returns:
            Cached DataFrame or None if not found
        """
        cache_file = self._get_cache_filename(symbol, timeframe)

        if not cache_file.exists():
            return None

        try:
            df = pd.read_pickle(cache_file)
            logger.debug(f"Loaded {len(df)} candles from cache: {cache_file}")
            return df
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return None

    def fetch_latest_candles(
        self,
        symbol: str,
        timeframe: str,
        count: int = 100
    ) -> pd.DataFrame:
        """
        Fetch the latest N candles.

        Args:
            symbol: Trading pair
            timeframe: Timeframe
            count: Number of candles to fetch

        Returns:
            DataFrame with latest candles
        """
        return self.fetch_ohlcv_dataframe(
            symbol=symbol,
            timeframe=timeframe,
            limit=count
        )

    def fetch_with_cache(
        self,
        symbol: str,
        timeframe: str,
        since: datetime,
        until: datetime,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """
        Fetch data with intelligent caching.
        Loads from cache and only fetches new data if needed.

        Args:
            symbol: Trading pair
            timeframe: Timeframe
            since: Start datetime
            until: End datetime
            force_refresh: Force fetching from exchange

        Returns:
            DataFrame with OHLCV data
        """
        if force_refresh:
            df = self.fetch_ohlcv_dataframe(symbol, timeframe, since, until)
            self.save_to_cache(symbol, timeframe, df)
            return df

        # Try to load from cache
        cached_df = self.load_from_cache(symbol, timeframe)

        if cached_df is None or cached_df.empty:
            # No cache, fetch all data
            df = self.fetch_ohlcv_dataframe(symbol, timeframe, since, until)
            self.save_to_cache(symbol, timeframe, df)
            return df

        # Check if cached data covers the requested range
        cache_start = cached_df['timestamp'].min()
        cache_end = cached_df['timestamp'].max()

        since_ms = int(since.timestamp() * 1000)
        until_ms = int(until.timestamp() * 1000)

        needs_update = cache_end < until_ms or cache_start > since_ms

        if not needs_update:
            # Cache is sufficient
            return cached_df[
                (cached_df['timestamp'] >= since_ms) &
                (cached_df['timestamp'] <= until_ms)
            ]

        # Fetch missing data
        if cache_end < until_ms:
            # Fetch newer data
            new_data = self.fetch_ohlcv_dataframe(
                symbol,
                timeframe,
                since=datetime.fromtimestamp(cache_end / 1000),
                until=until
            )
            cached_df = pd.concat([cached_df, new_data]).drop_duplicates(
                subset=['timestamp']
            ).sort_values('timestamp')

        if cache_start > since_ms:
            # Fetch older data
            old_data = self.fetch_ohlcv_dataframe(
                symbol,
                timeframe,
                since=since,
                until=datetime.fromtimestamp(cache_start / 1000)
            )
            cached_df = pd.concat([old_data, cached_df]).drop_duplicates(
                subset=['timestamp']
            ).sort_values('timestamp')

        # Save updated cache
        self.save_to_cache(symbol, timeframe, cached_df)

        # Return requested range
        return cached_df[
            (cached_df['timestamp'] >= since_ms) &
            (cached_df['timestamp'] <= until_ms)
        ]

    def _get_cache_filename(self, symbol: str, timeframe: str) -> Path:
        """
        Get cache filename for symbol and timeframe.

        Args:
            symbol: Trading pair
            timeframe: Timeframe

        Returns:
            Path to cache file
        """
        # Replace / with _ for filename safety
        safe_symbol = symbol.replace('/', '_')
        return self.cache_dir / f"{safe_symbol}_{timeframe}.pkl"

    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """
        Clear cached data.

        Args:
            symbol: Optional symbol to clear. If None, clears all cache.
        """
        if symbol:
            # Clear specific symbol
            for cache_file in self.cache_dir.glob(f"{symbol.replace('/', '_')}_*.pkl"):
                cache_file.unlink()
                logger.info(f"Cleared cache: {cache_file}")
        else:
            # Clear all cache
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
            logger.info("Cleared all cache files")
