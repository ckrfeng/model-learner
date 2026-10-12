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
