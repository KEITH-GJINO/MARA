"""MARA Quickstart — run a competitive intelligence pipeline.

Usage:
    python -m examples.quickstart

Requires:
    - ANTHROPIC_API_KEY or OPENAI_API_KEY set in environment or .env
"""

import asyncio

from mara import Pipeline, Runtime
from mara.agents import (
    CompetitorResearchAgent,
    AudienceAnalysisAgent,
    ContentStrategyAgent,
)
from mara.core.providers import AnthropicProvider


async def main():
    # Initialize runtime with Anthropic Claude
    runtime = Runtime(
        llm=AnthropicProvider(model="claude-sonnet-4-20250514"),
    )

    # Build a competitive intelligence pipeline
    pipeline = Pipeline(
        name="competitive_intelligence",
        description="Full competitive analysis with content strategy output",
    )

    pipeline.add_stage("research", CompetitorResearchAgent())
    pipeline.add_stage("audience", AudienceAnalysisAgent())
    pipeline.add_stage(
        "content",
        ContentStrategyAgent(),
        depends_on=["research", "audience"],
    )

    # Visualize the execution plan
    print(pipeline.visualize())
    print("\nExecuting pipeline...\n")

    # Execute
    results = await runtime.run_pipeline(
        pipeline,
        context={
            "competitors": [
                "Competitor A — Enterprise SaaS platform",
                "Competitor B — SMB-focused alternative",
                "Competitor C — Open-source community tool",
            ],
            "audience_segments": ["enterprise", "mid-market", "developer"],
            "content_goals": {
                "primary": "Establish thought leadership in the category",
                "secondary": "Drive qualified demo requests",
                "timeline": "Q2 2026",
            },
        },
    )

    # Output
    if results.success:
        print(f"Pipeline completed in {results.total_execution_time:.2f}s")
        for stage_name, result in results.stages.items():
            print(f"\n{'='*60}")
            print(f"Stage: {stage_name}")
            print(f"Execution time: {result.execution_time:.2f}s")
            print(f"Output preview: {str(result.data)[:200]}...")
    else:
        print("Pipeline failed. Check agent logs for details.")


if __name__ == "__main__":
    asyncio.run(main())
