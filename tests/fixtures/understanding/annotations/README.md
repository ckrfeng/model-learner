# Unannotated task-understanding collection seed

`seed.json` is a small benchmark collection for exercising the annotation CLI.
It contains 18 sanitized task snapshots: three historical candidates and three
queries in each of train, development and test. Project, family and lineage
identifiers do not cross splits. Its labels, reviews, protocol and freeze are
empty. It has no measured retrieval result or task outcome.

Every description and proposal is **agent-authored**. There has been no human
annotation or independent human review. The proposals in `proposals/` illustrate
complete `QueryJudgment` inputs; they are drafts that reviewers can reject. They
are not evaluation ground truth. A person's copying an agent proposal does not
make its technical judgment independent. Human annotators should first judge
snapshots and evidence without inspecting proposals or model rankings; independent
human reviewers should check those labels and resolve disagreements. Caller
identity attestations cannot authenticate the people performing this work.

This committed public fixture is an example of the workflow, not an unexposed
future holdout. For substantive evaluation, collect a new version with realistic
independently reviewed examples, keep its test groups unseen during selection,
and prospectively lock labels and the selected protocol before test scoring.
Only development examples can inform threshold selection. No model training or
model download is part of this seed.

## Sources and provenance

Three historical train descriptions are reused verbatim from the existing
sanitized `../retrieval_v1.json`. Each origin gives that file's SHA-256 and exact
JSON pointer to the description. Its frozen content is unchanged. These reused
examples were already exposed in the prior retrieval experiment; they are not
new independent evidence. Development and test descriptions, plus all queries,
are newly authored in `authored_descriptions.json`; origin locators are JSON
pointers of the form `#/descriptions/q-f19`, with the SHA-256 of actual source
bytes. Authorship stays `agent` in both cases. Source digests are provenance
references, not automatic attestations of real execution.

Only the train candidate `h-x17` includes an observed fact, `e-j37`, taken from
`tests/fixtures/execution/controlled_capture.jsonl`. Its source locator
`jsonl:4` means the complete fourth JSONL row, including its item and
redaction metadata. The complete source-file hash is retained. The source is a **simulated**
controlled fixture even though this surrounding description dataset is a
**benchmark**. The fact says only that the simulated metadata records command-1
as failed with exit code 1 and redacts the command/output. Attaching it as
constructed context does not assert that the profile-cache task was executed,
that the command was a verifier, that the task failed, or that it was difficult.
No executions, costs, private transcripts or verified outcomes were collected.

Snapshot checkpoint times and canonical UUIDs are hypothetical declared benchmark
context. The UUIDs exercise explicit task identity; they are not real ledger
records. Descriptions and explicit identity declarations remain distinct from
inferred relation/scope/apparent-difficulty judgments. Similarity never creates
an identity or ledger/session association.

## Coverage and collection

Opaque snapshot identifiers do not encode relevance. Every proposal covers all
three historical candidates in the query's own split, and every pair cites its
query and candidate snapshot IDs as evidence. Draft cases include:

| Query | Split | Case illustrated by the draft |
| --- | --- | --- |
| `q-f19` | train | Declared cache repair continues with expanded multi-worker scope; navigation wording trap. |
| `q-c07` | train | CDN avatar traffic has no relevant preference-cache history. |
| `q-m61` | train | Stale-read regression is similar; missing declared query identity leaves continuation unknown. |
| `q-b73` | development | Payroll rounding repair adds periods and corrections; documentation and locale formatting negatives. |
| `q-h28` | development | Same repair narrows to positive monthly amounts, apparently reducing acceptance constraints. |
| `q-r44` | development | CSV character encoding has no relevant currency history despite shared export wording. |
| `q-z53` | test | Archive containment repair adds symlink rejection and cleanup; preview-order wording trap. |
| `q-n06` | test | Independently declared containment regression is relevant history without continuity. |
| `q-d81` | test | Requester retains the declared identity while changing extraction to export: continuation and no relevant historical objective coexist. |

Apparent-difficulty drafts compare stated acceptance constraints. `unknown` is
used when cross-objective work cannot be compared; no draft treats retries,
command failures, completion or relevance scores as difficulty evidence. Human
review must check these inferences instead of assuming this table is correct.

A CLI exercise that honestly retains proposal authorship:

```sh
uv run model-learner annotation prepare \
  tests/fixtures/understanding/annotations/seed.json \
  /tmp/task-annotations-draft-v1.json --dataset-id local-task-annotations-draft-v1
uv run model-learner annotation show /tmp/task-annotations-draft-v1.json \
  --query-id q-f19
uv run model-learner annotation label /tmp/task-annotations-draft-v1.json q-f19 \
  tests/fixtures/understanding/annotations/proposals/q-f19.json \
  --annotator proposal-agent --actor-kind agent \
  --output /tmp/task-annotations-draft-v2.json
```

Outputs are new files. This exercise cannot freeze or evaluate the dataset:
it has agent labels, incomplete query coverage and no accepting human reviews.
See [the annotation protocol](../../../../docs/TASK_ANNOTATIONS.md) for independent
human labeling, review, freeze and evaluation. Retrieval evaluation does not
establish improved model-utility prediction.
