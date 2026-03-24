"""Audience analysis agent — segments audiences and uncovers behavioral insights."""

from __future__ import annotations

from typing import Any

from mara.core.agent import Agent, AgentConfig


class AudienceAnalysisAgent(Agent):
    """Analyzes audience data to identify segments, behaviors, and opportunities.

    Processes demographic, psychographic, and behavioral data to build
    actionable audience profiles. Identifies underserved segments and
    maps audience needs to product/service capabilities.
    """

    config = AgentConfig(
        name="audience_analysis",
        description="Audience segmentation and behavioral insights engine",
        memory_enabled=True,
        approval_required=False,
    )

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        segments = context.get("audience_segments", [])
        product_data = context.get("product_data", {})
        competitor_intel = context.get("competitor_research", {})

        analysis = await self.analyze(
            task="audience_segmentation",
            data={
                "segments": segments,
                "product": product_data,
                "competitive_landscape": competitor_intel,
            },
            instructions="""
                Perform deep audience analysis across the following dimensions:

                1. SEGMENT PROFILES
                   - Demographics and firmographics
                   - Psychographic patterns (values, motivations, fears)
                   - Behavioral signals (buying patterns, content consumption)
                   - Decision-making process and key influences

                2. NEEDS MAPPING
                   - Primary pain points per segment
                   - Unmet needs and underserved use cases
                   - Willingness to pay and value sensitivity
                   - Switching triggers and loyalty factors

                3. CHANNEL AFFINITY
                   - Preferred information sources
                   - Content format preferences
                   - Platform usage patterns
                   - Peak engagement windows

                4. OPPORTUNITY SCORING
                   - Segment size and accessibility
                   - Competitive intensity per segment
                   - Alignment with current capabilities
                   - Revenue potential and growth trajectory

                Rank segments by strategic priority with clear rationale.
            """,
        )

        return {
            "analysis": analysis,
            "segments_analyzed": len(segments),
            "agent": self.config.name,
        }
