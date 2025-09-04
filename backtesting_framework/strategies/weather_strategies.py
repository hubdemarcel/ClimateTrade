#!/usr/bin/env python3
"""
Example Weather-Based Trading Strategies

This module contains several example trading strategies that use weather data
to generate trading signals for Polymarket weather-related markets.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .base_strategy import BaseWeatherStrategy, TradingSignal


class TemperatureThresholdStrategy(BaseWeatherStrategy):
    """
    Strategy based on temperature thresholds

    Trades when temperature crosses predefined thresholds that might
    affect weather-dependent markets.
    """

    def __init__(self,
                 name: str = "TemperatureThresholdStrategy",
                 parameters: Optional[Dict[str, Any]] = None):
        super().__init__(name, parameters)

        # Default parameters
        self.hot_threshold = self.parameters.get('hot_threshold', 30.0)  # Celsius
        self.cold_threshold = self.parameters.get('cold_threshold', 0.0)  # Celsius
        self.signal_strength_threshold = self.parameters.get('signal_strength_threshold', 0.6)
        self.lookback_period = self.parameters.get('lookback_period', 24)  # hours

    def generate_signals(self,
                        market_data: pd.DataFrame,
                        weather_data: pd.DataFrame,
                        current_positions: List) -> List[TradingSignal]:
        signals = []

        if weather_data.empty:
            return signals

        # Group weather data by location
        for location, location_data in weather_data.groupby('location_name'):
            if location_data.empty:
                continue

            # Get recent weather data
            recent_weather = location_data.tail(self.lookback_period)

            # Check for temperature anomalies
            current_temp = recent_weather['temperature'].iloc[-1] if not recent_weather.empty else None
            avg_temp = recent_weather['temperature'].mean()
            temp_std = recent_weather['temperature'].std()

            if current_temp is None or temp_std == 0:
                continue

            # Calculate temperature z-score
            temp_zscore = (current_temp - avg_temp) / temp_std

            # Generate signals based on temperature extremes
            if current_temp >= self.hot_threshold and temp_zscore > 1.5:
                signal = self._create_heat_signal(recent_weather, market_data, temp_zscore)
                if signal:
                    signals.append(signal)

            elif current_temp <= self.cold_threshold and temp_zscore < -1.5:
                signal = self._create_cold_signal(recent_weather, market_data, temp_zscore)
                if signal:
                    signals.append(signal)

        return signals

    def _create_heat_signal(self, weather_data: pd.DataFrame, market_data: pd.DataFrame, zscore: float) -> Optional[TradingSignal]:
        """Create signal for heat conditions"""
        confidence = min(1.0, abs(zscore) / 3.0)  # Scale confidence

        if confidence >= self.signal_strength_threshold:
            return TradingSignal(
                timestamp=weather_data['timestamp'].iloc[-1],
                market_id='temperature_market',  # Would need to be mapped to actual market
                outcome_name='above_normal',
                signal_type='BUY',
                confidence=confidence,
                reasoning=f"Extreme heat detected: {weather_data['temperature'].iloc[-1]:.1f}°C (z-score: {zscore:.2f})"
            )

        return None

    def _create_cold_signal(self, weather_data: pd.DataFrame, market_data: pd.DataFrame, zscore: float) -> Optional[TradingSignal]:
        """Create signal for cold conditions"""
        confidence = min(1.0, abs(zscore) / 3.0)

        if confidence >= self.signal_strength_threshold:
            return TradingSignal(
                timestamp=weather_data['timestamp'].iloc[-1],
                market_id='temperature_market',
                outcome_name='below_normal',
                signal_type='BUY',
                confidence=confidence,
                reasoning=f"Extreme cold detected: {weather_data['temperature'].iloc[-1]:.1f}°C (z-score: {zscore:.2f})"
            )

        return None


class PrecipitationStrategy(BaseWeatherStrategy):
    """
    Strategy based on precipitation patterns

    Trades based on rainfall amounts and patterns that might affect
    weather-dependent markets.
    """

    def __init__(self,
                 name: str = "PrecipitationStrategy",
                 parameters: Optional[Dict[str, Any]] = None):
        super().__init__(name, parameters)

        self.rain_threshold = self.parameters.get('rain_threshold', 10.0)  # mm
        self.drought_threshold = self.parameters.get('drought_threshold', 0.1)  # mm
        self.signal_strength_threshold = self.parameters.get('signal_strength_threshold', 0.7)
        self.lookback_period = self.parameters.get('lookback_period', 72)  # hours

    def generate_signals(self,
                        market_data: pd.DataFrame,
                        weather_data: pd.DataFrame,
                        current_positions: List) -> List[TradingSignal]:
        signals = []

        if weather_data.empty:
            return signals

        for location, location_data in weather_data.groupby('location_name'):
            if location_data.empty:
                continue

            recent_weather = location_data.tail(self.lookback_period)

            # Calculate total precipitation over lookback period
            total_rain = recent_weather['precipitation'].sum()
            avg_rain = recent_weather['precipitation'].mean()

            # Check for precipitation extremes
            if total_rain >= self.rain_threshold:
                signal = self._create_rain_signal(recent_weather, market_data, total_rain)
                if signal:
                    signals.append(signal)

            elif total_rain <= self.drought_threshold:
                signal = self._create_drought_signal(recent_weather, market_data, total_rain)
                if signal:
                    signals.append(signal)

        return signals

    def _create_rain_signal(self, weather_data: pd.DataFrame, market_data: pd.DataFrame, total_rain: float) -> Optional[TradingSignal]:
        """Create signal for heavy rain conditions"""
        confidence = min(1.0, total_rain / (self.rain_threshold * 2))

        if confidence >= self.signal_strength_threshold:
            return TradingSignal(
                timestamp=weather_data['timestamp'].iloc[-1],
                market_id='precipitation_market',
                outcome_name='heavy_rain',
                signal_type='BUY',
                confidence=confidence,
                reasoning=f"Heavy precipitation detected: {total_rain:.1f}mm in {len(weather_data)} hours"
            )

        return None

    def _create_drought_signal(self, weather_data: pd.DataFrame, market_data: pd.DataFrame, total_rain: float) -> Optional[TradingSignal]:
        """Create signal for drought conditions"""
        confidence = min(1.0, (self.drought_threshold - total_rain) / self.drought_threshold)

        if confidence >= self.signal_strength_threshold:
            return TradingSignal(
                timestamp=weather_data['timestamp'].iloc[-1],
                market_id='precipitation_market',
                outcome_name='drought',
                signal_type='BUY',
                confidence=confidence,
                reasoning=f"Drought conditions detected: only {total_rain:.1f}mm in {len(weather_data)} hours"
            )

        return None


class WindSpeedStrategy(BaseWeatherStrategy):
    """
    Strategy based on wind speed patterns

    Trades based on wind speed that might affect various weather-dependent markets.
    """

    def __init__(self,
                 name: str = "WindSpeedStrategy",
                 parameters: Optional[Dict[str, Any]] = None):
        super().__init__(name, parameters)

        self.high_wind_threshold = self.parameters.get('high_wind_threshold', 20.0)  # m/s
        self.low_wind_threshold = self.parameters.get('low_wind_threshold', 2.0)   # m/s
        self.signal_strength_threshold = self.parameters.get('signal_strength_threshold', 0.7)
        self.lookback_period = self.parameters.get('lookback_period', 12)  # hours

    def generate_signals(self,
                        market_data: pd.DataFrame,
                        weather_data: pd.DataFrame,
                        current_positions: List) -> List[TradingSignal]:
        signals = []

        if weather_data.empty:
            return signals

        for location, location_data in weather_data.groupby('location_name'):
            if location_data.empty:
                continue

            recent_weather = location_data.tail(self.lookback_period)
            current_wind = recent_weather['wind_speed'].iloc[-1]

            if current_wind >= self.high_wind_threshold:
                signal = self._create_high_wind_signal(recent_weather, market_data, current_wind)
                if signal:
                    signals.append(signal)

            elif current_wind <= self.low_wind_threshold:
                signal = self._create_low_wind_signal(recent_weather, market_data, current_wind)
                if signal:
                    signals.append(signal)

        return signals

    def _create_high_wind_signal(self, weather_data: pd.DataFrame, market_data: pd.DataFrame, wind_speed: float) -> Optional[TradingSignal]:
        """Create signal for high wind conditions"""
        confidence = min(1.0, wind_speed / (self.high_wind_threshold * 1.5))

        if confidence >= self.signal_strength_threshold:
            return TradingSignal(
                timestamp=weather_data['timestamp'].iloc[-1],
                market_id='wind_market',
                outcome_name='high_winds',
                signal_type='BUY',
                confidence=confidence,
                reasoning=f"High wind speeds detected: {wind_speed:.1f} m/s"
            )

        return None

    def _create_low_wind_signal(self, weather_data: pd.DataFrame, market_data: pd.DataFrame, wind_speed: float) -> Optional[TradingSignal]:
        """Create signal for low wind conditions"""
        confidence = min(1.0, (self.low_wind_threshold - wind_speed) / self.low_wind_threshold)

        if confidence >= self.signal_strength_threshold:
            return TradingSignal(
                timestamp=weather_data['timestamp'].iloc[-1],
                market_id='wind_market',
                outcome_name='calm_winds',
                signal_type='BUY',
                confidence=confidence,
                reasoning=f"Calm wind conditions: {wind_speed:.1f} m/s"
            )

        return None


class WeatherPatternStrategy(BaseWeatherStrategy):
    """
    Advanced strategy based on weather pattern recognition

    Uses multiple weather variables and their interactions to generate
    more sophisticated trading signals.
    """

    def __init__(self,
                 name: str = "WeatherPatternStrategy",
                 parameters: Optional[Dict[str, Any]] = None):
        super().__init__(name, parameters)

        self.pattern_lookback = self.parameters.get('pattern_lookback', 168)  # 7 days in hours
        self.correlation_threshold = self.parameters.get('correlation_threshold', 0.7)
        self.signal_strength_threshold = self.parameters.get('signal_strength_threshold', 0.8)

    def generate_signals(self,
                        market_data: pd.DataFrame,
                        weather_data: pd.DataFrame,
                        current_positions: List) -> List[TradingSignal]:
        signals = []

        if weather_data.empty:
            return signals

        for location, location_data in weather_data.groupby('location_name'):
            if len(location_data) < self.pattern_lookback:
                continue

            # Analyze weather patterns
            pattern_signals = self._analyze_weather_patterns(location_data)

            for signal in pattern_signals:
                if signal.confidence >= self.signal_strength_threshold:
                    signals.append(signal)

        return signals

    def _analyze_weather_patterns(self, weather_data: pd.DataFrame) -> List[TradingSignal]:
        """Analyze complex weather patterns for trading signals"""
        signals = []

        # Get recent data
        recent_data = weather_data.tail(self.pattern_lookback)

        # Calculate correlations between weather variables
        temp_humidity_corr = recent_data['temperature'].corr(recent_data['humidity'])
        temp_precip_corr = recent_data['temperature'].corr(recent_data['precipitation'])
        wind_temp_corr = recent_data['wind_speed'].corr(recent_data['temperature'])

        # Pattern 1: Heat wave with low humidity (fire risk)
        if (recent_data['temperature'].mean() > 25 and
            recent_data['humidity'].mean() < 40 and
            abs(temp_humidity_corr) > self.correlation_threshold):

            confidence = min(1.0, (recent_data['temperature'].mean() - 25) / 10 +
                           (40 - recent_data['humidity'].mean()) / 20)

            signals.append(TradingSignal(
                timestamp=recent_data['timestamp'].iloc[-1],
                market_id='weather_pattern_market',
                outcome_name='heat_wave_dry',
                signal_type='BUY',
                confidence=confidence,
                reasoning="Heat wave with dry conditions detected (potential fire risk)"
            ))

        # Pattern 2: Cold front with high winds (storm potential)
        if (recent_data['temperature'].std() > 5 and
            recent_data['wind_speed'].mean() > 15 and
            abs(wind_temp_corr) > self.correlation_threshold):

            confidence = min(1.0, recent_data['temperature'].std() / 10 +
                           recent_data['wind_speed'].mean() / 25)

            signals.append(TradingSignal(
                timestamp=recent_data['timestamp'].iloc[-1],
                market_id='weather_pattern_market',
                outcome_name='storm_front',
                signal_type='BUY',
                confidence=confidence,
                reasoning="Cold front with high winds detected (storm potential)"
            ))

        # Pattern 3: Prolonged dry spell followed by rain (relief signal)
        dry_period = recent_data[recent_data['precipitation'] < 0.1]
        if (len(dry_period) > self.pattern_lookback * 0.7 and
            recent_data['precipitation'].tail(24).sum() > 5):

            confidence = min(1.0, len(dry_period) / self.pattern_lookback +
                           recent_data['precipitation'].tail(24).sum() / 20)

            signals.append(TradingSignal(
                timestamp=recent_data['timestamp'].iloc[-1],
                market_id='weather_pattern_market',
                outcome_name='drought_relief',
                signal_type='BUY',
                confidence=confidence,
                reasoning="Drought relief pattern detected after prolonged dry period"
            ))

        return signals


class SeasonalWeatherStrategy(BaseWeatherStrategy):
    """
    Strategy based on seasonal weather patterns

    Uses historical seasonal patterns to predict and trade weather outcomes.
    """

    def __init__(self,
                 name: str = "SeasonalWeatherStrategy",
                 parameters: Optional[Dict[str, Any]] = None):
        super().__init__(name, parameters)

        self.seasonal_lookback = self.parameters.get('seasonal_lookback', 365 * 24)  # 1 year in hours
        self.deviation_threshold = self.parameters.get('deviation_threshold', 2.0)  # standard deviations
        self.signal_strength_threshold = self.parameters.get('signal_strength_threshold', 0.75)

    def generate_signals(self,
                        market_data: pd.DataFrame,
                        weather_data: pd.DataFrame,
                        current_positions: List) -> List[TradingSignal]:
        signals = []

        if weather_data.empty:
            return signals

        for location, location_data in weather_data.groupby('location_name'):
            if len(location_data) < self.seasonal_lookback:
                continue

            # Analyze seasonal patterns
            seasonal_signals = self._analyze_seasonal_patterns(location_data)

            for signal in seasonal_signals:
                if signal.confidence >= self.signal_strength_threshold:
                    signals.append(signal)

        return signals

    def _analyze_seasonal_patterns(self, weather_data: pd.DataFrame) -> List[TradingSignal]:
        """Analyze seasonal weather patterns"""
        signals = []

        # Get current date and historical data
        current_timestamp = weather_data['timestamp'].iloc[-1]
        current_month = current_timestamp.month
        current_day = current_timestamp.day

        # Get historical data for same period
        historical_data = weather_data[
            (weather_data['timestamp'].dt.month == current_month) &
            (weather_data['timestamp'].dt.day == current_day)
        ]

        if len(historical_data) < 3:  # Need at least 3 years of data
            return signals

        # Calculate seasonal normals
        temp_normal = historical_data['temperature'].mean()
        temp_std = historical_data['temperature'].std()
        precip_normal = historical_data['precipitation'].mean()
        precip_std = historical_data['precipitation'].std()

        # Get current values
        current_temp = weather_data['temperature'].iloc[-1]
        current_precip = weather_data['precipitation'].tail(24).sum()  # Daily total

        # Check for seasonal deviations
        if abs(current_temp - temp_normal) > self.deviation_threshold * temp_std:
            if current_temp > temp_normal:
                confidence = min(1.0, (current_temp - temp_normal) / (3 * temp_std))
                signals.append(TradingSignal(
                    timestamp=current_timestamp,
                    market_id='seasonal_market',
                    outcome_name='warmer_than_seasonal',
                    signal_type='BUY',
                    confidence=confidence,
                    reasoning=f"Temperature {current_temp:.1f}°C is significantly warmer than seasonal normal {temp_normal:.1f}°C"
                ))
            else:
                confidence = min(1.0, (temp_normal - current_temp) / (3 * temp_std))
                signals.append(TradingSignal(
                    timestamp=current_timestamp,
                    market_id='seasonal_market',
                    outcome_name='colder_than_seasonal',
                    signal_type='BUY',
                    confidence=confidence,
                    reasoning=f"Temperature {current_temp:.1f}°C is significantly colder than seasonal normal {temp_normal:.1f}°C"
                ))

        if abs(current_precip - precip_normal) > self.deviation_threshold * precip_std:
            if current_precip > precip_normal:
                confidence = min(1.0, (current_precip - precip_normal) / (3 * precip_std))
                signals.append(TradingSignal(
                    timestamp=current_timestamp,
                    market_id='seasonal_market',
                    outcome_name='wetter_than_seasonal',
                    signal_type='BUY',
                    confidence=confidence,
                    reasoning=f"Precipitation {current_precip:.1f}mm is significantly wetter than seasonal normal {precip_normal:.1f}mm"
                ))

        return signals