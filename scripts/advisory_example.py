"""Executable W6A fictional example. No model, network, database or file writes.

Run with the installed project Python. --input prints command input instead of
advice; --with-evidence supplies fictional verified labels, never real results.
"""

import argparse
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

from model_learner.domain.models import (
    AcceptanceSpec,
    DatasetReference,
    ExecutionConfiguration,
    Observation,
    Task,
)
from model_learner.learn.advisory import AdvisoryInput, AdvisoryRequest, advise
from model_learner.learn.prospective import (
    CompatibilityPolicy,
    ConfigurationMember,
    TaskMember,
)


def example(*, with_evidence: bool = False) -> AdvisoryInput:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    acceptance = AcceptanceSpec(identifier="fictional-parser", version="1")
    dataset = DatasetReference(
        source_kind="simulated", dataset_id="w6a-fictional-example", dataset_version="1"
    )
    configurations = tuple(
        ExecutionConfiguration(
            provider="fictional",
            model=model,
            reasoning_level=effort,
            harness="offline-fixture",
            harness_version="1",
        )
        for model, effort in (
            ("fictional-sol", "low"),
            ("fictional-sol", "high"),
            ("fictional-lower", "low"),
        )
    )
    task = Task(
        task_id=UUID(int=3),
        description="Fictional parser task; no agent execution",
        acceptance_spec=acceptance,
        task_group="fictional-parsing",
        created_at=start,
    )
    policy = CompatibilityPolicy(
        "fictional-advisory/v1",
        start,
        dataset.model_dump_json(),
        acceptance.model_dump_json(),
        "null",
        tuple(
            ConfigurationMember(c.model_dump_json(), f"separate-{i}")
            for i, c in enumerate(configurations)
        ),
        tuple(
            TaskMember(str(UUID(int=i)), "fictional-parsing", "fictional-text")
            for i in (1, 2, 3)
        ),
    )
    observations = (
        tuple(
            Observation(
                observation_id=UUID(int=100 + i),
                source_kind="simulated",
                dataset=dataset,
                source_record_id=f"fictional-label-{i}",
                task_id=UUID(int=i + 1),
                run_id=UUID(int=200 + i),
                task_group="fictional-parsing",
                configuration=configuration,
                acceptance_spec=acceptance,
                attribution_status="single_configuration",
                eligible_for_configuration_learning=True,
                outcome_status="success" if i == 0 else "failure",
                verification_status="verified",
                decision_at=start + timedelta(minutes=1),
                label_available_at=start + timedelta(minutes=2),
                recorded_at=start + timedelta(minutes=2),
            )
            for i, configuration in enumerate(configurations[:2])
        )
        if with_evidence
        else ()
    )
    return AdvisoryInput(
        request=AdvisoryRequest(
            task=task,
            candidates=configurations,
            policy=policy,
            cutoff=start + timedelta(hours=1),
        ),
        observations=observations,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-evidence", action="store_true")
    parser.add_argument("--input", action="store_true")
    arguments = parser.parse_args()
    payload = example(with_evidence=arguments.with_evidence)
    if arguments.input:
        print(payload.model_dump_json(indent=2))
    else:
        print(
            json.dumps(
                advise(payload.request, observations=payload.observations), indent=2
            )
        )
