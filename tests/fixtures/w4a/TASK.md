# Transactional Dependency Graph Planner — contract 1

Origin: newly constructed synthetic algorithmic task for W4A, authored offline.
No external benchmark, user repository defect or historical execution was used.
Pre-outcome difficulty: medium-to-hard, based on coupled ordering, transactional
state, error handling and scale requirements. This is an assessment, not a learned
feature or demonstrated discrimination. Familiar graph algorithms may be known to
models; novelty/absence of training contamination cannot be guaranteed.

Implement `planner.py` using only Python 3.12+ standard-library modules. Submit
one regular UTF-8 source file, at most 128 KiB, without local imports, file/network
I/O, subprocesses, threads, plugins or import-time work beyond definitions/imports.
Only `planner.py` is collected for verification. Preserve this public contract.
Public context consists of exactly this file and the starting `planner.py`.
You may run your own local tests during the one attempt. No extra agents, external
sources, network, installation, escalation, retries after closure or later repair.

## Public API

Export `GraphError(ValueError)` and `Planner` with these methods:

| Method | Result |
| --- | --- |
| `Planner()` | New independent empty in-memory graph. |
| `add_node(name)` | Equivalent to `apply([("add_node", name)])`; returns `None`. |
| `remove_node(name)` | Equivalent to `apply([("remove_node", name)])`; returns `None`. |
| `add_dependency(task, prerequisite)` | Equivalent single-operation batch; returns `None`. |
| `remove_dependency(task, prerequisite)` | Equivalent single-operation batch; returns `None`. |
| `apply(operations)` | Atomically apply the entire batch; returns `None`. |
| `nodes()` | Tuple of names in ascending Python string order. |
| `dependencies()` | Tuple of `(task, prerequisite)` tuples, sorted lexicographically. |
| `order()` | Tuple of all nodes in the lexicographically smallest valid topological order. |

An edge `(task, prerequisite)` requires the prerequisite to precede the task.
At each step choose the smallest currently ready name, including newly ready
nodes. This is not sorting by layer or merely returning any topological order.
Disconnected components obey the same global ordering rule. Empty queries return
`()`. Returned tuples are detached snapshots; later changes cannot alter them.
Calls on one instance must never affect another. No persistence is required.

## Inputs, errors and atomicity

Names must be exact built-in `str` values matching ASCII `[A-Za-z0-9_]{1,64}`.
Case matters; no trimming, case folding or Unicode normalization. Invalid names
raise `GraphError`. The batch is an exact built-in `list`; each operation is an
exact built-in `tuple`, with exactly 2 items for node operations or 3 for dependency
operations. The opcode is an exact built-in string, one of the four method names.
Other containers, iterators, unknown opcodes, wrong arity and invalid arguments
raise `GraphError`. Inputs are not mutated or retained by reference. Error message
text is unspecified. Ordinary wrong Python call signatures are outside this API.

Process operations in list order against tentative state. Adding an existing node
or dependency is a successful no-op. Removing an unknown node is an error. Removing
an existing node deletes all its incoming and outgoing dependencies. Both endpoints
of either dependency operation must exist at that point in the batch. Removing an
absent dependency with two existing endpoints is a successful no-op. Self-dependency
addition always raises `GraphError`, even if a later operation would remove it;
removing `(x, x)` for an existing x is an absent-edge no-op.

Check acyclicity on the FINAL tentative graph. Temporary multi-node cycles inside
a batch are allowed if resolved by its end. For example, with edge `(b,a)`, adding
`(a,b)` then removing `(b,a)` succeeds and reverses the edge. An intermediate
unknown node, malformed operation or self-add is still invalid immediately. If
any operation is invalid or the final graph is cyclic, raise `GraphError` and
leave the entire prior state unchanged. The empty batch succeeds without changes.
Single-operation methods have the same atomicity. Queries never mutate state.
After a failure the same instance must remain usable for subsequent operations.

## Scale and acceptance

Support graphs through 8,000 nodes / 24,000 dependencies and batches through
32,000 operations, plus repeated small updates. No behavior above these sizes is
specified. Avoid recursion-depth failure on long chains. Full recomputation is
permitted; no particular data structure or incremental algorithm is mandated.

Acceptance includes exact examples, boundaries, compound transitions, rollback,
cycles, repeated operations, exhaustive small graphs, seeded differential checks
against a separate small-graph oracle, metamorphic checks and deterministic replay.
All required tests must execute with no skips and pass on the exact final file.
An incomplete report, tampering, timeout or infrastructure failure is indeterminate,
not an invented task failure; a complete failing acceptance report is failure.

The fixed performance workload builds an 8,000-node chain and a 2,000-node wide
DAG with 24,000 dependencies and 20 small reversible updates. Three fresh-instance trials are run;
median process CPU time must be <= 10.0 s and every trial <= 20.0 CPU s. A separate
30 s wall watchdog per trial is an infrastructure ceiling; a wall timeout alone
is indeterminate. No timing retries or threshold changes after model outcomes.
Before any measured run, calibrate the trusted reference on the SAME isolated
runtime: all three reference trials must be <= 2.0 CPU s, otherwise suspend the
cohort and review environment/contract version before forecasting. Warm imports,
exclusive single-worker execution, fixed interpreter and identical environment
apply to all arms. Report all three times. W4A host calibration does not establish
future isolated-runtime calibration.
