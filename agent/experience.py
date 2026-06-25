"""the compounding layer: the agent gets better the more you use it.

this ties the two memories together. after a run, `remember()` files the answer into semantic
memory and stashes any distilled lessons. before a run, `recall_context()` pulls the lessons and
past answers most relevant to the new question and formats them as a prepend for the prompt -- so
yesterday's work informs today's. point it at a directory and it persists across sessions.
"""

from __future__ import annotations

from pathlib import Path

from agent.reflect import LessonStore, reflect
from agent.semantic_memory import SemanticMemory


class Experience:
    def __init__(self, directory: str = ".agent_experience"):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.lessons = LessonStore(path=str(self.dir / "lessons.sqlite"))
        self.memory = SemanticMemory(path=str(self.dir / "notes.jsonl"))

    def remember(self, question: str, answer: str, lessons: list[str] | None = None, extract=None):
        """store the answer (for semantic recall) and any lessons (for explicit reuse).

        if `lessons` isn't given, derive them with reflect() using the injectable `extract`.
        """
        self.memory.add(answer, question=question)
        if lessons is None and extract is not None:
            lessons = reflect(question, answer, extract=extract)
        for lesson in lessons or []:
            self.lessons.add(topic=question, lesson=lesson)

    def recall_context(self, question: str, k_lessons: int = 3, k_notes: int = 3) -> str:
        """build a prompt addendum from the most relevant past lessons and answers, or ''."""
        lessons = self.lessons.recall(question, k=k_lessons)
        notes = self.memory.recall(question, k=k_notes)
        if not lessons and not notes:
            return ""
        blocks = []
        if lessons:
            blocks.append(
                "Lessons from past runs:\n" + "\n".join(f"- {lesson.lesson}" for lesson in lessons)
            )
        if notes:
            blocks.append(
                "Relevant notes from past answers:\n"
                + "\n".join(f"- {n.text[:200]}" for n in notes)
            )
        return "\n\n".join(blocks)

    def stats(self) -> dict:
        return {"lessons": len(self.lessons.all()), "notes": len(self.memory)}
