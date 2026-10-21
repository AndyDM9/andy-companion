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

import pytest  # noqa: E402


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
