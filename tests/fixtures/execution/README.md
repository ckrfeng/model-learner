# Controlled execution-analysis examples

All files in this directory are synthetic, sanitized examples. They are not real
agent executions, coding outcomes, benchmarks, or training observations.

`controlled_capture.jsonl` uses the supported metadata-only Codex CLI capture
envelope. It contains one nonzero command exit, two distinct failed invocations of
the same named MCP tool, a command exit zero, a command with an unknown exit code,
and a completed turn. Commands, arguments, output, and error text are absent.
Receipt times are designed fixture timestamps; integration tests declare ingestion
availability one second after each receipt.

The XML files resemble pytest JUnit output and declare the same two tests, with
one failure followed by all passing. Integration tests bind both reports to one
fixed artifact snapshot with explicit operator receipts. This demonstrates
observable report changes, not code-edit attribution or a claim that actual code
was fixed. XML timing fields are not used as agent execution duration.
