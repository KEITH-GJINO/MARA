"""SEO research agent — keyword research, SERP analysis, and technical audits."""

from __future__ import annotations

from typing import Any

from mara.core.agent import Agent, AgentConfig


class SEOResearchAgent(Agent):
    """Conducts SEO research across keyword opportunity, SERP landscape, and technical health.

    Identifies ranking opportunities, analyzes search intent patterns,
    and surfaces technical issues. Integrates with content strategy
    to align SEO priorities with editorial planning.
    """

    config = AgentConfig(
        name="seo_research",
        description="Keyword research, SERP analysis, and technical SEO audits",
        memory_enabled=True,
        approval_required=False,
        metadata={"status": "beta"},
    )

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        target_keywords = context.get("keywords", [])
        domain = context.get("domain", "")
        competitors = context.get("competitors", [])

        research = await self.analyze(
            task="seo_research",
            data={
                "target_keywords": target_keywords,
                "domain": domain,
                "competitors": competitors,
            },
            instructions="""
                Conduct comprehensive SEO analysis:

                1. KEYWORD OPPORTUNITIES
                   - Search volume and difficulty assessment
                   - Search intent classification per keyword
                   - Long-tail expansion opportunities
                   - Featured snippet and SERP feature potential

                2. COMPETITIVE SERP ANALYSIS
                   - Current ranking landscape per target keyword
                   - Competitor content analysis (format, depth, quality)
                   - Content gap identification
                   - Link profile comparisons

                3. TECHNICAL ASSESSMENT
                   - Site architecture recommendations
                   - Internal linking opportunities
                   - Schema markup suggestions
                   - Core Web Vitals priorities

                4. PRIORITY ACTIONS
                   - Quick wins (low effort, high impact)
                   - Strategic investments (high effort, high ceiling)
                   - Technical fixes ranked by impact
                   - Content creation priorities with target keywords

                Score each opportunity on a matrix of effort vs impact.
            """,
        )

        return {
            "research": research,
            "keywords_analyzed": len(target_keywords),
            "agent": self.config.name,
        }
