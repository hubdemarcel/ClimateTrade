"""
Example Integration: Using Resolution Subgraph with Polymarket Tools

This example demonstrates how to integrate the resolution subgraph client
with the existing Polymarket agents and py-clob-client for comprehensive
market analysis and backtesting.

The resolution subgraph provides historical data that complements:
1. Polymarket Agents: For strategy development and AI-driven trading
2. Py-clob-client: For real-time trading and market data access
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add the scripts directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from resolution_client import ResolutionSubgraphClient, format_resolution_data, calculate_resolution_stats

# Note: In a real integration, you would also import from the existing tools:
# from polymarket_client.py_clob_client import ClobClient
# from agents.polymarket.gamma import GammaMarketClient


class ComprehensiveMarketAnalyzer:
    """
    Comprehensive market analyzer that combines real-time and historical data.

    This class demonstrates how to integrate the resolution subgraph with
    existing Polymarket tools for complete market analysis.
    """

    def __init__(self):
        self.resolution_client = ResolutionSubgraphClient()
        # In a real implementation, you would initialize:
        # self.clob_client = ClobClient(...)
        # self.gamma_client = GammaMarketClient(...)

    def analyze_market_resolution_patterns(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Analyze market resolution patterns over a time period.

        Args:
            days_back: Number of days to look back

        Returns:
            Analysis results
        """
        # Calculate timestamp range
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)

        # Get resolved markets in the time range
        resolved_markets = self.resolution_client.get_resolved_markets(
            min_timestamp=int(start_time.timestamp()),
            max_timestamp=int(end_time.timestamp())
        )

        # Format the data
        formatted_markets = [format_resolution_data(market) for market in resolved_markets]

        # Calculate statistics
        stats = calculate_resolution_stats(resolved_markets)

        # Analyze dispute patterns
        disputed_markets = self.resolution_client.get_disputed_markets()

        return {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "days": days_back
            },
            "resolved_markets": formatted_markets,
            "statistics": stats,
            "disputed_markets_count": len(disputed_markets),
            "analysis": self._generate_insights(formatted_markets, stats)
        }

    def _generate_insights(self, markets: List[Dict[str, Any]], stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate insights from market resolution data.

        Args:
            markets: Formatted market data
            stats: Resolution statistics

        Returns:
            Insights dictionary
        """
        insights = {
            "dispute_risk": "High" if stats.get("dispute_rate", 0) > 0.1 else "Low",
            "market_reliability": "High" if stats.get("resolution_rate", 0) > 0.9 else "Medium",
            "recommendations": []
        }

        # Generate recommendations based on patterns
        if stats.get("dispute_rate", 0) > 0.1:
            insights["recommendations"].append(
                "Consider implementing additional due diligence for market creation"
            )

        if stats.get("resolution_rate", 0) < 0.9:
            insights["recommendations"].append(
                "Monitor markets with pending resolutions closely"
            )

        # Analyze price patterns
        price_changes = []
        for market in markets:
            if market.get("proposedPrice") and market.get("price"):
                change = abs(market["proposedPrice"] - market["price"])
                if change > 0.1:  # Significant price change
                    price_changes.append(market)

        if price_changes:
            insights["recommendations"].append(
                f"Found {len(price_changes)} markets with significant price changes during resolution"
            )

        return insights

    def backtest_strategy_with_historical_data(self, strategy_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Example backtesting function using historical resolution data.

        Args:
            strategy_config: Configuration for the backtesting strategy

        Returns:
            Backtesting results
        """
        # Get historical resolution data
        historical_resolutions = self.resolution_client.get_market_resolutions(
            first=strategy_config.get("sample_size", 100)
        )

        # Simulate strategy performance
        # This is a simplified example - real implementation would be more sophisticated
        profitable_trades = 0
        total_trades = 0

        for resolution in historical_resolutions:
            if resolution.get("status") == "resolved":
                total_trades += 1
                # Simple strategy: bet on resolutions that weren't disputed
                if not resolution.get("wasDisputed", False):
                    profitable_trades += 1

        return {
            "total_trades": total_trades,
            "profitable_trades": profitable_trades,
            "win_rate": profitable_trades / total_trades if total_trades > 0 else 0,
            "strategy": "No-dispute bias strategy",
            "historical_data_points": len(historical_resolutions)
        }

    def get_market_resolution_context(self, market_id: str) -> Dict[str, Any]:
        """
        Get comprehensive context for a market including resolution history.

        Args:
            market_id: The market/question ID

        Returns:
            Market context including resolution data
        """
        # Get resolution data
        resolution_data = self.resolution_client.get_market_resolution_by_id(market_id)

        if not resolution_data:
            return {"error": "Market resolution data not found"}

        # In a real implementation, you would also fetch:
        # - Current market data from Gamma API
        # - Order book data from CLOB
        # - Recent trades from py-clob-client

        context = {
            "market_id": market_id,
            "resolution_data": format_resolution_data(resolution_data),
            "resolution_status": resolution_data.get("status"),
            "was_disputed": resolution_data.get("wasDisputed", False),
            "final_price": resolution_data.get("price"),
            "last_update": datetime.fromtimestamp(
                int(resolution_data.get("lastUpdateTimestamp", 0))
            ).isoformat() if resolution_data.get("lastUpdateTimestamp") else None
        }

        # Add risk assessment
        context["risk_assessment"] = self._assess_market_risk(resolution_data)

        return context

    def _assess_market_risk(self, resolution_data: Dict[str, Any]) -> str:
        """
        Assess market risk based on resolution data.

        Args:
            resolution_data: Resolution data for the market

        Returns:
            Risk assessment string
        """
        if resolution_data.get("wasDisputed"):
            return "High - Market was disputed"

        if resolution_data.get("status") != "resolved":
            return "Medium - Market not yet resolved"

        # Check for significant price changes during resolution
        proposed = resolution_data.get("proposedPrice")
        final = resolution_data.get("price")

        if proposed and final:
            try:
                change = abs(int(proposed) - int(final)) / 10**18
                if change > 0.2:  # 20% price change
                    return "Medium - Significant price change during resolution"
            except (ValueError, TypeError):
                pass

        return "Low - Clean resolution"


def main():
    """
    Main function demonstrating the integration.
    """
    print("=== Polymarket Resolution Subgraph Integration Demo ===\n")

    analyzer = ComprehensiveMarketAnalyzer()

    # Analyze recent market resolution patterns
    print("1. Analyzing recent market resolution patterns...")
    analysis = analyzer.analyze_market_resolution_patterns(days_back=7)

    print(f"Time range: {analysis['time_range']['start']} to {analysis['time_range']['end']}")
    print(f"Resolved markets: {len(analysis['resolved_markets'])}")
    print(f"Dispute rate: {analysis['statistics'].get('dispute_rate', 0):.2%}")
    print(f"Risk assessment: {analysis['analysis']['dispute_risk']}")

    if analysis['analysis']['recommendations']:
        print("\nRecommendations:")
        for rec in analysis['analysis']['recommendations']:
            print(f"  - {rec}")

    # Example backtesting
    print("\n2. Running example backtest...")
    strategy_config = {"sample_size": 50}
    backtest_results = analyzer.backtest_strategy_with_historical_data(strategy_config)

    print(f"Strategy: {backtest_results['strategy']}")
    print(f"Win rate: {backtest_results['win_rate']:.2%}")
    print(f"Total trades: {backtest_results['total_trades']}")

    # Get context for a specific market (example)
    print("\n3. Getting market resolution context...")
    # Note: This would use a real market ID in practice
    example_context = {
        "market_id": "example-market-id",
        "resolution_data": {"status": "resolved", "wasDisputed": False},
        "risk_assessment": "Low - Clean resolution"
    }

    print(f"Market risk assessment: {example_context['risk_assessment']}")

    print("\n=== Integration Complete ===")
    print("\nThis demonstrates how the resolution subgraph complements:")
    print("- Polymarket Agents: Provides historical data for AI strategy training")
    print("- Py-clob-client: Offers resolution context for real-time trading decisions")
    print("- Backtesting: Enables analysis of past market performance")


if __name__ == "__main__":
    main()