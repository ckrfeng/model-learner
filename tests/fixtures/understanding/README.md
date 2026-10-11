# Frozen constructed semantic retrieval fixture

`retrieval_v1.json` contains independently authored technical relevance judgments,
not evaluated-encoder labels or agent-success outcomes. Author is a Codex agent;
external human adjudication is absent. Each candidate includes a rationale. All
text is newly authored, with no private conversation content or copied issues.

`manifest.json` freezes the final pre-encoding content hash, split counts and
metric choices. Provenance wording was corrected before initial encoding. Never
edit labels or wording based on reference scores: create a new dataset/holdout
version for subsequent work. Development/test families, projects and rewrite
groups are disjoint; within-split same-family retrieval targets are intentional.

`reference.json` records three fresh socket-blocked CPU workers per method,
including complete per-query top-three scores/relevant ranks, aggregate and family
metrics, false top-association types, model provenance and real timing/RSS. No
weights or machine-local paths are included. Repetitions replay the same task
judgments and do not multiply independent accuracy samples.

See `docs/SEMANTIC_TASK_EVALUATION.md` for exact methods, limitations and the
reproduction command. Important limits: six test families/twelve correlated
queries, template wording traps, ID tie order, no no-relevance queries, no
external adjudication, no classification/continuation/scope-change accuracy.
