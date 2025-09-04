#!/usr/bin/env python3
"""
Backtesting Engine Core

The main engine that simulates trading strategies against historical data,
managing the execution timeline, position tracking, and results collection.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..data.data_loader import BacktestingDataLoader
from ..strategies.base_strategy import BaseWeatherStrategy, Position, TradingSignal
from ..metrics.performance_metrics import PerformanceMetrics
from ..risk.risk_metrics import RiskMetrics

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Container for backtest results"""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    positions: List[Position] = field(default_factory=list)
    signals: List[TradingSignal] = field(default_factory=list)
    equity_curve: List[Tuple[datetime, float]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BacktestConfig:
    """Configuration for backtesting run"""
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10000.0
    commission_per_trade: float = 0.001  # 0.1%
    max_position_size: float = 0.1  # 10% of capital per position
    max_positions: int = 10
    data_frequency: str = 'H'  # Hourly
    enable_parallel: bool = False
    risk_free_rate: float = 0.02  # 2% annual risk-free rate


class BacktestingEngine:
    """
    Core backtesting engine that simulates trading strategies

    Handles data loading, strategy execution, position management,
    and results calculation across specified time periods.
    """

    def __init__(self, config: BacktestConfig, db_path: str = "data/climatetrade.db"):
        self.config = config
        self.data_loader = BacktestingDataLoader(db_path)
        self.performance_metrics = PerformanceMetrics()
        self.risk_metrics = RiskMetrics()
        self.logger = logging.getLogger(__name__)

    def run_backtest(self,
                    strategy: BaseWeatherStrategy,
                    market_ids: Optional[List[str]] = None,
                    locations: Optional[List[str]] = None) -> BacktestResult:
        """
        Run a complete backtest for a given strategy

        Args:
            strategy: The trading strategy to test
            market_ids: Specific market IDs to test (None for all)
            locations: Specific weather locations to use (None for all)

        Returns:
            BacktestResult with complete performance data
        """
        self.logger.info(f"Starting backtest for strategy: {strategy.name}")
        self.logger.info(f"Period: {self.config.start_date} to {self.config.end_date}")

        # Load historical data
        market_data = self.data_loader.load_market_data(
            market_ids=market_ids,
            start_date=self.config.start_date,
            end_date=self.config.end_date
        )

        weather_data = self.data_loader.load_weather_data(
            locations=locations,
            start_date=self.config.start_date,
            end_date=self.config.end_date
        )

        if market_data.empty or weather_data.empty:
            raise ValueError("Insufficient data for backtesting period")

        # Align data timelines
        market_data, weather_data = self.data_loader.align_data_timeline(
            market_data, weather_data, self.config.data_frequency
        )

        # Initialize simulation state
        capital = self.config.initial_capital
        equity_curve = [(self.config.start_date, capital)]
        all_signals = []
        all_positions = []

        # Process data in chronological order
        timeline = self._create_simulation_timeline(market_data, weather_data)

        for timestamp in timeline:
            # Get data for this timestamp
            current_market = market_data[market_data['timestamp'] == timestamp]
            current_weather = weather_data[weather_data['timestamp'] == timestamp]

            if current_market.empty and current_weather.empty:
                continue

            # Get current positions
            current_positions = [p for p in all_positions if p.status == 'OPEN']

            # Generate signals
            signals = strategy.generate_signals(
                current_market if not current_market.empty else pd.DataFrame(),
                current_weather if not current_weather.empty else pd.DataFrame(),
                current_positions
            )

            # Execute signals and update positions
            if signals:
                updated_positions = strategy.update_positions(signals, current_market)
                all_signals.extend(signals)

                # Update capital based on closed positions
                capital_change = sum(p.pnl for p in updated_positions
                                   if p.status == 'CLOSED' and p not in current_positions)
                capital += capital_change

                # Update position list
                all_positions = updated_positions

            # Record equity curve
            equity_curve.append((timestamp, capital))

        # Calculate final results
        result = self._calculate_results(strategy, all_positions, all_signals, equity_curve)
        self.logger.info(f"Backtest completed. Final capital: ${capital:.2f}")

        return result

    def run_multiple_strategies(self,
                               strategies: List[BaseWeatherStrategy],
                               market_ids: Optional[List[str]] = None,
                               locations: Optional[List[str]] = None) -> List[BacktestResult]:
        """
        Run backtests for multiple strategies

        Args:
            strategies: List of strategies to test
            market_ids: Market IDs to test
            locations: Weather locations to use

        Returns:
            List of BacktestResult objects
        """
        results = []

        if self.config.enable_parallel and len(strategies) > 1:
            # Run in parallel
            with ThreadPoolExecutor(max_workers=min(len(strategies), 4)) as executor:
                futures = [
                    executor.submit(self.run_backtest, strategy, market_ids, locations)
                    for strategy in strategies
                ]

                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        self.logger.error(f"Strategy backtest failed: {e}")
        else:
            # Run sequentially
            for strategy in strategies:
                try:
                    result = self.run_backtest(strategy, market_ids, locations)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Strategy {strategy.name} backtest failed: {e}")

        return results

    def _create_simulation_timeline(self,
                                   market_data: pd.DataFrame,
                                   weather_data: pd.DataFrame) -> List[datetime]:
        """Create chronological timeline for simulation"""
        all_timestamps = set()

        if not market_data.empty:
            all_timestamps.update(market_data['timestamp'].tolist())

        if not weather_data.empty:
            all_timestamps.update(weather_data['timestamp'].tolist())

        return sorted(list(all_timestamps))

    def _calculate_results(self,
                          strategy: BaseWeatherStrategy,
                          positions: List[Position],
                          signals: List[TradingSignal],
                          equity_curve: List[Tuple[datetime, float]]) -> BacktestResult:
        """Calculate comprehensive backtest results"""
        # Extract equity values and timestamps
        timestamps, equity_values = zip(*equity_curve)

        # Calculate basic returns
        initial_value = equity_values[0]
        final_value = equity_values[-1]
        total_return = (final_value - initial_value) / initial_value

        # Calculate time-weighted metrics
        days = (self.config.end_date - self.config.start_date).days
        annualized_return = (1 + total_return) ** (365 / max(days, 1)) - 1

        # Calculate volatility (daily returns)
        equity_series = pd.Series(equity_values, index=timestamps)
        daily_returns = equity_series.pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252)  # Annualized

        # Calculate Sharpe ratio
        excess_returns = daily_returns - self.config.risk_free_rate / 252
        sharpe_ratio = excess_returns.mean() / excess_returns.std() if excess_returns.std() > 0 else 0

        # Calculate drawdown
        cumulative = (1 + daily_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # Calculate trading metrics
        closed_positions = [p for p in positions if p.status == 'CLOSED']
        winning_trades = [p for p in closed_positions if p.pnl > 0]
        win_rate = len(winning_trades) / len(closed_positions) if closed_positions else 0

        # Additional metrics
        additional_metrics = {
            'total_trades': len(closed_positions),
            'avg_trade_pnl': np.mean([p.pnl for p in closed_positions]) if closed_positions else 0,
            'avg_win': np.mean([p.pnl for p in winning_trades]) if winning_trades else 0,
            'avg_loss': np.mean([p.pnl for p in closed_positions if p.pnl <= 0]) if closed_positions else 0,
            'profit_factor': (sum(p.pnl for p in winning_trades) /
                            abs(sum(p.pnl for p in closed_positions if p.pnl < 0)))
                            if closed_positions and any(p.pnl < 0 for p in closed_positions) else float('inf'),
            'calmar_ratio': annualized_return / abs(max_drawdown) if max_drawdown != 0 else float('inf'),
            'sortino_ratio': self._calculate_sortino_ratio(daily_returns, self.config.risk_free_rate),
        }

        return BacktestResult(
            strategy_name=strategy.name,
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=len(closed_positions),
            positions=positions,
            signals=signals,
            equity_curve=equity_curve,
            metrics=additional_metrics
        )

    def _calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float) -> float:
        """Calculate Sortino ratio (downside deviation only)"""
        excess_returns = returns - risk_free_rate / 252
        downside_returns = excess_returns[excess_returns < 0]

        if len(downside_returns) == 0:
            return float('inf')

        downside_deviation = downside_returns.std() * np.sqrt(252)
        return excess_returns.mean() / downside_deviation if downside_deviation > 0 else float('inf')

    def validate_backtest_data(self,
                              market_data: pd.DataFrame,
                              weather_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate data quality for backtesting

        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'market_data_points': len(market_data),
            'weather_data_points': len(weather_data),
            'market_date_range': None,
            'weather_date_range': None,
            'missing_data_warnings': [],
            'data_quality_score': 0.0
        }

        if not market_data.empty:
            validation_results['market_date_range'] = (
                market_data['timestamp'].min(),
                market_data['timestamp'].max()
            )

        if not weather_data.empty:
            validation_results['weather_date_range'] = (
                weather_data['timestamp'].min(),
                weather_data['timestamp'].max()
            )

        # Check for data gaps
        if not market_data.empty:
            market_gaps = self._check_data_gaps(market_data, 'timestamp')
            if market_gaps:
                validation_results['missing_data_warnings'].append(
                    f"Market data gaps: {len(market_gaps)} periods"
                )

        if not weather_data.empty:
            weather_gaps = self._check_data_gaps(weather_data, 'timestamp')
            if weather_gaps:
                validation_results['missing_data_warnings'].append(
                    f"Weather data gaps: {len(weather_gaps)} periods"
                )

        # Calculate data quality score
        quality_score = 1.0
        if validation_results['missing_data_warnings']:
            quality_score -= 0.2 * len(validation_results['missing_data_warnings'])

        if len(market_data) < 100:
            quality_score -= 0.3

        if len(weather_data) < 100:
            quality_score -= 0.3

        validation_results['data_quality_score'] = max(0.0, quality_score)

        return validation_results

    def _check_data_gaps(self, df: pd.DataFrame, time_col: str) -> List[Tuple[datetime, datetime]]:
        """Check for gaps in time series data"""
        if df.empty:
            return []

        df = df.sort_values(time_col)
        timestamps = df[time_col].tolist()

        gaps = []
        for i in range(1, len(timestamps)):
            gap = timestamps[i] - timestamps[i-1]
            if gap > timedelta(hours=2):  # More than 2 hours gap
                gaps.append((timestamps[i-1], timestamps[i]))

        return gaps