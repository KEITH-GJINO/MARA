"""Tests for the MARA agent base class."""

import pytest
import asyncio
from typing import Any

from mara.core.agent import Agent, AgentConfig, AgentResult, AgentState
from mara.core.memory import MemoryStore


class MockAgent(Agent):
    """Simple agent for testing."""

    config = AgentConfig(
        name="mock_agent",
        description="A test agent",
        memory_enabled=False,
    )

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        return {"received": context, "output": "test_result"}


class ApprovalAgent(Agent):
    """Agent that requires approval for testing."""

    config = AgentConfig(
        name="approval_agent",
        description="An agent requiring approval",
        approval_required=True,
    )

    async def execute(self, context: dict[str, Any]) -> str:
        return "approved_result"

    async def _request_approval(self, context: dict[str, Any]) -> bool:
        return context.get("approved", False)


class FailingAgent(Agent):
    """Agent that always fails for testing error handling."""

    config = AgentConfig(
        name="failing_agent",
        description="Always fails",
    )

    async def execute(self, context: dict[str, Any]) -> None:
        raise ValueError("Intentional test failure")


@pytest.mark.asyncio
async def test_agent_execute():
    agent = MockAgent()
    result = await agent.execute({"key": "value"})
    assert result["output"] == "test_result"
    assert result["received"]["key"] == "value"


@pytest.mark.asyncio
async def test_agent_run_lifecycle():
    agent = MockAgent()
    assert agent.state == AgentState.IDLE

    result = await agent.run({"input": "data"})

    assert isinstance(result, AgentResult)
    assert result.agent_name == "mock_agent"
    assert result.data["output"] == "test_result"
    assert result.execution_time >= 0
    assert agent.state == AgentState.COMPLETED
    assert agent._execution_count == 1


@pytest.mark.asyncio
async def test_agent_approval_granted():
    agent = ApprovalAgent()
    result = await agent.run({"approved": True})
    assert result.data == "approved_result"
    assert agent.state == AgentState.COMPLETED


@pytest.mark.asyncio
async def test_agent_approval_denied():
    agent = ApprovalAgent()
    result = await agent.run({"approved": False})
    assert result.data is None
    assert result.confidence == 0.0
    assert agent.state == AgentState.IDLE


@pytest.mark.asyncio
async def test_agent_failure():
    agent = FailingAgent()
    with pytest.raises(RuntimeError, match="Intentional test failure"):
        await agent.run({})
    assert agent.state == AgentState.FAILED


@pytest.mark.asyncio
async def test_agent_execution_count():
    agent = MockAgent()
    await agent.run({})
    await agent.run({})
    await agent.run({})
    assert agent._execution_count == 3


def test_agent_repr():
    agent = MockAgent()
    repr_str = repr(agent)
    assert "mock_agent" in repr_str
    assert "idle" in repr_str


def test_agent_result_to_dict():
    result = AgentResult(
        agent_name="test",
        data={"key": "value"},
        confidence=0.95,
        execution_time=1.5,
    )
    d = result.to_dict()
    assert d["agent_name"] == "test"
    assert d["confidence"] == 0.95
    assert "timestamp" in d
