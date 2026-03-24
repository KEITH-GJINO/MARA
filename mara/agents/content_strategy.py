"""Content strategy agent — plans, audits, and optimizes content operations."""

from __future__ import annotations

from typing import Any

from mara.core.agent import Agent, AgentConfig


class ContentStrategyAgent(Agent):
    """Plans content operations based on audience insights and competitive gaps.

    Generates editorial calendars, identifies content gaps, and maps
    content to funnel stages and audience segments. Learns from
    performance data to refine recommendations over time.
    """

    config = AgentConfig(
        name="content_strategy",
        description="Content planning, gap analysis, and editorial calendar generation",
        memory_enabled=True,
        approval_required=False,
    )

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        audience_data = context.get("audience_analysis", {})
        competitor_data = context.get("competitor_research", {})
        existing_content = context.get("content_inventory", [])
        goals = context.get("content_goals", {})

        strategy = await self.analyze(
            task="content_strategy_development",
            data={
                "audience_insights": audience_data,
                "competitive_content": competitor_data,
                "existing_content": existing_content,
                "goals": goals,
            },
            instructions="""
                Develop a comprehensive content strategy covering:

                1. CONTENT AUDIT
                   - Strengths and gaps in existing content
                   - Performance patterns (what's working, what isn't)
                   - Content age and refresh priorities

                2. STRATEGIC PILLARS
                   - Core topic clusters aligned to audience needs
                   - Differentiation angles vs competitor content
                   - Thought leadership opportunities

                3. FUNNEL MAPPING
                   - Top-of-funnel: awareness and discovery content
                   - Mid-funnel: consideration and evaluation content
                   - Bottom-funnel: decision and conversion content
                   - Retention: loyalty and expansion content

                4. EDITORIAL CALENDAR
                   - Priority content pieces with briefs
                   - Publishing cadence recommendations
                   - Channel distribution strategy
                   - Resource and capacity requirements

                5. MEASUREMENT FRAMEWORK
                   - KPIs per content type and funnel stage
                   - Leading vs lagging indicators
                   - Review and optimization cadence
            """,
        )

        return {
            "strategy": strategy,
            "agent": self.config.name,
        }
