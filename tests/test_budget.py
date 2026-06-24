"""tests for the cost budget guard."""

from __future__ import annotations

import pytest

from agent.budget import Budget, BudgetExceeded


def test_charges_accumulate():
    b = Budget()
    b.charge("a short prompt", 100, "one")
    b.charge("another short prompt", 100, "two")
    assert len(b.charges) == 2
    assert b.spent > 0
    assert b.remaining() == float("inf")  # no cap


def test_ceiling_blocks_oversized_call():
    b = Budget(max_usd=0.001)
    with pytest.raises(BudgetExceeded):
        b.charge("x" * 200000, 9000, "huge")
    # the failed charge was not recorded
    assert b.charges == []


def test_guard_is_nonraising():
    b = Budget(max_usd=0.001)
    assert b.guard("tiny", 10) is True
    assert b.guard("x" * 200000, 9000) is False


def test_remaining_decreases():
    b = Budget(max_usd=1.0)
    before = b.remaining()
    b.charge("some prompt text here", 200, "call")
    assert b.remaining() < before
