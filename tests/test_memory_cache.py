import os

from agent.cache import DiskCache
from agent.memory import ConversationMemory


def test_memory_roundtrip(tmp_dir):
    mem = ConversationMemory(path=os.path.join(tmp_dir, "m.sqlite"))
    mem.add_user("hi")
    mem.add_assistant("hello there")
    hist = mem.history()
    assert hist == [("user", "hi"), ("assistant", "hello there")]


def test_memory_langchain_shape(tmp_dir):
    mem = ConversationMemory(path=os.path.join(tmp_dir, "m.sqlite"))
    mem.add_user("q")
    mem.add_assistant("a")
    msgs = mem.as_langchain_messages()
    assert msgs[0][0] == "human"
    assert msgs[1][0] == "ai"


def test_memory_sessions_and_clear(tmp_dir):
    path = os.path.join(tmp_dir, "m.sqlite")
    a = ConversationMemory(path=path, session="alpha")
    b = ConversationMemory(path=path, session="beta")
    a.add_user("one")
    b.add_user("two")
    assert set(a.sessions()) == {"alpha", "beta"}
    a.clear()
    assert a.history() == []
    assert b.history() == [("user", "two")]


def test_cache_set_get(tmp_dir):
    cache = DiskCache(path=os.path.join(tmp_dir, "c"))
    cache.set({"answer": 42}, "key", 1)
    assert cache.get("key", 1) == {"answer": 42}
    assert cache.get("missing") is None


def test_cache_clear(tmp_dir):
    cache = DiskCache(path=os.path.join(tmp_dir, "c"))
    cache.set("v", "a")
    cache.set("v", "b")
    assert cache.clear() == 2
