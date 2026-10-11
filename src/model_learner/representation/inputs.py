"""Explicit public/sanitized initial descriptions; no transcript collection."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from model_learner.learn.estimator import require_aware
from model_learner.learn.task_state import TaskStateExample, generate_task_state_fixture


class TaskDescription(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    task_id: UUID
    task_family: str = Field(min_length=1, max_length=128)
    text: str = Field(min_length=1, max_length=4096)
    text_sha256: str = Field(pattern="^[0-9a-f]{64}$")
    source: Literal["public", "sanitized"]
    available_at: datetime

    @model_validator(mode="after")
    def validate_receipt(self) -> TaskDescription:
        require_aware(self.available_at, "description available_at")
        if not self.text.strip() or not self.task_family.strip():
            raise ValueError("description and task family must be nonblank")
        if hashlib.sha256(self.text.encode()).hexdigest() != self.text_sha256:
            raise ValueError("description text does not match its SHA-256 receipt")
        return self


class RepresentationExample(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version: Literal["task-representation-example/v1"] = (
        "task-representation-example/v1"
    )
    state: TaskStateExample
    description: TaskDescription

    @model_validator(mode="after")
    def validate_identity(self) -> RepresentationExample:
        if self.description.task_id != self.state.observation.task_id:
            raise ValueError("description and observation task identifiers must agree")
        return self


def representation_features(
    example: RepresentationExample, *, include_state: bool
) -> dict[str, float]:
    """The existing initial features plus allowlisted deterministic checkpoint facts.

    Description text, task/family identities, final tests, terminal execution state,
    outcomes and final resource totals cannot enter A/B. All counts use log1p.
    """
    row, facts = example.state.observation, example.state.checkpoint.facts
    result = {
        f"initial:task={row.task_group}": 1.0,
        f"initial:configuration={row.configuration.configuration_id}": 1.0,
    }
    if not include_state:
        return result
    values = (
        ("events", facts.event_count),
        ("tool_items", len(facts.tool_items)),
        ("started_turns", facts.started_turns),
        ("supported_events", facts.supported_event_count),
        *[
            (f"tokens_{k}", facts.token_usage.get(k))
            for k in ("input_tokens", "cached_input_tokens", "output_tokens")
        ],
    )
    for name, value in values:
        result[f"metrics:{name}:missing"] = float(value is None)
        if value is not None:
            if value < 0:
                raise ValueError("execution metrics must be nonnegative")
            result[f"metrics:{name}"] = math.log1p(value)
    for name, value in (
        ("failed_tools", facts.failed_tool_items),
        ("unknown_tools", facts.tool_items_with_unknown_failure),
        ("failed_turns", facts.failed_turns),
        ("repeated_failure_groups", len(facts.repeated_failures)),
        (
            "repeated_failure_items",
            sum(x.failed_items for x in facts.repeated_failures),
        ),
    ):
        if value < 0:
            raise ValueError("execution state counts must be nonnegative")
        result[f"state:{name}"] = math.log1p(value)
    result["state:failure_fraction"] = facts.failed_tool_items / max(
        1, facts.completed_tool_items
    )
    result["state:unknown_fraction"] = facts.tool_items_with_unknown_failure / max(
        1, len(facts.tool_items)
    )
    return result


def load_representation_examples(path: str | Path) -> tuple[RepresentationExample, ...]:
    values = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(values, list):
        raise ValueError("representation input must be a JSON array")
    return tuple(RepresentationExample.model_validate(x) for x in values)


_PUBLIC_OPERATIONS = (
    "Clamp an integer to inclusive ordered bounds.",
    "Parse an hours and minutes duration and reject malformed values.",
    "Compute the greatest common divisor of two integers.",
    "Merge overlapping inclusive intervals in sorted order.",
    "Find a pair of integers with a requested sum.",
    "Calculate the median of a nonempty sorted integer sequence.",
    "Topologically order a directed acyclic graph and reject cycles.",
    "Preserve the first occurrence of each element in a sequence.",
    "Split a delimited string while preserving empty fields.",
    "Count each word in a string after case normalization.",
    "Locate the longest common prefix of a sequence of strings.",
    "Validate balanced parentheses in a string.",
)


def generate_representation_fixture(
    *,
    seed: int = 1,
    count: int = 150,
    scenario: Literal["state_signal", "null_signal"] = "state_signal",
) -> tuple[RepresentationExample, ...]:
    """Invented public descriptions independent of simulated future outcomes.

    First 60% uses six task families; last 40% uses six different families.
    Variant numbers distinguish tasks, never encode their realized outcomes.
    This is algorithm rehearsal, not actual model-performance evidence.
    """
    rows = generate_task_state_fixture(seed=seed, count=count, scenario=scenario)
    split = int(count * 0.6)
    result = []
    for index, row in enumerate(rows):
        family = index % 6 + (0 if index < split else 6)
        text = f"{_PUBLIC_OPERATIONS[family]} Public task variant {index}."
        result.append(
            RepresentationExample(
                state=row,
                description=TaskDescription(
                    task_id=row.observation.task_id,
                    task_family=f"public-operation-{family}",
                    text=text,
                    text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                    source="public",
                    available_at=row.observation.decision_at,
                ),
            )
        )
    return tuple(result)
