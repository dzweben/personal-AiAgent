"""a writing-rules knowledge base the agent writes by.

this is bigger than APA: it's a growing library of writing rules drawn from recognised style
authorities (the APA Publication Manual, Williams' *Style: Lessons in Clarity and Grace*, Strunk
& White, academic-writing conventions). each rule knows how to spot its own violation and what
to suggest instead, so the linter can flag prose and the writer can self-correct toward good
academic writing -- not just correct formatting.

import-time side effect: importing this package registers all the built-in rules.
"""

from __future__ import annotations

from agent.style import builtin  # noqa: F401 - registers the built-in rules
from agent.style.readability import readability
from agent.style.rules import Finding, Rule, all_rules, lint, register

__all__ = ["Finding", "Rule", "all_rules", "lint", "register", "readability"]
