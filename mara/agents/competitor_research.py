"""Competitor research agent — monitors competitor activity and surfaces strategic insights."""

from __future__ import annotations

from typing import Any

from mara.core.agent import Agent, AgentConfig


class CompetitorResearchAgent(Agent):
    """Tracks competitor positioning, messaging, pricing, and strategic moves.

    Analyzes publicly available competitor data to identify patterns,
    vulnerabilities, and opportunities. Builds a persistent competitor
    knowledge base that enriches over time.
    """

    config = AgentConfig(
        name="competitor_research",
        description="Monitors competitor activity and surfaces strategic insights",
        memory_enabled=True,
        approval_required=False,
    )

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        competitors = context.get("competitors", [])

        if not competitors:
            return {"error": "No competitors provided in context"}

        landscape = await self.analyze(
            task="competitor_landscape_analysis",
            data={"competitors": competitors},
            instructions="""
                For each competitor, analyze and structure findings into:

                1. POSITIONING
                   - Primary value proposition
                   - Target audience segments
                   - Key differentiators claimed

                2. MESSAGING
                   - Core narrative and brand voice
                   - Primary channels and content themes
                   - Recent messaging shifts or campaigns

                3. STRATEGIC MOVES
                   - Recent product/service changes
                   - Pricing model and recent adjustments
                   - Partnerships, acquisitions, or expansions
                   - Hiring patterns indicating strategic direction

                4. VULNERABILITIES
                   - Customer complaints and common objections
                   - Gaps in their offering
                   - Segments they're underserving
                   - Weaknesses in their positioning

                Return structured analysis with confidence scores
                for each insight (high/medium/low based on data quality).
            """,
        )

        await self.memory.store("competitor_intel", "latest_landscape", landscape)

        return {
            "analysis": landscape,
            "competitors_analyzed": len(competitors),
            "agent": self.config.name,
        }
