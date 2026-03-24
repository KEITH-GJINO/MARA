"""Persistent memory store for agent context across executions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


class MemoryStore:
    """Key-value memory with namespace isolation for agents.

    Supports short-term (session) and long-term (persistent) memory.
    Each agent operates in its own namespace to prevent cross-contamination
    while still allowing explicit cross-agent memory sharing.

    Default backend is in-memory dict. Production deployments should
    use SQLite or Redis backends via subclassing.
    """

    def __init__(self, retention_days: int = 90) -> None:
        self.retention_days = retention_days
        self._store: dict[str, dict[str, Any]] = {}
        self._timestamps: dict[str, dict[str, str]] = {}

    async def store(
        self,
        namespace: str,
        key: str,
        value: Any,
    ) -> None:
        """Store a value in the given namespace.

        Args:
            namespace: Agent or scope identifier.
            key: Storage key within the namespace.
            value: Any JSON-serializable value.
        """
        if namespace not in self._store:
            self._store[namespace] = {}
            self._timestamps[namespace] = {}

        self._store[namespace][key] = value
        self._timestamps[namespace][key] = datetime.now(timezone.utc).isoformat()

    async def retrieve(
        self,
        namespace: str,
        query: str,
        limit: int = 10,
    ) -> str:
        """Retrieve relevant context from memory.

        Currently performs exact key matching. Semantic search
        will be added in v0.2.0 with embedding support.

        Args:
            namespace: Agent or scope identifier.
            query: Key or search query.
            limit: Maximum number of results.

        Returns:
            Formatted string of memory contents for prompt injection.
        """
        if namespace not in self._store:
            return ""

        ns = self._store[namespace]

        if query in ns:
            return self._format_memory(query, ns[query])

        results = []
        for key, value in list(ns.items())[:limit]:
            results.append(self._format_memory(key, value))

        return "\n\n".join(results) if results else ""

    async def delete(self, namespace: str, key: str) -> bool:
        if namespace in self._store and key in self._store[namespace]:
            del self._store[namespace][key]
            del self._timestamps[namespace][key]
            return True
        return False

    async def list_keys(self, namespace: str) -> list[str]:
        if namespace not in self._store:
            return []
        return list(self._store[namespace].keys())

    async def clear_namespace(self, namespace: str) -> None:
        self._store.pop(namespace, None)
        self._timestamps.pop(namespace, None)

    def _format_memory(self, key: str, value: Any) -> str:
        if isinstance(value, (dict, list)):
            formatted = json.dumps(value, indent=2, default=str)
        else:
            formatted = str(value)
        return f"[Memory: {key}]\n{formatted}"

    def __repr__(self) -> str:
        total = sum(len(ns) for ns in self._store.values())
        return f"<MemoryStore namespaces={len(self._store)} entries={total}>"
