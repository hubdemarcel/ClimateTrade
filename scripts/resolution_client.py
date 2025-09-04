"""
Polymarket Resolution Subgraph Client

This module provides access to historical market resolution data from the Polymarket
resolution subgraph. It complements the existing Polymarket tools by providing
historical data for backtesting, analysis, and strategy development.

The subgraph indexes market resolutions, disputes, and outcome data from Polymarket's
UMA-based resolution system.
"""

import requests
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResolutionSubgraphClient:
    """
    Client for querying Polymarket resolution subgraph data.

    This client provides methods to query historical market resolution data,
    including resolution status, prices, disputes, and timestamps.
    """

    def __init__(self, endpoint: str = "https://api.thegraph.com/subgraphs/name/polymarket/resolutions-subgraph"):
        """
        Initialize the resolution subgraph client.

        Args:
            endpoint: The GraphQL endpoint for the resolution subgraph
        """
        self.endpoint = endpoint
        self.session = requests.Session()

    def _execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query against the subgraph.

        Args:
            query: The GraphQL query string
            variables: Optional variables for the query

        Returns:
            The query response data
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            response = self.session.post(
                self.endpoint,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                raise Exception(f"GraphQL query failed: {data['errors']}")

            return data.get("data", {})

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def get_market_resolutions(
        self,
        first: int = 100,
        skip: int = 0,
        order_by: str = "lastUpdateTimestamp",
        order_direction: str = "desc"
    ) -> List[Dict[str, Any]]:
        """
        Get market resolution data.

        Args:
            first: Number of records to fetch
            skip: Number of records to skip
            order_by: Field to order by
            order_direction: Order direction (asc/desc)

        Returns:
            List of market resolution records
        """
        query = """
        query GetMarketResolutions($first: Int!, $skip: Int!, $orderBy: String!, $orderDirection: String!) {
          marketResolutions(
            first: $first
            skip: $skip
            orderBy: $orderBy
            orderDirection: $orderDirection
          ) {
            id
            newVersionQ
            author
            ancillaryData
            lastUpdateTimestamp
            status
            wasDisputed
            proposedPrice
            reproposedPrice
            price
            updates
            transactionHash
            logIndex
            approved
          }
        }
        """

        variables = {
            "first": first,
            "skip": skip,
            "orderBy": order_by,
            "orderDirection": order_direction
        }

        data = self._execute_query(query, variables)
        return data.get("marketResolutions", [])

    def get_market_resolution_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific market resolution by question ID.

        Args:
            question_id: The question ID to look up

        Returns:
            Market resolution data or None if not found
        """
        query = """
        query GetMarketResolution($id: ID!) {
          marketResolution(id: $id) {
            id
            newVersionQ
            author
            ancillaryData
            lastUpdateTimestamp
            status
            wasDisputed
            proposedPrice
            reproposedPrice
            price
            updates
            transactionHash
            logIndex
            approved
          }
        }
        """

        data = self._execute_query(query, {"id": question_id})
        return data.get("marketResolution")

    def get_ancillary_data_mapping(self, ancillary_data_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get the mapping from ancillary data hash to question ID.

        Args:
            ancillary_data_hash: The hash of the ancillary data

        Returns:
            Mapping data or None if not found
        """
        query = """
        query GetAncillaryDataHashToQuestionId($id: ID!) {
          ancillaryDataHashToQuestionId(id: $id) {
            id
            questionId
          }
        }
        """

        data = self._execute_query(query, {"id": ancillary_data_hash})
        return data.get("ancillaryDataHashToQuestionId")

    def get_moderators(self) -> List[Dict[str, Any]]:
        """
        Get all moderators and their permissions.

        Returns:
            List of moderator records
        """
        query = """
        query GetModerators {
          moderators {
            id
            canMod
          }
        }
        """

        data = self._execute_query(query)
        return data.get("moderators", [])

    def get_revisions(
        self,
        first: int = 100,
        skip: int = 0,
        order_by: str = "timestamp",
        order_direction: str = "desc"
    ) -> List[Dict[str, Any]]:
        """
        Get revision history for market updates.

        Args:
            first: Number of records to fetch
            skip: Number of records to skip
            order_by: Field to order by
            order_direction: Order direction (asc/desc)

        Returns:
            List of revision records
        """
        query = """
        query GetRevisions($first: Int!, $skip: Int!, $orderBy: String!, $orderDirection: String!) {
          revisions(
            first: $first
            skip: $skip
            orderBy: $orderBy
            orderDirection: $orderDirection
          ) {
            id
            moderator
            questionId
            timestamp
            update
            transactionHash
          }
        }
        """

        variables = {
            "first": first,
            "skip": skip,
            "orderBy": order_by,
            "orderDirection": order_direction
        }

        data = self._execute_query(query, variables)
        return data.get("revisions", [])

    def get_resolved_markets(
        self,
        min_timestamp: Optional[int] = None,
        max_timestamp: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get markets that have been resolved within a timestamp range.

        Args:
            min_timestamp: Minimum timestamp (Unix timestamp)
            max_timestamp: Maximum timestamp (Unix timestamp)

        Returns:
            List of resolved market records
        """
        # Build filter conditions
        where_conditions = ["status: resolved"]

        if min_timestamp:
            where_conditions.append(f"lastUpdateTimestamp_gte: {min_timestamp}")
        if max_timestamp:
            where_conditions.append(f"lastUpdateTimestamp_lte: {max_timestamp}")

        where_clause = ", ".join(where_conditions)

        query = f"""
        query GetResolvedMarkets {{
          marketResolutions(
            where: {{{where_clause}}}
            orderBy: lastUpdateTimestamp
            orderDirection: desc
          ) {{
            id
            newVersionQ
            author
            ancillaryData
            lastUpdateTimestamp
            status
            wasDisputed
            proposedPrice
            reproposedPrice
            price
            updates
            transactionHash
            logIndex
            approved
          }}
        }}
        """

        data = self._execute_query(query)
        return data.get("marketResolutions", [])

    def get_disputed_markets(self) -> List[Dict[str, Any]]:
        """
        Get markets that have been disputed.

        Returns:
            List of disputed market records
        """
        query = """
        query GetDisputedMarkets {
          marketResolutions(
            where: {wasDisputed: true}
            orderBy: lastUpdateTimestamp
            orderDirection: desc
          ) {
            id
            newVersionQ
            author
            ancillaryData
            lastUpdateTimestamp
            status
            wasDisputed
            proposedPrice
            reproposedPrice
            price
            updates
            transactionHash
            logIndex
            approved
          }
        }
        """

        data = self._execute_query(query)
        return data.get("marketResolutions", [])


# Utility functions for data processing
def format_resolution_data(resolution: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format raw resolution data for easier consumption.

    Args:
        resolution: Raw resolution data from subgraph

    Returns:
        Formatted resolution data
    """
    formatted = resolution.copy()

    # Convert timestamps to datetime objects
    if "lastUpdateTimestamp" in formatted:
        formatted["lastUpdateTimestamp"] = datetime.fromtimestamp(
            int(formatted["lastUpdateTimestamp"])
        )

    # Convert prices from BigInt strings to floats (assuming 18 decimals for prices)
    price_fields = ["proposedPrice", "reproposedPrice", "price"]
    for field in price_fields:
        if field in formatted and formatted[field]:
            try:
                # Convert from BigInt string to float
                formatted[field] = int(formatted[field]) / 10**18
            except (ValueError, TypeError):
                pass

    return formatted


def calculate_resolution_stats(resolutions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics from a list of resolution records.

    Args:
        resolutions: List of resolution records

    Returns:
        Dictionary with resolution statistics
    """
    if not resolutions:
        return {}

    total_resolutions = len(resolutions)
    disputed_count = sum(1 for r in resolutions if r.get("wasDisputed", False))
    resolved_count = sum(1 for r in resolutions if r.get("status") == "resolved")

    # Calculate average resolution time if timestamps are available
    resolution_times = []
    for r in resolutions:
        if r.get("status") == "resolved" and "lastUpdateTimestamp" in r:
            # This is a simplified calculation - in reality you'd need creation timestamp
            resolution_times.append(int(r["lastUpdateTimestamp"]))

    avg_resolution_time = None
    if resolution_times:
        avg_resolution_time = sum(resolution_times) / len(resolution_times)

    return {
        "total_resolutions": total_resolutions,
        "disputed_count": disputed_count,
        "resolved_count": resolved_count,
        "dispute_rate": disputed_count / total_resolutions if total_resolutions > 0 else 0,
        "resolution_rate": resolved_count / total_resolutions if total_resolutions > 0 else 0,
        "average_resolution_timestamp": avg_resolution_time
    }


# Example usage and integration points
def example_backtesting_integration():
    """
    Example of how to integrate resolution data with backtesting.

    This shows how the resolution subgraph can be used alongside
    the Polymarket agents and py-clob-client for comprehensive
    market analysis and strategy development.
    """
    client = ResolutionSubgraphClient()

    # Get recent resolutions for backtesting
    recent_resolutions = client.get_market_resolutions(first=50)

    # Analyze resolution patterns
    stats = calculate_resolution_stats(recent_resolutions)

    print("Resolution Statistics:")
    print(f"Total resolutions: {stats['total_resolutions']}")
    print(f"Dispute rate: {stats['dispute_rate']:.2%}")
    print(f"Resolution rate: {stats['resolution_rate']:.2%}")

    # Example: Find markets that were heavily disputed
    disputed_markets = client.get_disputed_markets()

    print(f"\nFound {len(disputed_markets)} disputed markets")

    return recent_resolutions, stats


if __name__ == "__main__":
    # Example usage
    example_backtesting_integration()