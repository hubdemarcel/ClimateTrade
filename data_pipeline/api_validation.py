#!/usr/bin/env python3
"""
API Parameter Validation Module

This module provides comprehensive validation utilities for API parameters,
including REST API inputs, WebSocket messages, and external API responses.
Extends the existing validation framework with API-specific validation patterns.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timezone
import re
import json
from enum import Enum
from dataclasses import dataclass
from urllib.parse import urlparse

from .data_validation import DataValidator

logger = logging.getLogger(__name__)


class APIType(Enum):
    """Enumeration of supported API types."""
    REST = "rest"
    WEBSOCKET = "websocket"
    GRAPHQL = "graphql"
    EXTERNAL = "external"


class ValidationSeverity(Enum):
    """Validation severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    """Structured validation result."""
    field: str
    severity: ValidationSeverity
    message: str
    value: Any = None
    suggestion: Optional[str] = None


class APIParameterValidator(DataValidator):
    """Base validator for API parameters with common validation methods."""

    def __init__(self, api_type: APIType):
        super().__init__()
        self.api_type = api_type
        self.validation_results: List[ValidationResult] = []

    def validate_request(self, request_data: Dict) -> List[ValidationResult]:
        """Validate API request parameters."""
        self.reset_errors()
        self.validation_results = []

        # Common validations
        self._validate_request_structure(request_data)
        self._validate_authentication(request_data)
        self._validate_rate_limits(request_data)

        return self.validation_results

    def validate_response(self, response_data: Dict, expected_schema: Optional[Dict] = None) -> List[ValidationResult]:
        """Validate API response data."""
        self.reset_errors()
        self.validation_results = []

        # Common response validations
        self._validate_response_structure(response_data)
        self._validate_response_schema(response_data, expected_schema)
        self._validate_response_metadata(response_data)

        return self.validation_results

    def _validate_request_structure(self, request_data: Dict):
        """Validate basic request structure."""
        if not isinstance(request_data, dict):
            self._add_result("request", ValidationSeverity.ERROR,
                           "Request must be a valid JSON object", request_data)

    def _validate_authentication(self, request_data: Dict):
        """Validate authentication parameters."""
        # This would be customized based on API authentication requirements
        pass

    def _validate_rate_limits(self, request_data: Dict):
        """Validate rate limiting parameters."""
        # This would check for rate limit headers or parameters
        pass

    def _validate_response_structure(self, response_data: Dict):
        """Validate basic response structure."""
        if not isinstance(response_data, dict):
            self._add_result("response", ValidationSeverity.ERROR,
                           "Response must be a valid JSON object", response_data)

    def _validate_response_schema(self, response_data: Dict, expected_schema: Optional[Dict]):
        """Validate response against expected schema."""
        if expected_schema:
            self._validate_against_schema(response_data, expected_schema, "response")

    def _validate_response_metadata(self, response_data: Dict):
        """Validate response metadata (status, headers, etc.)."""
        # This would validate HTTP status codes, headers, etc.
        pass

    def _validate_against_schema(self, data: Dict, schema: Dict, path: str = ""):
        """Recursively validate data against a schema."""
        for key, rules in schema.items():
            current_path = f"{path}.{key}" if path else key

            if key not in data:
                if rules.get("required", False):
                    self._add_result(current_path, ValidationSeverity.ERROR,
                                   f"Required field '{key}' is missing")
                continue

            value = data[key]
            expected_type = rules.get("type")

            # Type validation
            if expected_type and not self._validate_type(value, expected_type):
                self._add_result(current_path, ValidationSeverity.ERROR,
                               f"Field '{key}' must be of type {expected_type}",
                               value, f"Convert to {expected_type}")

            # Range validation
            if "min" in rules and isinstance(value, (int, float)):
                if value < rules["min"]:
                    self._add_result(current_path, ValidationSeverity.ERROR,
                                   f"Value must be >= {rules['min']}", value)

            if "max" in rules and isinstance(value, (int, float)):
                if value > rules["max"]:
                    self._add_result(current_path, ValidationSeverity.ERROR,
                                   f"Value must be <= {rules['max']}", value)

            # Pattern validation
            if "pattern" in rules and isinstance(value, str):
                if not re.match(rules["pattern"], value):
                    self._add_result(current_path, ValidationSeverity.ERROR,
                                   f"Value does not match required pattern", value)

            # Nested object validation
            if "properties" in rules and isinstance(value, dict):
                self._validate_against_schema(value, rules["properties"], current_path)

            # Array validation
            if "items" in rules and isinstance(value, list):
                item_schema = rules["items"]
                for i, item in enumerate(value):
                    if isinstance(item_schema, dict):
                        self._validate_against_schema({f"item_{i}": item},
                                                    {"item_" + str(i): item_schema},
                                                    f"{current_path}[{i}]")

    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type against expected type string."""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "object": dict,
            "array": list
        }

        if expected_type in type_map:
            return isinstance(value, type_map[expected_type])

        return True  # Unknown type, assume valid

    def _add_result(self, field: str, severity: ValidationSeverity,
                   message: str, value: Any = None, suggestion: Optional[str] = None):
        """Add a validation result."""
        result = ValidationResult(field, severity, message, value, suggestion)
        self.validation_results.append(result)

        # Also add to legacy error/warning lists for compatibility
        if severity == ValidationSeverity.ERROR:
            self.add_error(field, message, value)
        elif severity == ValidationSeverity.WARNING:
            self.add_warning(field, message, value)


class RESTAPIValidator(APIParameterValidator):
    """Validator for REST API parameters."""

    def __init__(self):
        super().__init__(APIType.REST)

    def validate_request(self, request_data: Dict, method: str = "GET",
                        endpoint: str = "", headers: Optional[Dict] = None) -> List[ValidationResult]:
        """Validate REST API request."""
        results = super().validate_request(request_data)

        # Method-specific validation
        self._validate_http_method(method, request_data)
        self._validate_endpoint(endpoint)
        self._validate_headers(headers or {})

        # Content validation based on method
        if method.upper() in ["POST", "PUT", "PATCH"]:
            self._validate_request_body(request_data)
        elif method.upper() in ["GET", "DELETE"]:
            self._validate_query_parameters(request_data)

        return self.validation_results

    def validate_response(self, response_data: Dict, status_code: int = 200,
                         expected_schema: Optional[Dict] = None) -> List[ValidationResult]:
        """Validate REST API response."""
        results = super().validate_response(response_data, expected_schema)

        # HTTP status validation
        self._validate_status_code(status_code, response_data)

        return self.validation_results

    def _validate_http_method(self, method: str, request_data: Dict):
        """Validate HTTP method."""
        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
        if method.upper() not in valid_methods:
            self._add_result("method", ValidationSeverity.ERROR,
                           f"Invalid HTTP method: {method}", method,
                           f"Use one of: {', '.join(valid_methods)}")

    def _validate_endpoint(self, endpoint: str):
        """Validate API endpoint."""
        if not endpoint:
            self._add_result("endpoint", ValidationSeverity.ERROR,
                           "Endpoint is required")
            return

        try:
            parsed = urlparse(endpoint)
            if not parsed.scheme or not parsed.netloc:
                self._add_result("endpoint", ValidationSeverity.ERROR,
                               "Invalid endpoint URL format", endpoint)
        except Exception as e:
            self._add_result("endpoint", ValidationSeverity.ERROR,
                           f"Invalid endpoint URL: {str(e)}", endpoint)

    def _validate_headers(self, headers: Dict):
        """Validate request headers."""
        required_headers = ["Content-Type"]  # Could be configurable

        for header in required_headers:
            if header not in headers:
                self._add_result(f"header.{header}", ValidationSeverity.WARNING,
                               f"Missing recommended header: {header}")

        # Content-Type validation
        content_type = headers.get("Content-Type", "").lower()
        if content_type and "json" not in content_type and "application" not in content_type:
            self._add_result("header.Content-Type", ValidationSeverity.WARNING,
                           "Content-Type should be application/json for API requests",
                           content_type, "Set to 'application/json'")

    def _validate_request_body(self, request_data: Dict):
        """Validate request body for POST/PUT/PATCH."""
        if not request_data:
            self._add_result("body", ValidationSeverity.WARNING,
                           "Request body is empty")

        # Check for common required fields
        if self.api_type == APIType.REST:
            # Add REST-specific body validations here
            pass

    def _validate_query_parameters(self, request_data: Dict):
        """Validate query parameters for GET/DELETE."""
        # Validate parameter types and formats
        for param, value in request_data.items():
            if isinstance(value, str) and len(value) > 1000:
                self._add_result(f"query.{param}", ValidationSeverity.WARNING,
                               "Query parameter value is very long", value)

    def _validate_status_code(self, status_code: int, response_data: Dict):
        """Validate HTTP status code."""
        if not (200 <= status_code < 300):
            severity = ValidationSeverity.ERROR if status_code >= 400 else ValidationSeverity.WARNING
            self._add_result("status_code", severity,
                           f"HTTP status code indicates issue: {status_code}",
                           status_code)


class WebSocketValidator(APIParameterValidator):
    """Validator for WebSocket messages."""

    def __init__(self):
        super().__init__(APIType.WEBSOCKET)

    def validate_message(self, message: Union[str, Dict], message_type: str = "data") -> List[ValidationResult]:
        """Validate WebSocket message."""
        self.reset_errors()
        self.validation_results = []

        # Parse message if string
        if isinstance(message, str):
            try:
                message = json.loads(message)
            except json.JSONDecodeError as e:
                self._add_result("message", ValidationSeverity.ERROR,
                               f"Invalid JSON message: {str(e)}", message)
                return self.validation_results

        if not isinstance(message, dict):
            self._add_result("message", ValidationSeverity.ERROR,
                           "WebSocket message must be a valid JSON object", message)
            return self.validation_results

        # Validate message structure
        self._validate_message_structure(message, message_type)

        # Validate message content
        self._validate_message_content(message, message_type)

        return self.validation_results

    def _validate_message_structure(self, message: Dict, message_type: str):
        """Validate WebSocket message structure."""
        required_fields = ["type", "timestamp"]

        for field in required_fields:
            if field not in message:
                self._add_result(f"message.{field}", ValidationSeverity.ERROR,
                               f"Required field '{field}' is missing in WebSocket message")

        # Validate message type
        if "type" in message and message["type"] != message_type:
            self._add_result("message.type", ValidationSeverity.WARNING,
                           f"Message type mismatch: expected '{message_type}', got '{message['type']}'",
                           message["type"])

    def _validate_message_content(self, message: Dict, message_type: str):
        """Validate WebSocket message content based on type."""
        if message_type == "data":
            # Validate data message content
            if "data" not in message:
                self._add_result("message.data", ValidationSeverity.ERROR,
                               "Data message must contain 'data' field")
            elif not isinstance(message["data"], (dict, list)):
                self._add_result("message.data", ValidationSeverity.ERROR,
                               "Message data must be an object or array", message["data"])

        elif message_type == "subscription":
            # Validate subscription message
            if "channel" not in message:
                self._add_result("message.channel", ValidationSeverity.ERROR,
                               "Subscription message must contain 'channel' field")

        # Validate timestamp
        if "timestamp" in message:
            try:
                datetime.fromisoformat(message["timestamp"].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                self._add_result("message.timestamp", ValidationSeverity.ERROR,
                               "Invalid timestamp format in message", message["timestamp"])


class ExternalAPIValidator(APIParameterValidator):
    """Validator for external API responses."""

    def __init__(self, api_name: str):
        super().__init__(APIType.EXTERNAL)
        self.api_name = api_name

    def validate_response(self, response_data: Dict, expected_schema: Optional[Dict] = None,
                         api_specific_rules: Optional[Dict] = None) -> List[ValidationResult]:
        """Validate external API response."""
        results = super().validate_response(response_data, expected_schema)

        # Apply API-specific validation rules
        if api_specific_rules:
            self._apply_api_specific_rules(response_data, api_specific_rules)

        # Validate common external API patterns
        self._validate_external_api_patterns(response_data)

        return self.validation_results

    def _apply_api_specific_rules(self, response_data: Dict, rules: Dict):
        """Apply API-specific validation rules."""
        for rule_name, rule_config in rules.items():
            validator_func = getattr(self, f"_validate_{rule_name}", None)
            if validator_func:
                validator_func(response_data, rule_config)
            else:
                logger.warning(f"Unknown validation rule: {rule_name}")

    def _validate_external_api_patterns(self, response_data: Dict):
        """Validate common external API response patterns."""
        # Check for error indicators
        if "error" in response_data:
            self._add_result("response.error", ValidationSeverity.ERROR,
                           "API response contains error", response_data["error"])

        if "errors" in response_data and response_data["errors"]:
            self._add_result("response.errors", ValidationSeverity.ERROR,
                           "API response contains errors", response_data["errors"])

        # Validate rate limit headers if present
        # This would be checked in the response metadata

    def _validate_weather_api_response(self, response_data: Dict, config: Dict):
        """Validate weather API specific response."""
        # Weather API specific validations
        if "main" in response_data:
            main_data = response_data["main"]
            if "temp" in main_data and not isinstance(main_data["temp"], (int, float)):
                self._add_result("response.main.temp", ValidationSeverity.ERROR,
                               "Temperature must be numeric", main_data["temp"])

    def _validate_market_api_response(self, response_data: Dict, config: Dict):
        """Validate market data API specific response."""
        # Market API specific validations
        if "markets" in response_data:
            markets = response_data["markets"]
            if isinstance(markets, list):
                for i, market in enumerate(markets):
                    if "id" not in market:
                        self._add_result(f"response.markets[{i}].id", ValidationSeverity.ERROR,
                                       "Market entry missing ID")


# Convenience functions
def validate_rest_request(request_data: Dict, method: str = "GET",
                         endpoint: str = "", headers: Optional[Dict] = None) -> List[ValidationResult]:
    """Convenience function to validate REST API request."""
    validator = RESTAPIValidator()
    return validator.validate_request(request_data, method, endpoint, headers)


def validate_websocket_message(message: Union[str, Dict], message_type: str = "data") -> List[ValidationResult]:
    """Convenience function to validate WebSocket message."""
    validator = WebSocketValidator()
    return validator.validate_message(message, message_type)


def validate_external_api_response(response_data: Dict, api_name: str,
                                 expected_schema: Optional[Dict] = None,
                                 api_specific_rules: Optional[Dict] = None) -> List[ValidationResult]:
    """Convenience function to validate external API response."""
    validator = ExternalAPIValidator(api_name)
    return validator.validate_response(response_data, expected_schema, api_specific_rules)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Test REST API validation
    rest_validator = RESTAPIValidator()
    test_request = {
        "user_id": 123,
        "action": "get_weather",
        "location": "London"
    }

    results = rest_validator.validate_request(test_request, "GET", "/api/weather")
    print(f"REST validation results: {len(results)} issues found")

    # Test WebSocket validation
    ws_validator = WebSocketValidator()
    test_message = {
        "type": "data",
        "timestamp": "2025-09-04T12:00:00Z",
        "data": {"temperature": 20.5}
    }

    results = ws_validator.validate_message(test_message)
    print(f"WebSocket validation results: {len(results)} issues found")