# J1 fictional task-intent v1

All 24 descriptions and reference labels were newly authored for this increment.
No personal task, history, execution, source locator or private evidence was used.
The 8 development and 16 holdout inputs, labels, splits and hashes are frozen by
`manifest.json`; the loader pins its digest. These are **authored reference labels
awaiting independent human review**, not human gold or real model evidence.
Unknown binary references are null and excluded with explicit denominators.

The baseline/rubric/questions/metrics freeze precedes all holdout prediction.
No baseline or mock prediction is collected for holdout. Authorship and public
label storage do not provide organizational blinding: future collectors must use
only input projections and avoid consulting reference labels before predictions
are frozen. Labels never enter serialized local requests. Questions, labels or
baseline changes after holdout predictions require a new evaluation version and
future untouched holdout; do not overwrite this version to claim improvement.

The local fixture transport/parser do not implement the official Decisions schema;
that captured schema and the provider slug remain missing. No difficulty target
exists. A fictional score control tests a local parser only. Mock results establish
plumbing, never Jev accuracy/calibration. With 16 holdout tasks, any future result
is exploratory. See `docs/J1_OFFLINE_INTENT.md` for limits and live blockers.
