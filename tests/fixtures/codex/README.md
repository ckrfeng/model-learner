# Codex fixture provenance

- `exec_capture.jsonl`: synthetic metadata-only envelopes based on the official
  Codex non-interactive JSONL schema. Tool, error, and unknown-event scenarios
  provide coverage beyond the minimal real smoke test. Identities, usage, and
  times are synthetic.
- `real_smoke_capture.jsonl`: metadata-only derivative of an actual local
  `codex-cli 0.162.0-alpha.17.2` read-only smoke run on macOS arm64, 2026-10-10.
  The approved prompt requested a literal response without tools or file edits.
  Thread and capture identities and receipt times are sanitized replacements;
  token counts retain the measured values. Native stdout was buffered before
  receipt envelopes were created, so no execution latency is represented.
  Message content was removed before fixture preparation. No task outcome or
  verified label is claimed.

Source: https://learn.chatgpt.com/docs/non-interactive-mode
