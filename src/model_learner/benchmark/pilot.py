"""Pure preregistration for an operator-run pilot; never executes an agent."""

import hashlib
import random
from dataclasses import dataclass

from model_learner.benchmark.fixtures import get_task
from model_learner.domain.models import ExecutionConfiguration

PILOT_TASK_IDS = (
    "clamp",
    "duration",
    "ceil_div",
    "first_index",
    "interval_length",
    "hex_integer",
    "median",
    "edit_distance",
    "components",
    "unique_window",
    "rpn",
    "balanced_span",
)


@dataclass(frozen=True)
class PilotRun:
    ordinal: int
    fixture_id: str
    fixture_version: str
    partition: str
    arm: str
    configuration: ExecutionConfiguration
    initial_source_sha256: str
    task_description_sha256: str


@dataclass(frozen=True)
class PilotPlan:
    version: str
    seed: int
    runs: tuple[PilotRun, ...]
    primary_checkpoint_seconds: int = 30
    diagnostic_checkpoint_seconds: tuple[int, ...] = (10, 60)
    agent_wall_limit_seconds: int = 120
    predictive_status: str = "blocked_export_contract_and_insufficient_data"
    execution_status: str = "blocked_unvalidated_containment"


def build_pilot_plan(
    *,
    configuration_a: ExecutionConfiguration,
    configuration_b: ExecutionConfiguration,
    seed: int = 1,
) -> PilotPlan:
    """Freeze 12 task pairs, a task-disjoint split and balanced arm order.

    Configurations are supplied by the operator after inspecting the installed
    executable. This is a schedule, not a routing decision or execution API.
    Separate preparation calls must stage each row in a fresh disposable root.
    """
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("pilot seed must be an integer")
    for configuration in (configuration_a, configuration_b):
        for field in (
            "provider",
            "model",
            "reasoning_level",
            "harness",
            "harness_version",
            "configuration_version",
        ):
            value = getattr(configuration, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"pilot requires declared {field}")
    if configuration_a.configuration_id == configuration_b.configuration_id:
        raise ValueError("pilot requires two distinct configurations")
    rng = random.Random(seed)
    tasks = list(PILOT_TASK_IDS)
    rng.shuffle(tasks)
    runs = []
    for partition, selected in (("training", tasks[:8]), ("held_out", tasks[8:])):
        # Exactly half of task pairs in each partition start with each arm.
        orders = [("A", "B"), ("B", "A")] * (len(selected) // 2)
        rng.shuffle(orders)
        for task_id, order in zip(selected, orders, strict=True):
            fixture = get_task(task_id)
            for arm in order:
                runs.append(
                    PilotRun(
                        ordinal=len(runs) + 1,
                        fixture_id=fixture.task_id,
                        fixture_version=fixture.version,
                        partition=partition,
                        arm=arm,
                        configuration=(
                            configuration_a if arm == "A" else configuration_b
                        ),
                        initial_source_sha256=hashlib.sha256(
                            fixture.initial_source.encode()
                        ).hexdigest(),
                        task_description_sha256=hashlib.sha256(
                            (fixture.description + "\n").encode()
                        ).hexdigest(),
                    )
                )
    return PilotPlan(version="real-coding-pilot/v1", seed=seed, runs=tuple(runs))
