These are public, synthetic solution fixtures for the built-in coding tasks.
`clamp_solution.py` and `duration_solution.py` cover the original two tasks;
`pilot_solutions.py` has hand-written reference implementations for all twelve
versioned pilot tasks. They contain no actual agent transcript or private data.
Tests invoke trusted acceptance only around these controlled local modules; no
agent or paid API is launched. Fixture results use benchmark source kind and
explicit fixture execution origin, never real-agent performance claims.

Pilot integration checks run each independent controller against the public
reference solution, the initial unimplemented module and a wrong numeric-return
module. All 93 named acceptance checks pass for references and fail for each
unimplemented/wrong module. This checks controller suitability on these cases,
not universal correctness, hidden-test secrecy or OS containment.
