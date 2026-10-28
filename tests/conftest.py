"""Every test runs against a throwaway data folder, set before Andy's modules are imported.

Each test still points the files it uses at its own tmp_path; this is the net under them, so a test
that forgets can never write a reminder, a setting or a card on the screen into the real Andy's data
(~/.local/share/andy-companion) while Andy is running beside the tests.
"""

import atexit
import os
import shutil
import tempfile

os.environ["ANDY_DATA_DIR"] = tempfile.mkdtemp(prefix="andy-tests-")
atexit.register(shutil.rmtree, os.environ["ANDY_DATA_DIR"], True)   # removed when the run ends

# Git's own repository variables, which the pre-commit hook passes to the tests: from a linked worktree GIT_DIR is an
# absolute path, so the fixtures' `git -C <tmp>` init, commit, tag and config reached the real repository instead of
# their throwaway ones (2026-10-28: test commits on the branch, a release tag, a fixture identity and core.bare=true in
# the shared config). Every git a test runs works on the folder it names.
for _name in [*os.environ]:
    if _name in ("GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
                 "GIT_OBJECT_DIRECTORY", "GIT_DIR", "GIT_WORK_TREE", "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE",
                 "GIT_INDEX_FILE", "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX", "GIT_SHALLOW_FILE",
                 "GIT_COMMON_DIR") or _name.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")):
        del os.environ[_name]

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _private_transient_state(monkeypatch):
    from andy_companion import board, consent, transient
    monkeypatch.setattr(transient, "owner", True)
    monkeypatch.setattr(board, "_screen", None)
    monkeypatch.setattr(board, "_research", [])
    monkeypatch.setattr(board, "_generation", 0)
    monkeypatch.setattr(consent, "_default", consent.Confirmation())


@pytest.fixture(autouse=True)
def _forget_last_seen_places():
    """Where Andy last saw things lives in memory (places._last_seen): never carried from one test to the next."""
    from andy_companion import places

    places._last_seen.clear()
    yield
    places._last_seen.clear()


@pytest.fixture(autouse=True)
def _forget_what_andy_is_looking_at():
    """What the head is turned to (body.looking_at) lives in memory for a few seconds: never carried between tests,
    whatever order or speed they run in."""
    from andy_companion.body import looking_at

    looking_at.clear()
    yield
    looking_at.clear()
