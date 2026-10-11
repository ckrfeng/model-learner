"""Harmless OS-containment diagnostics, never an agent execution backend.

A successful canary probe is deliberately insufficient to authorize real runs.
The probe exercises only public files it creates itself, never private data.
"""

import json
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from model_learner.domain.models import utc_now

PROBE_VERSION = "macos-canary-probe/v1"
PROBE_TIMEOUT_SECONDS = 5
SANDBOX_EXEC = Path("/usr/bin/sandbox-exec")


class ContainmentProbe(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version: Literal["macos-canary-probe/v1"] = PROBE_VERSION
    status: Literal["probe_passed", "unavailable", "failed"]
    reason: str
    platform: str
    observed_at: str
    exit_code: int | None = None
    permitted_read: bool | None = None
    permitted_write: bool | None = None
    outside_read_denied: bool | None = None
    outside_write_denied: bool | None = None
    symlink_read_denied: bool | None = None
    descendant_read_denied: bool | None = None
    canaries_unchanged: bool | None = None
    # Scope-specific probe results never certify an agent or acceptance runner.
    real_execution_ready: Literal[False] = False


_SCRIPT = """set +e
if IFS= read -r value < "$1/allowed.txt" && [ "$value" = public ]; then
    printf 'permitted_read\n'
fi
if printf 'public\n' > "$1/output.txt"; then printf 'permitted_write\n'; fi
if ! (IFS= read -r value < "$2/private-canary.txt") 2>/dev/null; then
    printf 'outside_read_denied\n'
fi
if ! (printf 'changed\n' > "$2/source-canary.txt") 2>/dev/null; then
    printf 'outside_write_denied\n'
fi
if ! (IFS= read -r value < "$1/outside-link") 2>/dev/null; then
    printf 'symlink_read_denied\n'
fi
if /bin/sh -c 'if (IFS= read -r x < "$1") 2>/dev/null; then exit 1; else exit 0; fi' \
    child "$2/private-canary.txt"; then printf 'descendant_read_denied\n'; fi
"""


def _profile(workspace: Path) -> str:
    # JSON string quoting matches SBPL string escaping for canonical local paths.
    allowed = json.dumps(str(workspace))
    return f"""(version 1)
(deny default)
(allow process-fork)
(allow process-exec (literal "/bin/sh"))
(allow file-read* (literal "/bin/sh") (subpath "/System")
    (subpath "/usr/lib") (subpath {allowed}))
(allow file-write* (subpath {allowed}))
(allow file-read* file-write* (literal "/dev/null"))
(allow sysctl-read)
"""


def probe_macos_containment() -> ContainmentProbe:
    """Try a fixed deny-default shell profile with disposable public canaries.

    Callers can rerun outside an outer sandbox when it rejects sandbox setup.
    A missing bootstrap marker is unavailable, never a successful denied read.
    No arbitrary program/profile/path is accepted and no network is used.
    """
    common = {"platform": platform.platform(), "observed_at": utc_now().isoformat()}
    if platform.system() != "Darwin" or not SANDBOX_EXEC.is_file():
        return ContainmentProbe(
            status="unavailable", reason="macos_sandbox_exec_unavailable", **common
        )
    with tempfile.TemporaryDirectory(prefix="model-learner-containment-") as temp:
        root = Path(temp).resolve()
        workspace, outside = root / "workspace", root / "outside"
        workspace.mkdir()
        outside.mkdir()
        (workspace / "allowed.txt").write_text("public\n")
        canaries = [outside / "private-canary.txt", outside / "source-canary.txt"]
        for path in canaries:
            path.write_text("public synthetic canary\n")
        (workspace / "outside-link").symlink_to(canaries[0])
        try:
            completed = subprocess.run(
                [
                    str(SANDBOX_EXEC),
                    "-p",
                    _profile(workspace),
                    "/bin/sh",
                    "-c",
                    _SCRIPT,
                    "probe",
                    str(workspace),
                    str(outside),
                ],
                cwd=workspace,
                env={},
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=PROBE_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.TimeoutExpired):
            return ContainmentProbe(
                status="unavailable", reason="sandbox_probe_did_not_complete", **common
            )
        markers = set(completed.stdout.decode("ascii", errors="replace").splitlines())
        fields = (
            "permitted_read",
            "permitted_write",
            "outside_read_denied",
            "outside_write_denied",
            "symlink_read_denied",
            "descendant_read_denied",
        )
        results = {field: field in markers for field in fields}
        results["canaries_unchanged"] = all(
            path.read_text() == "public synthetic canary\n" for path in canaries
        )
        # A denied bootstrap cannot establish that any forbidden operation ran.
        if not results["permitted_read"] or not results["permitted_write"]:
            return ContainmentProbe(
                status="unavailable",
                reason="sandbox_bootstrap_unavailable",
                permitted_read=results["permitted_read"],
                permitted_write=results["permitted_write"],
                canaries_unchanged=results["canaries_unchanged"],
                exit_code=completed.returncode,
                **common,
            )
        passed = completed.returncode == 0 and all(results.values())
        return ContainmentProbe(
            status="probe_passed" if passed else "failed",
            reason="canary_checks_passed" if passed else "canary_checks_failed",
            exit_code=completed.returncode,
            **results,
            **common,
        )


def require_supported_real_containment() -> None:
    """Refuse real-run collection until a verified execution backend is supported."""
    raise ValueError(
        "real benchmark collection is blocked: no supported verified containment "
        "backend; an isolation string, operator flag or canary probe is insufficient"
    )
