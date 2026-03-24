"""Tests for the MARA pipeline engine."""

import pytest
from typing import Any

from mara.core.agent import Agent, AgentConfig
from mara.core.pipeline import Pipeline, PipelineResult


class AddAgent(Agent):
    """Agent that adds a value to context for testing pipeline data flow."""

    config = AgentConfig(name="add_agent", description="Adds value", memory_enabled=False)

    def __init__(self, value: str = "added"):
        super().__init__()
        self.value = value

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        return {"value": self.value, "received_keys": list(context.keys())}


class MergeAgent(Agent):
    """Agent that merges upstream results for testing dependency resolution."""

    config = AgentConfig(name="merge_agent", description="Merges", memory_enabled=False)

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        return {"merged": True, "upstream_keys": list(context.keys())}


@pytest.mark.asyncio
async def test_sequential_pipeline():
    pipeline = Pipeline(name="test_seq")
    pipeline.add_stage("step1", AddAgent("first"))
    pipeline.add_stage("step2", AddAgent("second"), depends_on=["step1"])

    result = await pipeline.run()
    assert result.success
    assert "step1" in result.stages
    assert "step2" in result.stages
    assert result.stages["step1"].data["value"] == "first"
    assert result.stages["step2"].data["value"] == "second"


@pytest.mark.asyncio
async def test_parallel_pipeline():
    pipeline = Pipeline(name="test_parallel")
    pipeline.add_stage("a", AddAgent("alpha"))
    pipeline.add_stage("b", AddAgent("beta"))
    pipeline.add_stage("merge", MergeAgent(), depends_on=["a", "b"])

    result = await pipeline.run()
    assert result.success
    assert result.stages["merge"].data["merged"] is True


@pytest.mark.asyncio
async def test_conditional_stage():
    pipeline = Pipeline(name="test_cond")
    pipeline.add_stage("always", AddAgent("runs"))
    pipeline.add_stage(
        "conditional",
        AddAgent("skipped"),
        condition=lambda ctx: False,
    )

    result = await pipeline.run()
    assert result.success
    assert result.stages["conditional"].data is None


def test_duplicate_stage_raises():
    pipeline = Pipeline(name="test_dup")
    pipeline.add_stage("step", AddAgent())
    with pytest.raises(ValueError, match="already exists"):
        pipeline.add_stage("step", AddAgent())


def test_missing_dependency_raises():
    pipeline = Pipeline(name="test_missing")
    pipeline.add_stage("step", AddAgent(), depends_on=["nonexistent"])
    with pytest.raises(ValueError, match="doesn't exist"):
        pipeline._resolve_execution_order()


def test_circular_dependency_raises():
    pipeline = Pipeline(name="test_circular")
    pipeline.add_stage("a", AddAgent(), depends_on=["b"])
    pipeline.add_stage("b", AddAgent(), depends_on=["a"])
    with pytest.raises(ValueError, match="Circular dependency"):
        pipeline._resolve_execution_order()


def test_pipeline_visualize():
    pipeline = Pipeline(name="viz_test")
    pipeline.add_stage("research", AddAgent())
    pipeline.add_stage("analysis", AddAgent(), depends_on=["research"])
    text = pipeline.visualize()
    assert "viz_test" in text
    assert "research" in text
    assert "analysis" in text


def test_pipeline_result_to_dict():
    from mara.core.agent import AgentResult

    result = PipelineResult(
        pipeline_name="test",
        stages={"s1": AgentResult(agent_name="a", data="d")},
        total_execution_time=1.0,
    )
    d = result.to_dict()
    assert d["pipeline_name"] == "test"
    assert "s1" in d["stages"]


def test_remove_stage():
    pipeline = Pipeline(name="test_remove")
    pipeline.add_stage("a", AddAgent())
    pipeline.add_stage("b", AddAgent())
    pipeline.remove_stage("a")
    assert "a" not in pipeline.stages
    assert "b" in pipeline.stages
