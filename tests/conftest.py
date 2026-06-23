"""shared pytest fixtures.

these tests are all offline. nothing here calls a real model or hits the network, so they
run fast and do not need api keys.
"""

import os

import pytest

# make sure the agent never tries to talk to a real provider during tests
os.environ.setdefault("OPENAI_API_KEY", "sk-test-not-real")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-not-real")


@pytest.fixture
def tmp_dir(tmp_path):
    return str(tmp_path)
