#!/usr/bin/env python3
"""
Risk Metrics for Backtesting

Calculates various risk measures including Value at Risk (VaR),
Expected Shortfall (ES), stress testing, and risk-adjusted returns.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from scipy import stats
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RiskReport:
    """Comprehensive risk report"""
    value_at_risk_95: float
    value_at_risk_99: float
    expected_shortfall_95: float
    expected_shortfall_99: float
    maximum_drawdown: float
    ulcer_index: float
    volatility: float
    downside_volatility: float
    beta: float
    var_cvar_ratio: float
    stress_test_results: Dict[str, float]
    risk_adjusted_metrics: Dict[str, float]


class RiskMetrics:
    """
    Calculates comprehensive risk metrics for trading strategies

    Provides Value at Risk, Expected Shortfall, stress testing,
    and other risk measures for portfolio analysis.
    """

    def __init__(self, confidence_levels: List[float] = None):
        self.confidence_levels = confidence_levels or [0.95, 0.99]
        self.risk_free_rate = 0.02  # 2% annual risk-free rate

    def calculate_comprehensive_risk(self,
                                   returns: pd.Series,
                                   portfolio_values: pd.Series = None,
                                   benchmark_returns: pd.Series = None) -> RiskReport:
        """
        Calculate comprehensive risk metrics

        Args:
            returns: Series of portfolio returns
            portfolio_values: Series of portfolio values (for drawdown calculations)
            benchmark_returns: Series of benchmark returns (for beta calculation)

        Returns:
            RiskReport with all calculated risk metrics
        """
        if returns.empty:
            return self._empty_risk_report()

        # Value at Risk calculations
        var_95 = self.calculate_value_at_risk(returns, confidence_level=0.95)
        var_99 = self.calculate_value_at_risk(returns, confidence_level=0.99)

        # Expected Shortfall calculations
        es_95 = self.calculate_expected_shortfall(returns, confidence_level=0.95)
        es_99 = self.calculate_expected_shortfall(returns, confidence_level=0.99)

        # Drawdown analysis
        max_drawdown = self.calculate_maximum_drawdown(portfolio_values or self._returns_to_values(returns))

        # Volatility measures
        volatility = self.calculate_volatility(returns)
        downside_volatility = self.calculate_downside_volatility(returns)

        # Ulcer Index
        ulcer_index = self.calculate_ulcer_index(portfolio_values or self._returns_to_values(returns))

        # Beta calculation
        beta = self.calculate_beta(returns, benchmark_returns) if benchmark_returns is not None else 0.0

        # VaR/CVaR ratio
        var_cvar_ratio = abs(var_95) / abs(es_95) if es_95 != 0 else float('inf')

        # Stress testing
        stress_test_results = self.perform_stress_tests(returns)

        # Risk-adjusted metrics
        risk_adjusted_metrics = self.calculate_risk_adjusted_metrics(returns, volatility, max_drawdown)

        return RiskReport(
            value_at_risk_95=var_95,
            value_at_risk_99=var_99,
            expected_shortfall_95=es_95,
            expected_shortfall_99=es_99,
            maximum_drawdown=max_drawdown,
            ulcer_index=ulcer_index,
            volatility=volatility,
            downside_volatility=downside_volatility,
            beta=beta,
            var_cvar_ratio=var_cvar_ratio,
            stress_test_results=stress_test_results,
            risk_adjusted_metrics=risk_adjusted_metrics
        )

    def calculate_value_at_risk(self,
                              returns: pd.Series,
                              confidence_level: float = 0.95,
                              method: str = 'historical') -> float:
        """
        Calculate Value at Risk (VaR)

        Args:
            returns: Series of returns
            confidence_level: Confidence level (e.g., 0.95 for 95% VaR)
            method: Calculation method ('historical', 'parametric', 'monte_carlo')

        Returns:
            Value at Risk as a negative percentage
        """
        if returns.empty:
            return 0.0

        if method == 'historical':
            return -np.percentile(returns, (1 - confidence_level) * 100)
        elif method == 'parametric':
            # Assume normal distribution
            mean = returns.mean()
            std = returns.std()
            z_score = stats.norm.ppf(1 - confidence_level)
            return -(mean + z_score * std)
        elif method == 'monte_carlo':
            # Simple Monte Carlo simulation
            n_simulations = 10000
            simulated_returns = np.random.normal(returns.mean(), returns.std(), n_simulations)
            return -np.percentile(simulated_returns, (1 - confidence_level) * 100)
        else:
            raise ValueError(f"Unknown VaR method: {method}")

    def calculate_expected_shortfall(self,
                                   returns: pd.Series,
                                   confidence_level: float = 0.95) -> float:
        """
        Calculate Expected Shortfall (Conditional VaR)

        Args:
            returns: Series of returns
            confidence_level: Confidence level

        Returns:
            Expected Shortfall as a negative percentage
        """
        if returns.empty:
            return 0.0

        var_threshold = np.percentile(returns, (1 - confidence_level) * 100)
        tail_losses = returns[returns <= var_threshold]

        if len(tail_losses) == 0:
            return -var_threshold

        return -tail_losses.mean()

    def calculate_maximum_drawdown(self, portfolio_values: pd.Series) -> float:
        """
        Calculate Maximum Drawdown

        Args:
            portfolio_values: Series of portfolio values

        Returns:
            Maximum drawdown as a positive percentage
        """
        if portfolio_values.empty:
            return 0.0

        cumulative = portfolio_values / portfolio_values.iloc[0]
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return abs(drawdown.min())

    def calculate_volatility(self, returns: pd.Series, annualize: bool = True) -> float:
        """
        Calculate portfolio volatility

        Args:
            returns: Series of returns
            annualize: Whether to annualize the volatility

        Returns:
            Volatility as a percentage
        """
        if returns.empty:
            return 0.0

        daily_vol = returns.std()
        return daily_vol * np.sqrt(252) if annualize else daily_vol

    def calculate_downside_volatility(self, returns: pd.Series, annualize: bool = True) -> float:
        """
        Calculate downside volatility (semi-deviation)

        Args:
            returns: Series of returns
            annualize: Whether to annualize the volatility

        Returns:
            Downside volatility as a percentage
        """
        if returns.empty:
            return 0.0

        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return 0.0

        daily_vol = downside_returns.std()
        return daily_vol * np.sqrt(252) if annualize else daily_vol

    def calculate_ulcer_index(self, portfolio_values: pd.Series) -> float:
        """
        Calculate Ulcer Index (measure of downside risk)

        Args:
            portfolio_values: Series of portfolio values

        Returns:
            Ulcer Index
        """
        if portfolio_values.empty:
            return 0.0

        # Calculate drawdowns
        cumulative = portfolio_values / portfolio_values.iloc[0]
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max

        # Ulcer Index = sqrt(mean of squared drawdowns)
        return np.sqrt(np.mean(drawdown ** 2))

    def calculate_beta(self, portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """
        Calculate portfolio beta relative to benchmark

        Args:
            portfolio_returns: Series of portfolio returns
            benchmark_returns: Series of benchmark returns

        Returns:
            Beta coefficient
        """
        if portfolio_returns.empty or benchmark_returns.empty:
            return 1.0

        # Align the series
        combined = pd.concat([portfolio_returns, benchmark_returns], axis=1, join='inner')
        combined.columns = ['portfolio', 'benchmark']

        if len(combined) < 2:
            return 1.0

        covariance = combined.cov().iloc[0, 1]
        benchmark_variance = combined['benchmark'].var()

        return covariance / benchmark_variance if benchmark_variance != 0 else 1.0

    def perform_stress_tests(self, returns: pd.Series) -> Dict[str, float]:
        """
        Perform stress tests on the return series

        Args:
            returns: Series of returns

        Returns:
            Dictionary of stress test results
        """
        if returns.empty:
            return {}

        stress_tests = {}

        # Historical scenarios
        stress_tests['black_monday_1987'] = self._simulate_historical_scenario(returns, -0.22)  # -22%
        stress_tests['dot_com_crash'] = self._simulate_historical_scenario(returns, -0.15)    # -15%
        stress_tests['financial_crisis_2008'] = self._simulate_historical_scenario(returns, -0.10)  # -10%
        stress_tests['covid_2020'] = self._simulate_historical_scenario(returns, -0.12)       # -12%

        # Extreme scenarios
        stress_tests['extreme_bear_market'] = self._simulate_historical_scenario(returns, -0.30)  # -30%
        stress_tests['flash_crash'] = self._simulate_historical_scenario(returns, -0.15)         # -15%

        # Recovery analysis
        stress_tests['recovery_time_10pct'] = self._calculate_recovery_time(returns, -0.10)
        stress_tests['recovery_time_20pct'] = self._calculate_recovery_time(returns, -0.20)

        return stress_tests

    def _simulate_historical_scenario(self, returns: pd.Series, shock_return: float) -> float:
        """Simulate the impact of a historical shock"""
        if returns.empty:
            return 0.0

        # Calculate portfolio impact of a sudden shock
        portfolio_value = 10000  # Assume $10,000 portfolio
        shocked_value = portfolio_value * (1 + shock_return)

        # Estimate recovery based on historical volatility
        vol = returns.std()
        expected_recovery_days = abs(shock_return) / (vol * 2)  # Rough estimate

        return shocked_value

    def _calculate_recovery_time(self, returns: pd.Series, drawdown_threshold: float) -> float:
        """Calculate expected recovery time for a given drawdown"""
        if returns.empty:
            return 0.0

        # Simple recovery time estimation based on volatility
        vol = returns.std()
        if vol == 0:
            return 0.0

        return abs(drawdown_threshold) / vol

    def calculate_risk_adjusted_metrics(self,
                                       returns: pd.Series,
                                       volatility: float,
                                       max_drawdown: float) -> Dict[str, float]:
        """
        Calculate risk-adjusted performance metrics

        Args:
            returns: Series of returns
            volatility: Portfolio volatility
            max_drawdown: Maximum drawdown

        Returns:
            Dictionary of risk-adjusted metrics
        """
        if returns.empty:
            return {}

        metrics = {}

        # Sharpe Ratio
        excess_returns = returns - self.risk_free_rate / 252
        metrics['sharpe_ratio'] = excess_returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0

        # Sortino Ratio
        downside_returns = returns[returns < 0]
        downside_vol = downside_returns.std() if len(downside_returns) > 0 else 0
        metrics['sortino_ratio'] = (excess_returns.mean() / downside_vol * np.sqrt(252)
                                   if downside_vol > 0 else float('inf'))

        # Calmar Ratio
        annual_return = (1 + returns.mean()) ** 252 - 1
        metrics['calmar_ratio'] = annual_return / max_drawdown if max_drawdown > 0 else float('inf')

        # Information Ratio (assuming benchmark is risk-free rate)
        tracking_error = returns.std()
        metrics['information_ratio'] = excess_returns.mean() / tracking_error if tracking_error > 0 else 0

        return metrics

    def _returns_to_values(self, returns: pd.Series, initial_value: float = 10000) -> pd.Series:
        """Convert returns series to portfolio values"""
        if returns.empty:
            return pd.Series()

        cumulative_returns = (1 + returns).cumprod()
        return initial_value * cumulative_returns

    def _empty_risk_report(self) -> RiskReport:
        """Return empty risk report"""
        return RiskReport(
            value_at_risk_95=0.0,
            value_at_risk_99=0.0,
            expected_shortfall_95=0.0,
            expected_shortfall_99=0.0,
            maximum_drawdown=0.0,
            ulcer_index=0.0,
            volatility=0.0,
            downside_volatility=0.0,
            beta=0.0,
            var_cvar_ratio=0.0,
            stress_test_results={},
            risk_adjusted_metrics={}
        )

    def generate_risk_summary(self, report: RiskReport) -> str:
        """Generate human-readable risk summary"""
        summary = f"""
RISK ANALYSIS SUMMARY
=====================

Value at Risk (VaR):
  95% Confidence: {report.value_at_risk_95:.2%}
  99% Confidence: {report.value_at_risk_99:.2%}

Expected Shortfall (ES/CVaR):
  95% Confidence: {report.expected_shortfall_95:.2%}
  99% Confidence: {report.expected_shortfall_99:.2%}

Drawdown Analysis:
  Maximum Drawdown: {report.maximum_drawdown:.2%}
  Ulcer Index: {report.ulcer_index:.4f}

Volatility Measures:
  Total Volatility: {report.volatility:.2%}
  Downside Volatility: {report.downside_volatility:.2%}

Risk-Adjusted Metrics:
  Sharpe Ratio: {report.risk_adjusted_metrics.get('sharpe_ratio', 0):.2f}
  Sortino Ratio: {report.risk_adjusted_metrics.get('sortino_ratio', 0):.2f}
  Calmar Ratio: {report.risk_adjusted_metrics.get('calmar_ratio', 0):.2f}

Stress Test Results:
"""

        for test_name, result in report.stress_test_results.items():
            summary += f"  {test_name.replace('_', ' ').title()}: ${result:.2f}\n"

        return summary