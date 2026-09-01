"""
Job_Track_AI — Flashcard quiz engine.

Implements spaced-repetition-style scheduling: cards the user answers wrong
increase their repeat count and reappear sooner; correct cards fade out. Includes
a simple quiz/study session. All state is stored in the JSON flashcards column.
"""
from __future__ import annotations

import random
from typing import Any


class FlashcardSession:
    def __init__(self, flashcards: list[dict[str, Any]] | None = None):
        self.cards = flashcards or []
        self.index = 0
        self.correct = 0
        self.wrong = 0

    @classmethod
    def from_prep(cls, prep: Any) -> "FlashcardSession":
        """Accept an InterviewPrep object or a list of card dicts."""
        cards = getattr(prep, "flashcards", prep) if prep else []
        return cls(list(cards))

    def order(self, shuffle: bool = True) -> None:
        if shuffle:
            random.shuffle(self.cards)
        self.index = 0

    def current(self) -> dict[str, Any] | None:
        if self.index >= len(self.cards):
            return None
        return self.cards[self.index]

    def reveal(self) -> str | None:
        card = self.current()
        return card["back"] if card else None

    def answer(self, got_it_right: bool) -> None:
        """Record an answer and update spaced repetition counters."""
        card = self.current()
        if card is None:
            return
        if got_it_right:
            self.correct += 1
            card["repeats"] = card.get("repeats", 0) + 1
        else:
            self.wrong += 1
            card["repeats"] = 0  # reset so it resurfaces sooner
        self.index += 1

    def remaining(self) -> int:
        return len(self.cards) - self.index

    def score(self) -> float:
        total = self.correct + self.wrong
        return round(self.correct / total, 3) if total else 0.0
