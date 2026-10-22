"""J1 frozen task-intent research contract; never a canonical Task or utility input.

This is a LOCAL contract. OpenRouter's alpha wire schema is not available offline.
Reference labels are authored synthetic judgments, awaiting independent human review.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

VERSION = "task-intent/v1"
BASELINE_VERSION = "intent-keywords/v1"
LABELS = (
    "bug_fix",
    "new_feature",
    "refactor",
    "investigation",
    "documentation",
    "unclear",
)
Intent = Literal[
    "bug_fix", "new_feature", "refactor", "investigation", "documentation", "unclear"
]
Probability = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
RUBRIC = (
    "Label the requested task, never the eventual patch or outcome. "
    "bug_fix: restore stated existing intended behavior; new_feature: add stated "
    "new behavior; refactor: reorganize executable implementation while preserving "
    "behavior; investigation: diagnose, compare or explain without a requested "
    "repair; documentation: change prose or examples intended only as documentation. "
    "For mixed intent use an explicit dominant objective; subordinate tests/docs "
    "follow that objective. Equal independent objectives, vague requests, or "
    "insufficient context are unclear. Do not infer a repair from a diagnosis."
)
CODE_RUBRIC = (
    "Does the request explicitly need executable source-code changes? True for "
    "an explicit implementation, repair, executable test, or code refactor request. "
    "False for only investigation, explanation, documentation, or static data. "
    "Code shown only in documentation is false. Conditional future repairs, "
    "unspecified 'improve this', and mixed requests without explicit implementation "
    "are ambiguous; express uncertainty rather than inventing a requirement."
)


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class Question(Strict):
    id: str
    kind: Literal["choice", "noul", "score"]
    prompt: str
    labels: tuple[str, ...] = ()
    levels: tuple[float, ...] = ()

    @model_validator(mode="after")
    def supported(self):
        if not self.id or len(self.prompt) > 2048:
            raise ValueError("invalid local question")
        if self.kind == "choice":
            if len(self.labels) < 2 or len(set(self.labels)) != len(self.labels):
                raise ValueError("distinct choice labels required")
            if self.levels:
                raise ValueError("choice cannot declare score levels")
        elif self.kind == "score":
            if (
                self.labels
                or not self.levels
                or len(set(self.levels)) != len(self.levels)
            ):
                raise ValueError("score requires distinct numeric levels only")
            if any(not (-1000 <= x <= 1000) for x in self.levels):
                raise ValueError("invalid score level")
        elif self.labels or self.levels:
            raise ValueError("noul has no labels or levels")
        return self


QUESTIONS = (
    Question(id="primary_intent_v1", kind="choice", prompt=RUBRIC, labels=LABELS),
    Question(id="executable_changes_v1", kind="noul", prompt=CODE_RUBRIC),
)
# Fictional parser control only. No difficulty question or evaluation target.
SCORE_CONTROL = Question(
    id="fictional_score_control_v1",
    kind="score",
    prompt="Fictional scalar control",
    levels=(0.0, 1.0, 2.0),
)


def canonical(value) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def digest(value) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


class Prediction(Strict):
    intent: Intent | None
    code_probability: Probability | None
    origin: Literal["deterministic_baseline", "mocked_external_model"]


def baseline(description: str) -> Prediction:
    """Fixed lexical rules, frozen before holdout prediction; no training/model load."""
    text = description.lower()
    rules = (
        ("investigation", r"\b(investigate|explain|diagnose|compare)\b"),
        ("documentation", r"\b(document|readme|guide|glossary)\b"),
        ("bug_fix", r"\b(fix|repair|restore|regression)\b"),
        ("refactor", r"\b(refactor|reorganize|rename)\b"),
        ("new_feature", r"\b(add|implement|create)\b"),
    )
    intent = next(
        (label for label, pattern in rules if re.search(pattern, text)), "unclear"
    )
    code = (
        0.0
        if intent in ("documentation", "investigation")
        else (0.5 if intent == "unclear" else 1.0)
    )
    return Prediction(
        intent=intent, code_probability=code, origin="deterministic_baseline"
    )


# Freeze the actual rule implementation as well as its public version.
BASELINE_SHA256 = hashlib.sha256(inspect.getsource(baseline).encode()).hexdigest()
