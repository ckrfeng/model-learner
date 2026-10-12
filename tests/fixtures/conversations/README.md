# Controlled conversation history

`history.json` is a synthetic, sanitized example of the installed App Server
`thread/read` and `thread/turns/list` response shapes. Its three turns, IDs, times,
messages and sentinel values were authored for tests. It contains no original
test-conversation content. Tests use both validated originators, reverse one-turn
pages, and check exact Unicode, whitespace and multiline text retention.

`app_server.py` is a fake stdio peer for offline transport and CLI integration
tests. It never launches Codex or invokes a model. Special test modes exercise
errors, unsolicited requests, malformed envelopes and byte/time limits.
