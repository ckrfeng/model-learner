"""Finite, authored synthetic processes establish limits of existing controls.

No agent, model, arbitrary candidate or protected verifier source is executed.
Children self-exit after one second even if their parent is killed. Signals target
only Popen children or a newly created group whose leader has NOT been reaped.
No PID discovery, process-table scan or signaling of detached descendants occurs.
These diagnostics deliberately do not implement a production watchdog.
"""

import os
import selectors
import signal
import subprocess
import sys
import time

import pytest

from model_learner.benchmark.offline import _bounded, _ProbeError

pytestmark = pytest.mark.skipif(os.name != "posix", reason="POSIX process diagnostics")


def _line(process):
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdout, selectors.EVENT_READ)
        assert selector.select(3), "synthetic process did not reach its marker"
        return process.stdout.readline().decode().strip()


def _spawn_tree(*, detached=False, ignore_term=False, parent_exits=False):
    child = (
        "import os, signal, time\n"
        + ("signal.signal(signal.SIGTERM, signal.SIG_IGN)\n" if ignore_term else "")
        + "print('child-ready', os.getpid(), os.getpgrp(), flush=True)\n"
        + "time.sleep(1)\nprint('child-survived', flush=True)\n"
    )
    parent = (
        "import subprocess, sys, time\n"
        f"p = subprocess.Popen([sys.executable, '-I', '-c', {child!r}], "
        f"start_new_session={detached!r}, env={{}})\n"
        + ("sys.exit(0)\n" if parent_exits else "p.wait()\ntime.sleep(2)\n")
    )
    return subprocess.Popen(
        [sys.executable, "-I", "-c", parent],
        start_new_session=True,
        env={},
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=0,
    )


def _finish(process):
    # Popen owns/reaps only its direct child. Finite descendants close the pipe.
    if process.poll() is None:
        process.kill()
    output, _ = process.communicate(timeout=4)
    assert process.returncode is not None
    return output


def _assert_gone(pid):
    """Observe only a known synthetic PID; never signal a discovered process."""
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.01)
    pytest.fail("synthetic PID still observed after bounded cleanup")


def test_existing_bounded_normal_exit_uses_local_monotonic_duration(record_property):
    start = time.monotonic_ns()
    output = _bounded(
        [sys.executable, "-I", "-c", "print('fictional normal exit')"],
        deadline=time.monotonic() + 3,
        env={},
    )
    stop = time.monotonic_ns()
    assert output == b"fictional normal exit\n"
    assert 0 < stop - start < 3_000_000_000
    record_property("local_start_monotonic_ns", start)
    record_property("local_stop_monotonic_ns", stop)
    record_property("external_elapsed_seconds", (stop - start) / 1e9)


def test_existing_bounded_timeout_leaves_a_finite_descendant(tmp_path, record_property):
    marker = tmp_path / "synthetic-child"
    identity = tmp_path / "synthetic-child-pid"
    child = (
        "import os, time\nfrom pathlib import Path\n"
        f"Path({str(identity)!r}).write_text(str(os.getpid()))\n"
        f"p = Path({str(marker)!r})\np.write_text('ready')\n"
        "time.sleep(1)\np.write_text('survived-parent-timeout')\n"
    )
    parent = (
        "import subprocess, sys, time\n"
        f"subprocess.Popen([sys.executable, '-I', '-c', {child!r}], env={{}})\n"
        "time.sleep(2)\n"
    )
    start = time.monotonic_ns()
    try:
        with pytest.raises(_ProbeError, match="wall_deadline_exceeded"):
            _bounded(
                [sys.executable, "-I", "-c", parent],
                deadline=time.monotonic() + 0.4,
                env={},
            )
        stop = time.monotonic_ns()
        assert marker.read_text() == "ready"
        record_property("local_start_monotonic_ns", start)
        record_property("local_stop_monotonic_ns", stop)
        record_property("external_timeout_seconds", (stop - start) / 1e9)
    finally:
        # The fixed child is finite; allow it to finish even on assertion failure.
        time.sleep(1.2)
    assert marker.read_text() == "survived-parent-timeout"
    _assert_gone(int(identity.read_text()))


def test_parent_exit_does_not_close_descendants():
    process = _spawn_tree(parent_exits=True)
    try:
        marker, child_pid, _ = _line(process).split()
        assert marker == "child-ready"
        assert process.wait(timeout=2) == 0
        assert _line(process) == "child-survived"
    finally:
        _finish(process)
    _assert_gone(int(child_pid))


@pytest.mark.parametrize("detached", [False, True], ids=["in-group", "new-session"])
def test_group_kill_reaches_only_members_and_preserves_unrelated_child(
    detached, record_property
):
    process = _spawn_tree(detached=detached, ignore_term=True)
    other = subprocess.Popen(
        [sys.executable, "-I", "-c", "import time; time.sleep(3)"],
        start_new_session=True,
        env={},
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        marker, child_pid, child_group = _line(process).split()
        assert marker == "child-ready"
        assert (int(child_group) != process.pid) is detached
        assert int(child_pid) != process.pid
        # Do not poll/wait/reap the leader before the last group signal: its
        # unreaped PID pins the identity even if SIGTERM has already exited it.
        os.killpg(process.pid, signal.SIGTERM)
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            assert not selector.select(0.05), "child did not ignore graceful stop"
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError) as exc:
            # Some hosts reject signals to a group with only its zombie leader.
            # This is NOT evidence of descendant cleanup. The detached child
            # must still demonstrate survival below. In-group denial fails.
            if not detached:
                raise
            record_property("empty_group_signal_error", type(exc).__name__)
        output, _ = process.communicate(timeout=3)
        assert (b"child-survived" in output) is detached
        assert other.poll() is None
    finally:
        _finish(process)
        _finish(other)
    _assert_gone(int(child_pid))
    _assert_gone(process.pid)
    _assert_gone(other.pid)


def test_duplicate_direct_child_cleanup_is_safe():
    process = subprocess.Popen(
        [sys.executable, "-I", "-c", "import time; time.sleep(2)"],
        env={},
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    _finish(process)
    previous = process.returncode
    _finish(process)
    assert process.returncode == previous
