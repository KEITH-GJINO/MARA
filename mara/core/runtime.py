"""MARA Runtime — the top-level orchestrator for agents and pipelines."""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any

from mara.core.agent import Agent
from mara.core.memory import MemoryStore
from mara.core.pipeline import Pipeline, PipelineResult
from mara.core.providers import AnthropicProvider, LLMProvider, OpenAIProvider


_PROVIDER_MAP: dict[str, type[LLMProvider]] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
}


class Runtime:
    """Central runtime that manages providers, memory, and agent execution.

    The Runtime is the recommended entry point for production use. It handles
    configuration loading, provider initialization, and provides a clean API
    for running agents and pipelines.

    Example:
        runtime = Runtime.from_config("mara.config.yaml")
        result = await runtime.run_agent(MyAgent(), context={...})
    """

    def __init__(
        self,
        llm: LLMProvider,
        memory: MemoryStore | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.llm = llm
        self.memory = memory or MemoryStore()
        self.config = config or {}
        self._registered_agents: dict[str, Agent] = {}

    @classmethod
    def from_config(cls, config_path: str | Path) -> Runtime:
        """Initialize a Runtime from a YAML configuration file.

        Args:
            config_path: Path to mara.config.yaml

        Returns:
            Configured Runtime instance.
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path) as f:
            config = yaml.safe_load(f)

        llm_config = config.get("llm", {})
        provider_name = llm_config.get("provider", "anthropic")
        provider_cls = _PROVIDER_MAP.get(provider_name)

        if provider_cls is None:
            raise ValueError(
                f"Unknown LLM provider: {provider_name}. "
                f"Available: {', '.join(_PROVIDER_MAP)}"
            )

        llm = provider_cls(model=llm_config.get("model", ""))

        memory_config = config.get("memory", {})
        memory = MemoryStore(
            retention_days=memory_config.get("retention_days", 90),
        )

        return cls(llm=llm, memory=memory, config=config)

    def register_agent(self, agent: Agent) -> None:
        """Register an agent with the runtime for discovery and reuse."""
        agent.llm = self.llm
        agent.memory = self.memory
        self._registered_agents[agent.config.name] = agent

    def get_agent(self, name: str) -> Agent | None:
        return self._registered_agents.get(name)

    async def run_agent(
        self,
        agent: Agent,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a single agent through the runtime.

        Injects the runtime's LLM provider and memory store if the
        agent doesn't already have them configured.
        """
        if agent.llm is None:
            agent.llm = self.llm
        if agent.memory is None:
            agent.memory = self.memory

        result = await agent.run(context or {})
        return result

    async def run_pipeline(
        self,
        pipeline: Pipeline,
        context: dict[str, Any] | None = None,
    ) -> PipelineResult:
        """Execute a pipeline through the runtime.

        All agents in the pipeline receive the runtime's LLM and memory.
        """
        for stage in pipeline.stages.values():
            if stage.agent.llm is None:
                stage.agent.llm = self.llm
            if stage.agent.memory is None:
                stage.agent.memory = self.memory

        return await pipeline.run(context)

    def __repr__(self) -> str:
        return (
            f"<Runtime provider={type(self.llm).__name__!r} "
            f"agents={len(self._registered_agents)}>"
        )
