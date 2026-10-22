# Signal Note configuration repair — v1

Task ID: `w4b-p0-signal-note`; task version: `1`.
Origin: synthetically constructed for this offline preparation, no real project
or historical conversation. A later actual model execution is a real run on a
synthetic task, not evidence about naturally occurring repository work.

You receive this instruction and one starting file, `pyproject.toml`. Repair only
that file for a fictional standalone Python project. Do not create source code,
lockfiles, reports, tests or other outputs. Do not install, build, import the
project, invoke a package manager, run candidate code or use the network. The
operator will parse the final TOML independently; executable behavior is outside
this task. The CLI target and package path are configuration declarations, not
claims that corresponding source files exist.

The accepted artifact is a UTF-8 TOML regular file of at most 8,192 bytes. No
symlink (including parent components), duplicate definitions, extra fields or
tables, dynamic metadata, conflicting alternate configuration or malformed
requirements are accepted. Formatting and comments may change. Array order is
fixed below; this deliberately finite contract accepts only the listed values.

Set exactly these fields:

| Table | Required values |
| --- | --- |
| `project` | `name = "signal-note"`, `version = "0.2.0"`, `description = "Fictional offline note formatter."`, `requires-python = ">=3.12,<3.14"`, `dependencies = []` |
| `build-system` | `requires = ["hatchling>=1.27,<2"]`, `build-backend = "hatchling.build"` |
| `project.scripts` | `signal-note = "signal_note.cli:main"` |
| `project.optional-dependencies` | `dev = ["pytest>=8,<9", "ruff>=0.12,<1"]` |
| `tool.hatch.build.targets.wheel` | `packages = ["src/signal_note"]` |
| `tool.ruff` | `target-version = "py312"`, `line-length = 88` |
| `tool.ruff.lint` | `select = ["E", "F", "I", "UP", "B"]` |
| `tool.ruff.format` | `quote-style = "double"`, `indent-style = "space"` |

Preserve the complete parsed `tool.signal_note` table and its nested `labels`
from the start, with exact keys, values and types: `default_style = "compact"`,
`retention_days = 7`, labels `team = "fictional"`, `channel = "local"`.
No other tables/keys are allowed. In particular preserve the package name,
description and empty runtime dependencies; the version and Python constraint
are intentional changes. Key/table ordering is unrestricted.

Frozen data acceptance: `w4b-p0-signal-note-data`, version `1`, all nine
`w4b_p0_v1::*` cases listed in the pre-run manifest must pass with no skips.
The operator controls the checker and report outside your workspace. Do not
supply verification claims. Completion is separate from acceptance.
