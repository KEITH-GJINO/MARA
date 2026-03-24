"""Base agent class and configuration for MARA agents."""

from __future__ import annotations

import asyncio
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from mara.core.memory import MemoryStore
from mara.core.providers import LLMProvider


class AgentState(Enum):
    """Lifecycle states for a MARA agent."""

    IDLE = "idle"
    INITIALIZING = "initializing"
    EXECUTING = "executing"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentConfig:
    """Configuration for an individual agent."""

    name: str
    description: str
    memory_enabled: bool = True
    approval_required: bool = False
    timeout: int = 300
    max_retries: int = 3
    retry_backoff: float = 2.0
    temperature: float = 0.3
    max_tokens: int = 4096
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Structured result from an agent execution."""

    agent_name: str
    data: Any
    confidence: float = 1.0
    execution_time: float = 0.0
    token_usage: dict[str, int] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "data": self.data,
            "confidence": self.confidence,
            "execution_time": self.execution_time,
            "token_usage": self.token_usage,
            "timestamp": self.timestamp,
        }


class Agent(ABC):
    """Base class for all MARA agents.

    Subclass this to create specialized marketing agents. Each agent
    encapsulates a specific marketing function and can operate standalone
    or as part of a pipeline.

    Example:
        class MyAgent(Agent):
            config = AgentConfig(
                name="my_agent",
                description="Does something useful",
            )

            async def execute(self, context):
                result = await self.analyze(
                    task="my_task",
                    data=context.get("input"),
                    instructions="Analyze this data.",
                )
                return result
    """

    config: AgentConfig

    def __init__(
        self,
        llm: LLMProvider | None = None,
        memory: MemoryStore | None = None,
    ) -> None:
        self.id = str(uuid.uuid4())
        self.state = AgentState.IDLE
        self.llm = llm
        self.memory = memory or MemoryStore()
        self._execution_count = 0
        self._created_at = datetime.now(timezone.utc)

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> Any:
        """Execute the agent's primary function.

        Args:
            context: Dictionary of inputs and shared state from the
                pipeline or direct invocation.

        Returns:
            Agent output — can be any serializable type. When running
            in a pipeline, this is passed downstream to dependent stages.
        """
        ...

    async def analyze(
        self,
        task: str,
        data: Any,
        instructions: str,
        **kwargs: Any,
    ) -> Any:
        """Send a structured analysis request to the LLM provider.

        This is the primary interface agents use to interact with the
        underlying language model. It handles prompt construction,
        provider routing, and response parsing.

        Args:
            task: Short identifier for the analysis type.
            data: Input data to analyze.
            instructions: Natural language instructions for the model.
            **kwargs: Additional provider-specific parameters.

        Returns:
            Parsed model response.
        """
        if self.llm is None:
            raise RuntimeError(
                f"Agent '{self.config.name}' has no LLM provider configured. "
                "Pass an LLMProvider instance during initialization or "
                "run the agent through a Runtime."
            )

        prompt = self._build_prompt(task, data, instructions)
        memory_context = ""

        if self.config.memory_enabled and self.memory:
            memory_context = await self.memory.retrieve(
                namespace=self.config.name,
                query=task,
            )

        response = await self.llm.complete(
            prompt=prompt,
            context=memory_context,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
        )

        if self.config.memory_enabled and self.memory:
            await self.memory.store(
                namespace=self.config.name,
                key=task,
                value=response,
            )

        return response

    async def run(self, context: dict[str, Any]) -> AgentResult:
        """Full lifecycle execution with state management and telemetry.

        This is called by the pipeline engine. For direct use, you can
        call execute() directly.
        """
        self.state = AgentState.INITIALIZING
        start_time = asyncio.get_event_loop().time()

        try:
            self.state = AgentState.EXECUTING
            self._execution_count += 1

            if self.config.approval_required:
                self.state = AgentState.WAITING_APPROVAL
                approved = await self._request_approval(context)
                if not approved:
                    self.state = AgentState.IDLE
                    return AgentResult(
                        agent_name=self.config.name,
                        data=None,
                        confidence=0.0,
                    )
                self.state = AgentState.EXECUTING

            result = await self.execute(context)
            elapsed = asyncio.get_event_loop().time() - start_time

            self.state = AgentState.COMPLETED
            return AgentResult(
                agent_name=self.config.name,
                data=result,
                execution_time=elapsed,
            )

        except Exception as e:
            self.state = AgentState.FAILED
            raise RuntimeError(
                f"Agent '{self.config.name}' failed: {e}"
            ) from e

    def _build_prompt(self, task: str, data: Any, instructions: str) -> str:
        return (
            f"Task: {task}\n"
            f"Agent: {self.config.name} — {self.config.description}\n\n"
            f"Instructions:\n{instructions}\n\n"
            f"Data:\n{data}"
        )

    async def _request_approval(self, context: dict[str, Any]) -> bool:
        """Override to implement custom approval logic."""
        return True

    def __repr__(self) -> str:
        return (
            f"<Agent name={self.config.name!r} "
            f"state={self.state.value!r} "
            f"executions={self._execution_count}>"
        )
