"""
Base strategy abstract class.
All trading strategies must inherit from this class.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import logging

from ..config.constants import SignalType

logger = logging.getLogger(__name__)


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.
    """

    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        """
        Initialize strategy with parameters.

        Args:
            parameters: Strategy-specific parameters
        """
        self.parameters = parameters or {}
        self.name = self.__class__.__name__
        logger.info(f"Initialized strategy: {self.name}")

    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators and add them to the dataframe.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with added indicator columns
        """
        pass

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on indicators.

        Args:
            df: DataFrame with OHLCV data and indicators

        Returns:
            DataFrame with added 'signal' column (-1: sell, 0: hold, 1: buy)
        """
        pass

    def should_enter(self, row: pd.Series) -> bool:
        """
        Check if should enter a position based on current data.

        Args:
            row: Current candle data with indicators

        Returns:
            True if should enter position, False otherwise
        """
        return row.get('signal', 0) == SignalType.BUY.value

    def should_exit(self, row: pd.Series, position: Optional[Dict] = None) -> bool:
        """
        Check if should exit current position.

        Args:
            row: Current candle data with indicators
            position: Current position information (optional)

        Returns:
            True if should exit position, False otherwise
        """
        return row.get('signal', 0) == SignalType.SELL.value

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data by calculating indicators and generating signals.

        Args:
            df: Raw OHLCV DataFrame

        Returns:
            DataFrame with indicators and signals
        """
        # Make a copy to avoid modifying original
        df = df.copy()

        # Calculate indicators
        df = self.calculate_indicators(df)

        # Generate signals
        df = self.generate_signals(df)

        return df

    def get_entry_reason(self, row: pd.Series) -> str:
        """
        Get reason for entry signal.

        Args:
            row: Current candle data

        Returns:
            Human-readable entry reason
        """
        return f"{self.name} entry signal"

    def get_exit_reason(self, row: pd.Series) -> str:
        """
        Get reason for exit signal.

        Args:
            row: Current candle data

        Returns:
            Human-readable exit reason
        """
        return f"{self.name} exit signal"

    def validate_signal(self, row: pd.Series, signal_type: SignalType) -> bool:
        """
        Validate if a signal is reliable.
        Can be overridden for additional validation logic.

        Args:
            row: Current candle data
            signal_type: Type of signal to validate

        Returns:
            True if signal is valid, False otherwise
        """
        # By default, all signals are valid
        # Subclasses can override this for custom validation
        return True

    def get_parameter(self, param_name: str, default: Any = None) -> Any:
        """
        Get a strategy parameter.

        Args:
            param_name: Parameter name
            default: Default value if parameter not found

        Returns:
            Parameter value or default
        """
        return self.parameters.get(param_name, default)

    def set_parameter(self, param_name: str, value: Any) -> None:
        """
        Set a strategy parameter.

        Args:
            param_name: Parameter name
            value: Parameter value
        """
        self.parameters[param_name] = value
        logger.debug(f"Set parameter {param_name} = {value}")

    def __str__(self) -> str:
        """String representation of strategy."""
        return f"{self.name}({self.parameters})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return self.__str__()
