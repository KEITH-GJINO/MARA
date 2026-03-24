"""Pipeline engine for composing and executing agent workflows."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable

from mara.core.agent import Agent, AgentResult


@dataclass
class PipelineStage:
    """A single stage in a pipeline, wrapping an agent with execution metadata."""

    name: str
    agent: Agent
    depends_on: list[str] = field(default_factory=list)
    condition: Callable[[dict[str, Any]], bool] | None = None

    def should_execute(self, context: dict[str, Any]) -> bool:
        if self.condition is None:
            return True
        return self.condition(context)


@dataclass
class PipelineResult:
    """Aggregated results from a complete pipeline execution."""

    pipeline_name: str
    stages: dict[str, AgentResult]
    total_execution_time: float = 0.0
    success: bool = True

    def get_stage(self, name: str) -> AgentResult | None:
        return self.stages.get(name)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pipeline_name": self.pipeline_name,
            "stages": {k: v.to_dict() for k, v in self.stages.items()},
            "total_execution_time": self.total_execution_time,
            "success": self.success,
        }


class Pipeline:
    """Composable workflow engine for chaining agents into multi-step operations.

    Supports sequential, parallel, and conditional execution patterns.
    The engine resolves dependencies between stages and determines the
    optimal execution order automatically.

    Example:
        pipeline = Pipeline(name="competitive_intel")
        pipeline.add_stage("research", ResearchAgent())
        pipeline.add_stage("analysis", AnalysisAgent(), depends_on=["research"])
        results = await pipeline.run(context={"competitors": [...]})
    """

    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description
        self.stages: dict[str, PipelineStage] = {}
        self._execution_order: list[list[str]] | None = None

    def add_stage(
        self,
        name: str,
        agent: Agent,
        depends_on: list[str] | None = None,
        condition: Callable[[dict[str, Any]], bool] | None = None,
    ) -> Pipeline:
        """Add an agent as a named stage in the pipeline.

        Args:
            name: Unique identifier for this stage.
            agent: The agent instance to execute.
            depends_on: List of stage names that must complete before this one.
            condition: Optional callable that receives the pipeline context
                and returns True if this stage should execute.

        Returns:
            Self, for method chaining.
        """
        if name in self.stages:
            raise ValueError(f"Stage '{name}' already exists in pipeline '{self.name}'")

        self.stages[name] = PipelineStage(
            name=name,
            agent=agent,
            depends_on=depends_on or [],
            condition=condition,
        )
        self._execution_order = None  # invalidate cached order
        return self

    def remove_stage(self, name: str) -> Pipeline:
        if name not in self.stages:
            raise ValueError(f"Stage '{name}' not found in pipeline '{self.name}'")
        del self.stages[name]
        self._execution_order = None
        return self

    async def run(self, context: dict[str, Any] | None = None) -> PipelineResult:
        """Execute the full pipeline.

        Resolves the dependency graph, groups stages into parallelizable
        batches, and executes them in order. Results from each stage are
        injected into the shared context for downstream stages.

        Args:
            context: Initial context dictionary passed to all stages.

        Returns:
            PipelineResult with all stage outputs and execution metadata.
        """
        context = dict(context or {})
        execution_order = self._resolve_execution_order()
        results: dict[str, AgentResult] = {}
        start = asyncio.get_event_loop().time()

        for batch in execution_order:
            tasks = []
            for stage_name in batch:
                stage = self.stages[stage_name]
                if stage.should_execute(context):
                    stage_context = self._build_stage_context(stage, context, results)
                    tasks.append(self._execute_stage(stage, stage_context))
                else:
                    results[stage_name] = AgentResult(
                        agent_name=stage.agent.config.name,
                        data=None,
                        confidence=0.0,
                    )

            if tasks:
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                for stage_name, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        return PipelineResult(
                            pipeline_name=self.name,
                            stages=results,
                            total_execution_time=asyncio.get_event_loop().time() - start,
                            success=False,
                        )
                    results[stage_name] = result
                    context[stage_name] = result.data

        elapsed = asyncio.get_event_loop().time() - start
        return PipelineResult(
            pipeline_name=self.name,
            stages=results,
            total_execution_time=elapsed,
        )

    def _resolve_execution_order(self) -> list[list[str]]:
        """Topological sort of stages into parallelizable batches."""
        if self._execution_order is not None:
            return self._execution_order

        in_degree: dict[str, int] = {name: 0 for name in self.stages}
        for name, stage in self.stages.items():
            for dep in stage.depends_on:
                if dep not in self.stages:
                    raise ValueError(
                        f"Stage '{name}' depends on '{dep}' which doesn't exist"
                    )
                in_degree[name] += 1

        order: list[list[str]] = []
        remaining = set(self.stages.keys())

        while remaining:
            batch = [
                name for name in remaining
                if in_degree[name] == 0
            ]
            if not batch:
                raise ValueError(
                    f"Circular dependency detected in pipeline '{self.name}'"
                )
            order.append(sorted(batch))
            for name in batch:
                remaining.remove(name)
                for other_name in remaining:
                    if name in self.stages[other_name].depends_on:
                        in_degree[other_name] -= 1

        self._execution_order = order
        return order

    def _build_stage_context(
        self,
        stage: PipelineStage,
        base_context: dict[str, Any],
        results: dict[str, AgentResult],
    ) -> dict[str, Any]:
        """Build the context dictionary for a specific stage."""
        ctx = dict(base_context)
        for dep in stage.depends_on:
            if dep in results:
                ctx[dep] = results[dep].data
        return ctx

    async def _execute_stage(
        self,
        stage: PipelineStage,
        context: dict[str, Any],
    ) -> AgentResult:
        return await stage.agent.run(context)

    def visualize(self) -> str:
        """Return a simple text representation of the pipeline DAG."""
        lines = [f"Pipeline: {self.name}"]
        order = self._resolve_execution_order()
        for i, batch in enumerate(order):
            lines.append(f"  Batch {i + 1}: {', '.join(batch)}")
            for name in batch:
                deps = self.stages[name].depends_on
                if deps:
                    lines.append(f"    └── depends on: {', '.join(deps)}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"<Pipeline name={self.name!r} stages={len(self.stages)}>"
