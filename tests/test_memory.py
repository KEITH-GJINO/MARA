"""Tests for the MARA memory store."""

import pytest

from mara.core.memory import MemoryStore


@pytest.mark.asyncio
async def test_store_and_retrieve():
    memory = MemoryStore()
    await memory.store("agent_a", "key1", {"data": "value"})
    result = await memory.retrieve("agent_a", "key1")
    assert "value" in result


@pytest.mark.asyncio
async def test_retrieve_nonexistent_namespace():
    memory = MemoryStore()
    result = await memory.retrieve("nonexistent", "key")
    assert result == ""


@pytest.mark.asyncio
async def test_delete():
    memory = MemoryStore()
    await memory.store("ns", "key", "value")
    deleted = await memory.delete("ns", "key")
    assert deleted is True
    result = await memory.retrieve("ns", "key")
    assert result == ""


@pytest.mark.asyncio
async def test_delete_nonexistent():
    memory = MemoryStore()
    deleted = await memory.delete("ns", "nope")
    assert deleted is False


@pytest.mark.asyncio
async def test_list_keys():
    memory = MemoryStore()
    await memory.store("ns", "a", 1)
    await memory.store("ns", "b", 2)
    await memory.store("ns", "c", 3)
    keys = await memory.list_keys("ns")
    assert set(keys) == {"a", "b", "c"}


@pytest.mark.asyncio
async def test_list_keys_empty():
    memory = MemoryStore()
    keys = await memory.list_keys("empty")
    assert keys == []


@pytest.mark.asyncio
async def test_clear_namespace():
    memory = MemoryStore()
    await memory.store("ns", "a", 1)
    await memory.store("ns", "b", 2)
    await memory.clear_namespace("ns")
    keys = await memory.list_keys("ns")
    assert keys == []


@pytest.mark.asyncio
async def test_namespace_isolation():
    memory = MemoryStore()
    await memory.store("agent_a", "key", "a_value")
    await memory.store("agent_b", "key", "b_value")
    result_a = await memory.retrieve("agent_a", "key")
    result_b = await memory.retrieve("agent_b", "key")
    assert "a_value" in result_a
    assert "b_value" in result_b


def test_memory_repr():
    memory = MemoryStore()
    assert "namespaces=0" in repr(memory)
