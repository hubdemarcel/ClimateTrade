#!/usr/bin/env python3
"""
Base Strategy Framework for Weather-Based Trading

Defines the interface and base classes for implementing trading strategies
that use weather data to generate trading signals on Polymarket.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class TradingSignal:
    """Represents a trading signal"""
    timestamp: datetime
    market_id: str
    outcome_name: str
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 0.0 to 1.0
    quantity: Optional[float] = None
    price: Optional[float] = None
    reasoning: Optional[str] = None


@dataclass
class Position:
    """Represents a trading position"""
    market_id: str
    outcome_name: str
    quantity: float
    entry_price: float
    entry_time: datetime
    current_price: Optional[float] = None
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    pnl: float = 0.0
    status: str = 'OPEN'  # 'OPEN', 'CLOSED', 'STOPPED'


class BaseWeatherStrategy(ABC):
    """
    Abstract base class for weather-based trading strategies

    Strategies should implement the generate_signals method to analyze
    weather data and market conditions to produce trading signals.
    """

    def __init__(self, name: str, parameters: Optional[Dict[str, Any]] = None):
        self.name = name
        self.parameters = parameters or {}
        self.positions: List[Position] = []
        self.signals_history: List[TradingSignal] = []
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def generate_signals(self,
                        market_data: pd.DataFrame,
                        weather_data: pd.DataFrame,
                        current_positions: List[Position]) -> List[TradingSignal]:
        """
        Generate trading signals based on market and weather data

        Args:
            market_data: Current market data (probabilities, volumes, etc.)
            weather_data: Current weather data for relevant locations
            current_positions: List of currently open positions

        Returns:
            List of trading signals to execute
        """
        pass

    def update_positions(self,
                        signals: List[TradingSignal],
                        market_data: pd.DataFrame) -> List[Position]:
        """
        Update positions based on generated signals

        Args:
            signals: Trading signals to execute
            market_data: Current market data for price information

        Returns:
            Updated list of positions
        """
        updated_positions = self.positions.copy()

        for signal in signals:
            if signal.signal_type == 'BUY':
                position = self._open_position(signal, market_data)
                if position:
                    updated_positions.append(position)
                    self.signals_history.append(signal)

            elif signal.signal_type == 'SELL':
                closed_positions = self._close_positions(signal, market_data, updated_positions)
                updated_positions.extend(closed_positions)
                self.signals_history.append(signal)

        self.positions = updated_positions
        return self.positions

    def _open_position(self, signal: TradingSignal, market_data: pd.DataFrame) -> Optional[Position]:
        """Open a new position based on signal"""
        # Get current market price
        current_data = market_data[
            (market_data['market_id'] == signal.market_id) &
            (market_data['outcome_name'] == signal.outcome_name)
        ]

        if current_data.empty:
            self.logger.warning(f"No market data found for {signal.market_id}:{signal.outcome_name}")
            return None

        current_price = current_data['probability'].iloc[-1]
        quantity = signal.quantity or 1.0  # Default quantity

        position = Position(
            market_id=signal.market_id,
            outcome_name=signal.outcome_name,
            quantity=quantity,
            entry_price=current_price,
            entry_time=signal.timestamp,
            current_price=current_price
        )

        self.logger.info(f"Opened position: {signal.market_id}:{signal.outcome_name} "
                        f"at {current_price:.3f} (qty: {quantity})")
        return position

    def _close_positions(self,
                        signal: TradingSignal,
                        market_data: pd.DataFrame,
                        positions: List[Position]) -> List[Position]:
        """Close positions matching the signal"""
        closed_positions = []

        for position in positions:
            if (position.market_id == signal.market_id and
                position.outcome_name == signal.outcome_name and
                position.status == 'OPEN'):

                # Get current market price
                current_data = market_data[
                    (market_data['market_id'] == signal.market_id) &
                    (market_data['outcome_name'] == signal.outcome_name)
                ]

                if not current_data.empty:
                    exit_price = current_data['probability'].iloc[-1]
                    position.exit_price = exit_price
                    position.exit_time = signal.timestamp
                    position.pnl = (exit_price - position.entry_price) * position.quantity
                    position.status = 'CLOSED'

                    self.logger.info(f"Closed position: {signal.market_id}:{signal.outcome_name} "
                                    f"PNL: {position.pnl:.4f}")
                    closed_positions.append(position)

        return closed_positions

    def get_open_positions(self) -> List[Position]:
        """Get all currently open positions"""
        return [p for p in self.positions if p.status == 'OPEN']

    def get_closed_positions(self) -> List[Position]:
        """Get all closed positions"""
        return [p for p in self.positions if p.status == 'CLOSED']

    def get_total_pnl(self) -> float:
        """Calculate total realized P&L"""
        return sum(p.pnl for p in self.get_closed_positions())

    def get_strategy_metrics(self) -> Dict[str, Any]:
        """Get strategy performance metrics"""
        closed_positions = self.get_closed_positions()
        open_positions = self.get_open_positions()

        if not closed_positions:
            return {
                'total_pnl': 0.0,
                'total_trades': 0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'open_positions': len(open_positions)
            }

        winning_trades = [p for p in closed_positions if p.pnl > 0]
        losing_trades = [p for p in closed_positions if p.pnl < 0]

        return {
            'total_pnl': sum(p.pnl for p in closed_positions),
            'total_trades': len(closed_positions),
            'win_rate': len(winning_trades) / len(closed_positions),
            'avg_win': np.mean([p.pnl for p in winning_trades]) if winning_trades else 0.0,
            'avg_loss': np.mean([p.pnl for p in losing_trades]) if losing_trades else 0.0,
            'open_positions': len(open_positions)
        }


class WeatherThresholdStrategy(BaseWeatherStrategy):
    """
    Example strategy: Trade based on weather thresholds

    This strategy generates signals when weather conditions cross predefined thresholds.
    """

    def __init__(self,
                 name: str = "WeatherThresholdStrategy",
                 parameters: Optional[Dict[str, Any]] = None):
        super().__init__(name, parameters)

        # Default parameters
        self.temperature_threshold = self.parameters.get('temperature_threshold', 25.0)
        self.humidity_threshold = self.parameters.get('humidity_threshold', 80.0)
        self.signal_strength_threshold = self.parameters.get('signal_strength_threshold', 0.7)

    def generate_signals(self,
                        market_data: pd.DataFrame,
                        weather_data: pd.DataFrame,
                        current_positions: List[Position]) -> List[TradingSignal]:
        """
        Generate signals based on weather thresholds
        """
        signals = []

        # Group weather data by location
        weather_by_location = weather_data.groupby('location_name')

        for location, weather_group in weather_by_location:
            latest_weather = weather_group.iloc[-1] if not weather_group.empty else None
            if latest_weather is None:
                continue

            # Check temperature threshold
            if latest_weather['temperature'] > self.temperature_threshold:
                signal = self._create_temperature_signal(
                    latest_weather, market_data, 'HIGH_TEMP'
                )
                if signal:
                    signals.append(signal)

            # Check humidity threshold
            if latest_weather['humidity'] > self.humidity_threshold:
                signal = self._create_humidity_signal(
                    latest_weather, market_data, 'HIGH_HUMIDITY'
                )
                if signal:
                    signals.append(signal)

        return signals

    def _create_temperature_signal(self,
                                  weather_row: pd.Series,
                                  market_data: pd.DataFrame,
                                  signal_type: str) -> Optional[TradingSignal]:
        """Create signal based on temperature conditions"""
        # Find relevant markets (this would need market-weather mapping logic)
        relevant_markets = market_data[
            market_data['timestamp'] >= weather_row['timestamp'] - pd.Timedelta(hours=1)
        ]

        if relevant_markets.empty:
            return None

        # Use the most recent market data
        latest_market = relevant_markets.iloc[-1]

        confidence = min(1.0, (weather_row['temperature'] - self.temperature_threshold) / 10.0)

        if confidence >= self.signal_strength_threshold:
            return TradingSignal(
                timestamp=weather_row['timestamp'],
                market_id=latest_market['market_id'],
                outcome_name=latest_market['outcome_name'],
                signal_type='BUY',
                confidence=confidence,
                reasoning=f"Temperature {weather_row['temperature']:.1f}°C exceeds threshold {self.temperature_threshold}°C"
            )

        return None

    def _create_humidity_signal(self,
                               weather_row: pd.Series,
                               market_data: pd.DataFrame,
                               signal_type: str) -> Optional[TradingSignal]:
        """Create signal based on humidity conditions"""
        # Similar logic to temperature signal
        relevant_markets = market_data[
            market_data['timestamp'] >= weather_row['timestamp'] - pd.Timedelta(hours=1)
        ]

        if relevant_markets.empty:
            return None

        latest_market = relevant_markets.iloc[-1]

        confidence = min(1.0, (weather_row['humidity'] - self.humidity_threshold) / 20.0)

        if confidence >= self.signal_strength_threshold:
            return TradingSignal(
                timestamp=weather_row['timestamp'],
                market_id=latest_market['market_id'],
                outcome_name=latest_market['outcome_name'],
                signal_type='BUY',
                confidence=confidence,
                reasoning=f"Humidity {weather_row['humidity']:.1f}% exceeds threshold {self.humidity_threshold}%"
            )

        return None