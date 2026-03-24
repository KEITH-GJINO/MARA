"""Campaign analysis agent — evaluates performance and generates optimization insights."""

from __future__ import annotations

from typing import Any

from mara.core.agent import Agent, AgentConfig


class CampaignAnalysisAgent(Agent):
    """Analyzes marketing campaign performance across channels and surfaces optimizations.

    Processes campaign metrics to identify what's working, what's failing,
    and what to do next. Supports multi-channel attribution and
    incrementality analysis.
    """

    config = AgentConfig(
        name="campaign_analysis",
        description="Campaign performance analysis and optimization recommendations",
        memory_enabled=True,
        approval_required=False,
        metadata={"status": "beta"},
    )

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        campaign_data = context.get("campaign_data", {})
        historical = context.get("historical_performance", {})
        budget = context.get("budget_constraints", {})

        analysis = await self.analyze(
            task="campaign_performance_analysis",
            data={
                "current_campaigns": campaign_data,
                "historical": historical,
                "budget": budget,
            },
            instructions="""
                Analyze campaign performance and provide:

                1. PERFORMANCE SUMMARY
                   - Key metrics by campaign and channel
                   - Trend analysis vs historical benchmarks
                   - Budget efficiency and ROAS by segment

                2. ATTRIBUTION INSIGHTS
                   - Channel contribution analysis
                   - Cross-channel interaction effects
                   - First-touch vs last-touch vs multi-touch views

                3. OPTIMIZATION RECOMMENDATIONS
                   - Budget reallocation opportunities
                   - Creative and messaging improvements
                   - Audience targeting refinements
                   - Bid and placement adjustments

                4. FORECAST
                   - Expected performance at current trajectory
                   - Impact projections for recommended changes
                   - Confidence intervals and key assumptions

                Prioritize recommendations by expected impact and ease
                of implementation.
            """,
        )

        return {
            "analysis": analysis,
            "agent": self.config.name,
        }
