#!/usr/bin/env python3
"""
Enhanced Data Validation Module

This module extends the existing data validation framework with advanced features:
- Real-time validation for streaming data
- Cross-source consistency checks
- Automated quality alerting
- Performance monitoring and metrics
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable, AsyncGenerator
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
import time
from collections import defaultdict, deque
import statistics
import json

from .data_validation import DataValidator, PolymarketDataValidator, WeatherDataValidator

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class DataSource(Enum):
    """Data source types."""
    WEATHER = "weather"
    POLYMARKET = "polymarket"
    EXTERNAL = "external"


@dataclass
class ValidationAlert:
    """Data validation alert structure."""
    alert_id: str
    level: AlertLevel
    source: DataSource
    message: str
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class ConsistencyCheck:
    """Cross-source consistency check result."""
    check_id: str
    sources: List[str]
    metric: str
    expected_range: tuple
    actual_values: Dict[str, float]
    is_consistent: bool
    deviation_threshold: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ValidationMetrics:
    """Validation performance metrics."""
    total_validations: int = 0
    successful_validations: int = 0
    failed_validations: int = 0
    average_validation_time: float = 0.0
    validation_times: deque = field(default_factory=lambda: deque(maxlen=1000))
    error_counts: Dict[str, int] = field(default_factory=dict)
    alert_counts: Dict[str, int] = field(default_factory=dict)


class AlertManager:
    """Manages validation alerts and notifications."""

    def __init__(self):
        self.alerts: List[ValidationAlert] = []
        self.alert_handlers: List[Callable] = []
        self.active_alerts: Dict[str, ValidationAlert] = {}

    def add_alert_handler(self, handler: Callable):
        """Add an alert notification handler."""
        self.alert_handlers.append(handler)

    def raise_alert(self, alert: ValidationAlert):
        """Raise a new validation alert."""
        self.alerts.append(alert)
        self.active_alerts[alert.alert_id] = alert

        # Notify all handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")

        logger.log(
            logging.WARNING if alert.level == AlertLevel.WARNING else logging.ERROR,
            f"Validation Alert [{alert.level.value}]: {alert.message}"
        )

    def resolve_alert(self, alert_id: str, resolution_note: str = ""):
        """Resolve an active alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now(timezone.utc)
            alert.details["resolution_note"] = resolution_note

            logger.info(f"Alert resolved: {alert_id}")

    def get_active_alerts(self, level: Optional[AlertLevel] = None) -> List[ValidationAlert]:
        """Get active alerts, optionally filtered by level."""
        alerts = [a for a in self.active_alerts.values() if not a.resolved]
        if level:
            alerts = [a for a in alerts if a.level == level]
        return alerts

    def get_alert_history(self, hours: int = 24) -> List[ValidationAlert]:
        """Get alert history for the specified time period."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [a for a in self.alerts if a.timestamp >= cutoff]


class CrossSourceConsistencyChecker:
    """Checks data consistency across multiple sources."""

    def __init__(self):
        self.consistency_checks: List[ConsistencyCheck] = []
        self.source_data_cache: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

    def add_source_data(self, source: str, data: Dict, timestamp: datetime):
        """Add data from a source for consistency checking."""
        self.source_data_cache[source].append({
            'data': data,
            'timestamp': timestamp
        })

    def check_weather_consistency(self, sources: List[str], location: str,
                                time_window_minutes: int = 30) -> List[ConsistencyCheck]:
        """Check weather data consistency across sources."""
        checks = []

        # Get recent data for each source
        recent_data = {}
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)

        for source in sources:
            source_data = [
                item for item in self.source_data_cache[source]
                if item['timestamp'] >= cutoff and
                item['data'].get('location_name') == location
            ]
            if source_data:
                recent_data[source] = source_data[-1]['data']  # Most recent

        if len(recent_data) < 2:
            return checks  # Need at least 2 sources for consistency check

        # Temperature consistency check
        temp_values = {}
        for source, data in recent_data.items():
            if 'temperature' in data and data['temperature'] is not None:
                temp_values[source] = data['temperature']

        if len(temp_values) >= 2:
            check = self._perform_consistency_check(
                sources=list(temp_values.keys()),
                metric="temperature",
                values=temp_values,
                expected_deviation=2.0  # 2°C tolerance
            )
            checks.append(check)

        # Humidity consistency check
        humidity_values = {}
        for source, data in recent_data.items():
            if 'humidity' in data and data['humidity'] is not None:
                humidity_values[source] = data['humidity']

        if len(humidity_values) >= 2:
            check = self._perform_consistency_check(
                sources=list(humidity_values.keys()),
                metric="humidity",
                values=humidity_values,
                expected_deviation=10.0  # 10% tolerance
            )
            checks.append(check)

        return checks

    def check_market_consistency(self, sources: List[str], market_id: str,
                               time_window_minutes: int = 5) -> List[ConsistencyCheck]:
        """Check market data consistency across sources."""
        checks = []

        # Get recent data for each source
        recent_data = {}
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)

        for source in sources:
            source_data = [
                item for item in self.source_data_cache[source]
                if item['timestamp'] >= cutoff and
                item['data'].get('market_id') == market_id
            ]
            if source_data:
                recent_data[source] = source_data[-1]['data']

        if len(recent_data) < 2:
            return checks

        # Probability consistency check
        prob_values = {}
        for source, data in recent_data.items():
            if 'probability' in data and data['probability'] is not None:
                prob_values[source] = data['probability']

        if len(prob_values) >= 2:
            check = self._perform_consistency_check(
                sources=list(prob_values.keys()),
                metric="probability",
                values=prob_values,
                expected_deviation=0.05  # 5% tolerance
            )
            checks.append(check)

        return checks

    def _perform_consistency_check(self, sources: List[str], metric: str,
                                 values: Dict[str, float], expected_deviation: float) -> ConsistencyCheck:
        """Perform consistency check on a set of values."""
        check_id = f"{metric}_{'_'.join(sources)}_{int(time.time())}"

        if len(values) < 2:
            return ConsistencyCheck(
                check_id=check_id,
                sources=sources,
                metric=metric,
                expected_range=(0, 0),
                actual_values=values,
                is_consistent=True,
                deviation_threshold=expected_deviation
            )

        # Calculate statistics
        value_list = list(values.values())
        mean_val = statistics.mean(value_list)
        max_val = max(value_list)
        min_val = min(value_list)
        max_deviation = max_val - min_val

        is_consistent = max_deviation <= expected_deviation

        return ConsistencyCheck(
            check_id=check_id,
            sources=sources,
            metric=metric,
            expected_range=(mean_val - expected_deviation, mean_val + expected_deviation),
            actual_values=values,
            is_consistent=is_consistent,
            deviation_threshold=expected_deviation
        )


class RealTimeValidator:
    """Real-time validator for streaming data."""

    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
        self.consistency_checker = CrossSourceConsistencyChecker()
        self.metrics = ValidationMetrics()
        self.is_running = False
        self.validation_thread: Optional[threading.Thread] = None

    async def validate_stream(self, data_stream: AsyncGenerator[Dict, None],
                            source: DataSource, validator: DataValidator) -> AsyncGenerator[Dict, None]:
        """Validate data from an async stream."""
        async for data_item in data_stream:
            start_time = time.time()

            try:
                # Perform validation
                if source == DataSource.WEATHER:
                    is_valid = validator.validate_record(data_item)
                elif source == DataSource.POLYMARKET:
                    is_valid = validator.validate_record(data_item)
                else:
                    is_valid = True  # Default for unknown sources

                # Update metrics
                self.metrics.total_validations += 1
                validation_time = time.time() - start_time
                self.metrics.validation_times.append(validation_time)

                if is_valid:
                    self.metrics.successful_validations += 1
                else:
                    self.metrics.failed_validations += 1
                    # Raise alert for validation failure
                    alert = ValidationAlert(
                        alert_id=f"validation_failure_{int(time.time())}_{self.metrics.total_validations}",
                        level=AlertLevel.WARNING,
                        source=source,
                        message=f"Data validation failed for {source.value} record",
                        details={
                            'errors': validator.validation_errors,
                            'warnings': validator.validation_warnings,
                            'data_sample': str(data_item)[:200] + '...' if len(str(data_item)) > 200 else str(data_item)
                        }
                    )
                    self.alert_manager.raise_alert(alert)

                # Add to consistency checker
                timestamp = datetime.now(timezone.utc)
                if 'timestamp' in data_item:
                    try:
                        timestamp = datetime.fromisoformat(data_item['timestamp'].replace('Z', '+00:00'))
                    except:
                        pass

                self.consistency_checker.add_source_data(source.value, data_item, timestamp)

                # Yield validated data with metadata
                validated_item = {
                    **data_item,
                    '_validation': {
                        'is_valid': is_valid,
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'errors': validator.validation_errors,
                        'warnings': validator.validation_warnings
                    }
                }

                yield validated_item

            except Exception as e:
                logger.error(f"Real-time validation error: {e}")
                self.metrics.failed_validations += 1

                # Yield data with error metadata
                yield {
                    **data_item,
                    '_validation': {
                        'is_valid': False,
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'errors': [str(e)],
                        'warnings': []
                    }
                }

    def start_periodic_consistency_checks(self, interval_seconds: int = 300):
        """Start periodic consistency checks."""
        if self.is_running:
            return

        self.is_running = True
        self.validation_thread = threading.Thread(
            target=self._run_consistency_checks,
            args=(interval_seconds,),
            daemon=True
        )
        self.validation_thread.start()

    def stop_periodic_checks(self):
        """Stop periodic consistency checks."""
        self.is_running = False
        if self.validation_thread:
            self.validation_thread.join(timeout=5)

    def _run_consistency_checks(self, interval_seconds: int):
        """Run periodic consistency checks in background thread."""
        while self.is_running:
            try:
                self._perform_consistency_checks()
            except Exception as e:
                logger.error(f"Consistency check error: {e}")

            time.sleep(interval_seconds)

    def _perform_consistency_checks(self):
        """Perform cross-source consistency checks."""
        # Weather consistency checks
        weather_sources = ["meteostat", "openweather", "weather_gov"]
        locations = ["London", "New York", "Tokyo"]  # Example locations

        for location in locations:
            checks = self.consistency_checker.check_weather_consistency(weather_sources, location)
            for check in checks:
                if not check.is_consistent:
                    alert = ValidationAlert(
                        alert_id=f"consistency_{check.check_id}",
                        level=AlertLevel.WARNING,
                        source=DataSource.WEATHER,
                        message=f"Weather data inconsistency detected for {location}",
                        details={
                            'check': check.__dict__,
                            'location': location
                        }
                    )
                    self.alert_manager.raise_alert(alert)

        # Market consistency checks
        market_sources = ["polymarket", "kalshi"]
        market_ids = ["0x123", "0x456"]  # Example market IDs

        for market_id in market_ids:
            checks = self.consistency_checker.check_market_consistency(market_sources, market_id)
            for check in checks:
                if not check.is_consistent:
                    alert = ValidationAlert(
                        alert_id=f"consistency_{check.check_id}",
                        level=AlertLevel.WARNING,
                        source=DataSource.POLYMARKET,
                        message=f"Market data inconsistency detected for {market_id}",
                        details={
                            'check': check.__dict__,
                            'market_id': market_id
                        }
                    )
                    self.alert_manager.raise_alert(alert)

    def get_metrics(self) -> Dict:
        """Get validation metrics."""
        if self.metrics.validation_times:
            self.metrics.average_validation_time = statistics.mean(self.metrics.validation_times)

        return {
            'total_validations': self.metrics.total_validations,
            'successful_validations': self.metrics.successful_validations,
            'failed_validations': self.metrics.failed_validations,
            'success_rate': (self.metrics.successful_validations / self.metrics.total_validations * 100)
                           if self.metrics.total_validations > 0 else 0,
            'average_validation_time': self.metrics.average_validation_time,
            'error_counts': dict(self.metrics.error_counts),
            'alert_counts': dict(self.metrics.alert_counts)
        }


class EnhancedWeatherValidator(WeatherDataValidator):
    """Enhanced weather validator with real-time and consistency features."""

    def __init__(self, alert_manager: Optional[AlertManager] = None):
        super().__init__()
        self.alert_manager = alert_manager or AlertManager()
        self.recent_readings: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

    def validate_record(self, record: Dict) -> bool:
        """Enhanced validation with alerting and trend analysis."""
        is_valid = super().validate_record(record)

        if not is_valid and self.alert_manager:
            # Check for patterns in validation failures
            location = record.get('location_name', 'unknown')
            error_types = [err.split(':')[0] for err in self.validation_errors]

            for error_type in error_types:
                if error_type not in self.alert_manager.active_alerts:
                    alert = ValidationAlert(
                        alert_id=f"weather_validation_{error_type}_{location}",
                        level=AlertLevel.WARNING,
                        source=DataSource.WEATHER,
                        message=f"Recurring weather validation error: {error_type}",
                        details={
                            'location': location,
                            'error_type': error_type,
                            'sample_record': record
                        }
                    )
                    self.alert_manager.raise_alert(alert)

        # Store reading for trend analysis
        location = record.get('location_name', 'unknown')
        self.recent_readings[location].append({
            'timestamp': datetime.now(timezone.utc),
            'temperature': record.get('temperature'),
            'is_valid': is_valid
        })

        return is_valid

    def detect_anomalies(self, location: str) -> List[Dict]:
        """Detect anomalies in weather data for a location."""
        readings = list(self.recent_readings[location])
        if len(readings) < 10:
            return []

        anomalies = []
        temperatures = [r['temperature'] for r in readings if r['temperature'] is not None]

        if len(temperatures) >= 10:
            mean_temp = statistics.mean(temperatures)
            stdev_temp = statistics.stdev(temperatures)

            for i, reading in enumerate(readings[-5:]):  # Check last 5 readings
                if reading['temperature'] is not None:
                    z_score = abs(reading['temperature'] - mean_temp) / stdev_temp
                    if z_score > 3.0:  # 3 standard deviations
                        anomalies.append({
                            'type': 'temperature_anomaly',
                            'value': reading['temperature'],
                            'expected_range': (mean_temp - 2*stdev_temp, mean_temp + 2*stdev_temp),
                            'z_score': z_score,
                            'timestamp': reading['timestamp']
                        })

        return anomalies


class EnhancedPolymarketValidator(PolymarketDataValidator):
    """Enhanced polymarket validator with real-time and consistency features."""

    def __init__(self, alert_manager: Optional[AlertManager] = None):
        super().__init__()
        self.alert_manager = alert_manager or AlertManager()
        self.market_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

    def validate_record(self, record: Dict) -> bool:
        """Enhanced validation with market-specific checks."""
        is_valid = super().validate_record(record)

        market_id = record.get('market_id', 'unknown')

        # Store market data for analysis
        self.market_history[market_id].append({
            'timestamp': datetime.now(timezone.utc),
            'probability': record.get('probability'),
            'volume': record.get('volume'),
            'is_valid': is_valid
        })

        # Check for suspicious probability changes
        if len(self.market_history[market_id]) >= 5:
            recent_probs = [r['probability'] for r in list(self.market_history[market_id])[-5:]
                          if r['probability'] is not None]

            if len(recent_probs) >= 3:
                prob_changes = [abs(recent_probs[i] - recent_probs[i-1])
                              for i in range(1, len(recent_probs))]

                avg_change = statistics.mean(prob_changes)
                if avg_change > 0.3:  # 30% average change in recent readings
                    if self.alert_manager:
                        alert = ValidationAlert(
                            alert_id=f"market_volatility_{market_id}_{int(time.time())}",
                            level=AlertLevel.INFO,
                            source=DataSource.POLYMARKET,
                            message=f"High volatility detected in market {market_id}",
                            details={
                                'market_id': market_id,
                                'average_change': avg_change,
                                'recent_probabilities': recent_probs
                            }
                        )
                        self.alert_manager.raise_alert(alert)

        return is_valid


# Convenience functions
def create_enhanced_weather_validator(alert_manager: Optional[AlertManager] = None) -> EnhancedWeatherValidator:
    """Create an enhanced weather validator."""
    return EnhancedWeatherValidator(alert_manager)


def create_enhanced_polymarket_validator(alert_manager: Optional[AlertManager] = None) -> EnhancedPolymarketValidator:
    """Create an enhanced polymarket validator."""
    return EnhancedPolymarketValidator(alert_manager)


def create_realtime_validator(alert_manager: Optional[AlertManager] = None) -> RealTimeValidator:
    """Create a real-time validator."""
    alert_manager = alert_manager or AlertManager()
    return RealTimeValidator(alert_manager)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Create alert manager
    alert_manager = AlertManager()

    # Create validators
    weather_validator = create_enhanced_weather_validator(alert_manager)
    market_validator = create_enhanced_polymarket_validator(alert_manager)

    # Test weather validation
    weather_record = {
        'location_name': 'London, UK',
        'latitude': 51.5074,
        'longitude': -0.1278,
        'timestamp': '2025-09-04T12:00:00Z',
        'temperature': 18.5,
        'humidity': 72
    }

    is_valid = weather_validator.validate_record(weather_record)
    print(f"Weather record valid: {is_valid}")

    # Test market validation
    market_record = {
        'event_title': 'Will it rain in London tomorrow?',
        'market_id': '0x1234567890abcdef',
        'outcome_name': 'Yes',
        'probability': 0.65,
        'volume': 10000.50,
        'timestamp': '2025-09-04T12:00:00Z',
        'scraped_at': '2025-09-04T12:30:00Z'
    }

    is_valid = market_validator.validate_record(market_record)
    print(f"Market record valid: {is_valid}")

    # Check for active alerts
    active_alerts = alert_manager.get_active_alerts()
    print(f"Active alerts: {len(active_alerts)}")