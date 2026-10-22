"""W6B reviewed fictional handoff; never launches or executes candidate code.

All bytes/events are authored synthetic fixtures. REAL is used solely to exercise
the production real-contract resolver in disposable storage, never measured data.
The independent fixture verifier compares a bounded data artifact to b"42\n".
This is operator choreography, not an external authentication/import service.
"""

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from pydantic import TypeAdapter

from model_learner.adapters.codex import capture_codex_stream, ingest_codex_capture
from model_learner.domain.models import (
    AcceptanceSpec,
    Attempt,
    DatasetReference,
    ExecutionConfiguration,
    Run,
    RunSessionLink,
    Session,
    Task,
    TaskSessionLink,
    Verification,
    utc_now,
)
from model_learner.learn.advisory import AdvisoryInput, AdvisoryRequest, advise
from model_learner.learn.prospective import (
    CompatibilityPolicy,
    ConfigurationMember,
    TaskMember,
    forecast,
    freeze,
    score_frozen,
)
from model_learner.observations import build_real_observation
from model_learner.storage import evidence as portable
from model_learner.storage.database import Database, Repository, StorageError
from model_learner.verification import (
    JUnitReportBinding,
    assess_run,
    file_sha256,
    junit_criterion,
    verify_junit,
)

DATASET = DatasetReference(
    source_kind="real", dataset_id="synthetic-w6b-disposable-only", dataset_version="1"
)
SPEC = AcceptanceSpec(identifier="fictional-answer-data", version="1")
CONFIG = ExecutionConfiguration(
    provider="fictional",
    model="fictional-coder",
    reasoning_level="low",
    harness="codex.exec",
    harness_version="synthetic-v1",
)
REQUIRED = ["fixture::exact_answer"]


def repository(path):
    database = Database(path)
    database.initialize()
    return Repository(database)


def declare():
    """No budget is approved for this separate data fixture; unrelated to W4A."""
    return Task(
        description="Fictional bounded answer data; no agent execution",
        acceptance_spec=SPEC,
        task_group="fictional-data",
        created_at=utc_now(),
        metadata={"junit_verifier": junit_criterion(required_test_ids=REQUIRED)},
    )


def policy_for(tasks):
    return CompatibilityPolicy(
        "fictional-w6b/v1",
        utc_now(),
        DATASET.model_dump_json(),
        SPEC.model_dump_json(),
        "null",
        (ConfigurationMember(CONFIG.model_dump_json(), "fictional"),),
        tuple(TaskMember(str(t.task_id), t.task_group, "fictional") for t in tasks),
    )


def produce(directory, task, run_id, *, broken=False, emitted_model=None, budget=None):
    """Fictional producer: serialize execution only, without trusted labels."""
    directory.mkdir()
    source = repository(directory / "producer.sqlite")
    source.create_task(task)
    start = utc_now()
    native = [
        {"type": "thread.started", "thread_id": f"fictional-{run_id}"},
        {"type": "turn.started", "model": emitted_model or CONFIG.model},
        {
            "type": "item.completed",
            "item": {
                "type": "agent_message",
                "text": "Fictional pass self-report",
            },
        },
        {"type": "turn.completed"},
    ]
    capture = directory / "capture.jsonl"
    with capture.open("w") as stream:
        result = capture_codex_stream(
            map(json.dumps, native), stream, source_version="synthetic-v1"
        )
    assert result.accepted == 4 and not result.diagnostics
    imported = ingest_codex_capture(source, capture, machine_id="fictional-machine")
    assert imported.events_inserted == 4 and not imported.diagnostics
    session = source.list_records(Session)[0]
    artifact = directory / "answer.txt"
    artifact.write_bytes(b"41\n" if broken else b"42\n")
    end = utc_now()
    run = source.create_run(
        Run(
            run_id=run_id,
            task_id=task.task_id,
            state="finished",
            started_at=start,
            ended_at=end,
            resource_budget=budget,
            metadata={"final_artifact_fingerprint": "sha256:" + file_sha256(artifact)},
        )
    )
    source.associate_session(
        TaskSessionLink(
            task_id=task.task_id,
            session_id=session.session_id,
        )
    )
    source.associate_run_session(
        RunSessionLink(
            run_id=run_id,
            session_id=session.session_id,
        )
    )
    source.create_attempt(
        Attempt(
            run_id=run_id,
            configuration=CONFIG,
            started_at=start,
            ended_at=end,
            metadata={"configuration_provenance": "human_declaration"},
        )
    )
    package = portable.scoped_bundle(source, task_id=task.task_id, dataset=DATASET)
    (directory / "execution.json").write_text(package.model_dump_json())
    return source, run


def receive_execution(directory, approved_task, approved_run_id):
    """Reviewed fixture intake: reject producer verification/labels, re-receipt.

    Real external input needs a separately approved trust contract. These fixture
    checks are deliberately not advertised as a production security boundary.
    """
    package = portable.EvidenceBundle.model_validate_json(
        (directory / "execution.json").read_text()
    )
    if any(
        e.record_type in {"Verification", "Outcome", "Observation"}
        or e.received_at is not None
        for e in package.entries
    ):
        raise ValueError("fixture intake requires execution-only unreceipted evidence")
    records = [e.parse() for e in package.entries]
    if (
        package.dataset != DATASET
        or package.task_id != approved_task.task_id
        or [r for r in records if isinstance(r, Task)]
        != [portable._public(approved_task)]
        or [r.run_id for r in records if isinstance(r, Run)] != [approved_run_id]
        or [r.configuration for r in records if isinstance(r, Attempt)] != [CONFIG]
    ):
        raise ValueError("fixture handoff disagrees with frozen intake")
    receiver = repository(directory / "receiver.sqlite")
    portable.import_bundle(receiver, package)
    book = portable.ReceiptBook()
    book.capture(package)
    (directory / "execution-receipts.json").write_text(book.model_dump_json())
    return receiver, book


def trusted_report(directory, task, run):
    """Separate reviewed verifier: inspect data only; never execute its contents."""
    artifact = directory / "answer.txt"
    with artifact.open("rb") as stream:
        passed = stream.read(65) == b"42\n"
    report = directory / "independent.xml"
    report.write_text(
        f'<testsuite tests="1" failures="{int(not passed)}" errors="0" skipped="0">'
        '<testcase classname="fixture" name="exact_answer">'
        + ("" if passed else "<failure/>")
        + "</testcase></testsuite>"
    )
    return JUnitReportBinding(
        task_id=task.task_id,
        run_id=run.run_id,
        acceptance_spec=SPEC,
        artifact_fingerprint="sha256:" + file_sha256(artifact),
        report_sha256=file_sha256(report),
        report_generated_at=utc_now(),
        source="junit",
        execution_completed=True,
        command_exit_code=int(not passed),
    )


def verify_and_receive(receiver, book, directory, run, binding):
    evidence = verify_junit(
        receiver,
        run_id=run.run_id,
        report=directory / "independent.xml",
        artifact=directory / "answer.txt",
        binding=binding,
    )
    outcome = assess_run(
        receiver, run_id=run.run_id, verification_id=evidence.verification_id
    )
    row = build_real_observation(
        receiver, run_id=run.run_id, outcome_id=outcome.outcome_id, dataset=DATASET
    )
    book.capture(portable.scoped_bundle(receiver, task_id=run.task_id, dataset=DATASET))
    bundle = portable.scoped_bundle(
        receiver, task_id=run.task_id, dataset=DATASET, receipts=book
    )
    (directory / "resolved.json").write_text(bundle.model_dump_json())
    (directory / "receipts.json").write_text(book.model_dump_json())
    return row, bundle


def demonstrate(root):
    tasks = [declare() for _ in range(3)]
    policy = policy_for(tasks)
    adapter = TypeAdapter(CompatibilityPolicy)
    (root / "policy.json").write_bytes(adapter.dump_json(policy))
    (root / "intake.json").write_text(
        json.dumps(
            {
                "tasks": [portable._public(t).model_dump(mode="json") for t in tasks],
                "configuration": CONFIG.model_dump(mode="json"),
                "trusted_fixture_sha256": file_sha256(Path(__file__)),
                "fixture_provenance": "synthetic-w6b; not measured agent execution",
            }
        )
    )
    bundles, scores, checksums = [], [], []
    for i, task in enumerate(tasks[:2]):
        run_id, cutoff = uuid4(), utc_now()
        rows = [
            row
            for b in bundles
            for row in portable.resolve_bundle(b, cutoff=cutoff).observations
        ]
        prediction = forecast(
            rows,
            policy=policy,
            task_id=task.task_id,
            run_id=run_id,
            configuration=CONFIG,
            cutoff=cutoff,
        )
        path = root / f"forecast-{i}.json"
        checksum = freeze(path, prediction)
        (root / f"forecast-{i}.sha256").write_text(checksum + "\n")
        checksums.append(checksum)
        directory = root / f"handoff-{i}"
        _, run = produce(directory, task, run_id, broken=bool(i))
        receiver, book = receive_execution(directory, task, run_id)
        row, bundle = verify_and_receive(
            receiver, book, directory, run, trusted_report(directory, task, run)
        )
        resolved = portable.resolve_bundle(bundle, cutoff=utc_now()).observations[0]
        assert row.stable_key == resolved.stable_key
        scores.append(score_frozen(path, checksum, resolved))
        bundles.append(bundle)
    request = AdvisoryRequest(
        task=tasks[2], candidates=(CONFIG,), policy=policy, cutoff=utc_now()
    )
    envelope = AdvisoryInput(request=request, bundles=tuple(bundles))
    (root / "advisory-input.json").write_text(envelope.model_dump_json())
    advice = advise(request, bundles=bundles)
    (root / "advisory.json").write_text(json.dumps(advice, sort_keys=True))
    summary = {
        "origin": "fictional-offline-only",
        "scores": scores,
        "forecast_sha256": checksums,
        "eligible_outcomes": advice["eligible_source_count"],
        "policy_fingerprint": policy.fingerprint,
    }
    # Summaries retain actual calculated forecasts, never prefilled predictions.
    summary["forecast_probabilities"] = [
        json.loads((root / f"forecast-{i}.json").read_text())["predictions"][0][
            "probability"
        ]
        for i in range(2)
    ]
    (root / "summary.json").write_text(json.dumps(summary, sort_keys=True))
    return summary


def replay(root):
    """Read retained fictional evidence; reconstruct only in temporary storage.

    Local consistency with the reviewed fixture is not external authenticity.
    Original receipt times and frozen forecasts are never regenerated.
    """

    def require(condition, message):
        if not condition:
            raise ValueError(message)

    intake = json.loads((root / "intake.json").read_text())
    require(
        intake["trusted_fixture_sha256"] == file_sha256(Path(__file__)),
        "reviewed fixture source changed; use the original checkout",
    )
    tasks = [Task.model_validate(t) for t in intake["tasks"]]
    require(len(tasks) == 3, "expected three fictional tasks")
    require(intake["configuration"] == CONFIG.model_dump(mode="json"), "configuration")
    policy = TypeAdapter(CompatibilityPolicy).validate_json(
        (root / "policy.json").read_text()
    )
    envelope = AdvisoryInput.model_validate_json(
        (root / "advisory-input.json").read_text()
    )
    require(envelope.request.policy == policy, "advisory policy mismatch")
    require(
        portable._public(envelope.request.task) == tasks[2], "advisory task mismatch"
    )
    bundles, scores, checksums, probabilities = [], [], [], []
    with TemporaryDirectory(prefix="model-learner-replay-") as temporary:
        for i, task in enumerate(tasks[:2]):
            directory = root / f"handoff-{i}"
            bundle = portable.EvidenceBundle.model_validate_json(
                (directory / "resolved.json").read_text()
            )
            require(bundle.dataset == DATASET, "fictional dataset mismatch")
            book = portable.ReceiptBook.model_validate_json(
                (directory / "receipts.json").read_text()
            )
            execution = portable.EvidenceBundle.model_validate_json(
                (directory / "execution.json").read_text()
            )
            first = portable.ReceiptBook.model_validate_json(
                (directory / "execution-receipts.json").read_text()
            )
            require(
                execution.dataset == DATASET
                and execution.task_id == task.task_id
                and not execution.verification_attempts,
                "execution intake mismatch",
            )
            execution_store = repository(Path(temporary) / f"execution-{i}.sqlite")
            portable.import_bundle(execution_store, execution)
            expected_entries = {
                portable.key(e.parse()): e
                for e in bundle.entries
                if e.record_type not in {"Verification", "Outcome", "Observation"}
            }
            require(
                len(execution.entries) == len(expected_entries),
                "execution membership mismatch",
            )
            for entry in execution.entries:
                retained = expected_entries.get(portable.key(entry.parse()))
                require(
                    entry.received_at is None
                    and retained is not None
                    and entry.record == retained.record
                    and entry.sha256 == retained.sha256,
                    "execution-only evidence mismatch",
                )
            require(
                first.receipts
                == {
                    key: value
                    for key, value in book.receipts.items()
                    if key in expected_entries
                },
                "first receipt mismatch",
            )
            restored = repository(Path(temporary) / f"resolved-{i}.sqlite")
            portable.import_bundle(restored, bundle)
            portable.import_bundle(restored, bundle)
            require(
                portable.scoped_bundle(
                    restored, task_id=task.task_id, dataset=DATASET, receipts=book
                )
                == bundle,
                "retained receipts or scoped reconstruction mismatch",
            )
            require(restored.get(Task, task.task_id) == task, "intake task mismatch")
            run = restored.list_records(Run)[0]
            evidence = restored.list_records(Verification)[0]
            binding = JUnitReportBinding.model_validate(evidence.metadata["binding"])
            # Recheck actual retained artifact/XML through the original verifier.
            checked = verify_junit(
                restored,
                run_id=run.run_id,
                artifact=directory / "answer.txt",
                report=directory / "independent.xml",
                binding=binding,
                observed_at=evidence.observed_at,
            )
            require(checked.result == evidence.result, "verification result mismatch")
            with (directory / "answer.txt").open("rb") as stream:
                require(
                    stream.read(65) == (b"41\n" if i else b"42\n"),
                    "reviewed fictional artifact mismatch",
                )
            rows = portable.resolve_bundle(
                bundle, cutoff=envelope.request.cutoff
            ).observations
            require(len(rows) == 1, "expected one resolved observation")
            row = rows[0]
            require(row.eligible_for_configuration_learning, "ineligible outcome")
            require(
                row.outcome_status.value == ("failure" if i else "success"),
                "fictional outcome mismatch",
            )
            path = root / f"forecast-{i}.json"
            frozen = json.loads(path.read_text())
            cutoff = datetime.fromisoformat(frozen["cutoff"])
            reconstructed = forecast(
                [
                    r
                    for b in bundles
                    for r in portable.resolve_bundle(b, cutoff=cutoff).observations
                ],
                policy=policy,
                task_id=task.task_id,
                run_id=run.run_id,
                configuration=CONFIG,
                cutoff=cutoff,
            )
            require(
                json.loads(json.dumps(asdict(reconstructed))) == frozen,
                "historical forecast mismatch",
            )
            checksum = (root / f"forecast-{i}.sha256").read_text().strip()
            scores.append(score_frozen(path, checksum, row))
            checksums.append(checksum)
            probabilities.append(frozen["predictions"][0]["probability"])
            bundles.append(bundle)
    require(tuple(bundles) == envelope.bundles, "advisory evidence mismatch")
    advice = advise(envelope.request, bundles=bundles)
    require(
        advice == json.loads((root / "advisory.json").read_text()), "advisory mismatch"
    )
    summary = {
        "origin": "fictional-offline-only",
        "scores": scores,
        "forecast_sha256": checksums,
        "eligible_outcomes": advice["eligible_source_count"],
        "policy_fingerprint": policy.fingerprint,
        "forecast_probabilities": probabilities,
    }
    require(
        summary == json.loads((root / "summary.json").read_text()), "summary mismatch"
    )
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--output-directory", type=Path, help="Retain in a new directory."
    )
    mode.add_argument("--replay-directory", type=Path, help="Check retained evidence.")
    arguments = parser.parse_args(argv)
    try:
        if arguments.replay_directory:
            summary = replay(arguments.replay_directory)
        elif arguments.output_directory:
            arguments.output_directory.mkdir(parents=True, exist_ok=False)
            demonstrate(arguments.output_directory)
            summary = replay(arguments.output_directory)
        else:
            with TemporaryDirectory(prefix="model-learner-w6b-") as temporary:
                root = Path(temporary)
                demonstrate(root)
                summary = replay(root)
    except (
        OSError,
        ValueError,
        KeyError,
        IndexError,
        TypeError,
        StorageError,
    ) as error:
        # Avoid echoing file contents or arbitrary validation input on refusal.
        parser.exit(1, f"Fictional demo/replay refused ({type(error).__name__}).\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    main()
