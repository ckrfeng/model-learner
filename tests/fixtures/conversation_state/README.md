# Authored conversation-state fixtures

All inputs and reference outputs are simulated, authored public fixtures, not
copies, excerpts or derivatives of either selected real conversation.

- `demo.json`: standalone end-to-end CPU timeline with an explicitly simulated
  independent acceptance sidecar. Its verified checkpoint is synthetic evidence.
- `evaluation.json`: 52 separated NB training examples; 23 evaluation conversations,
  54 hand-specified intent labels and final-state signatures. Labels were supplied
  by the implementing agent before first execution, not independently by humans.
- `reference.json`: actual final evaluation output, with volatile timings removed.

This became a diagnostic regression set during rule debugging. It is not an
untouched holdout and cannot establish generalization. See
`docs/CONVERSATION_TASK_STATE.md` for metrics, errors, labeling limits and privacy.

## Independent synthetic holdout increment

- `frozen_v1/`: original source/evaluator/configuration digests and untouched
  diagnostic fixture/reference. Replay the archive with the frozen loader; its
  evaluator imports must be explicitly bound to the frozen backend (tested).
- `holdout_v1.json`: 12 prediction-blind independently agent-authored cases,
  63 messages / 85 reference events, frozen before baseline execution.
- `holdout_v1_baseline.json`: original pre-change result, retained with its initial
  scorer defect. `holdout_v1_baseline_audited.json` corrects target-edge accounting
  and adds artifact-sensitive measurements without changing predictions or labels.
- `holdout_v1_revised.json`: diagnostic rerun after two bounded corrections.
- `revision_v1_manifest.json`: revised-rule hash frozen before untouched examples
  were authored. No further tuning occurred.
- `post_holdout_v1.json`: 8 untouched cases, 38 messages / 46 reference events,
  authored independently after the rule revision was frozen.
- `scope_reversal_holdout_v1.json`: separately frozen untouched coverage supplement,
  1 case / 6 messages / 8 events, removes then reinstates the same requirement.
- Each new dataset has a freeze manifest and baseline/revised reports. Missing
  denominators are null; every source and check is simulated. The initial scorer
  digest and final reviewed scorer digest are distinct in the first manifest.

Labels are prediction-blind agent judgments, not independent human ground truth.
Frozen references include documented policy disputes; they are not relabeled
after execution. See `docs/CONVERSATION_TASK_STATE_HOLDOUT.md` for results,
failures, scorer artifacts, reproduction and the next-step recommendation.
