# Public task representation rehearsal

`controlled_reference.json` contains actual seed 0–4 reports generated from
`generate_representation_fixture(count=150)` and
`evaluate_task_representation(bootstrap_replicates=300)`, in state-signal and
null-signal scenarios. Fit/score cutoffs are 2026-01-01 04:30 / 07:30 UTC with
30-second checkpoints. Statistics are deterministic; actual timing/RSS fields
naturally vary. Prediction vectors are omitted to keep the reference concise.

The source is simulated. Descriptions are invented public coding objectives,
never raw private transcripts. State is sampled before final outcomes. Six
families per partition are disjoint. A/B labels and features use the existing
controlled simulator; C is explicitly unavailable because no approved local
pretrained model/runtime was present. No fake encoder is used for this artifact.
It establishes neither agent utility nor semantic improvement. Full methodology,
resource measurement caveats and reproduction are in
`docs/CPU_TASK_REPRESENTATION.md`.
