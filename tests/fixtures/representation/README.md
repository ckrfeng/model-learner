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

`potion_reference.json` adds actual pretrained CPU C results for the same ten
cohorts and settings, with `minishlab/potion-base-8M` pinned to
`bf8b056651a2c21b8d2565580b8569da283cab23`. Original A/B statistics and cohort hashes
match exactly; `controlled_reference.json` is unchanged. This new artifact uses
the real approved model, never a fake encoder. Ten fresh socket-blocked workers
measure model load, inference, serial latency and whole-process peak RSS. Timing
varies; scores, calibration and bootstrap intervals are reproducible. Per-seed
predictions are omitted from both artifacts. No raw descriptions or weights are
stored in reports; public inputs are regenerated deterministically. No consistent
C improvement or real-world task-understanding claim follows from these fixtures.
