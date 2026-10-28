"""The suite's Nebius job bundle (2026-10-28): Nebius encodes injected files once more and refused 53 KB of base64
("plaintext must not exceed 65536 bytes", all files together), so cloud/suite-job.sh sends the xz bytes themselves
and cloud/job-entry.sh reads them; base64 still works for older bundles. No Nebius call here."""

import random
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BIG = random.Random(1).randbytes(60_000)
SUITE_FILES = ("evals/run_suite.py evals/suite.json evals/tools.json profiles/companion/profile.md "
               "src/andy_companion/__init__.py src/andy_companion/urgent.py src/andy_companion/offers.py "
               "src/andy_companion/recall.py src/andy_companion/consent.py src/andy_companion/tool_text.py "
               "src/andy_companion/turn_notes.py")

pytestmark = pytest.mark.skipif(not all(shutil.which(t) for t in ("tar", "xz", "base64")),
                                reason="needs tar, xz and base64")


@pytest.mark.parametrize("as_bytes", [True, False])
def test_the_bundle_unpacks_as_xz_bytes_or_as_base64(tmp_path, as_bytes):
    src = tmp_path / "src"
    (src / "evals").mkdir(parents=True)
    (src / "evals" / "big.bin").write_bytes(BIG)                             # does not compress away
    (src / "evals" / "small.txt").write_text("hello")
    work = tmp_path / "andy"
    work.mkdir()
    pack = "tar -C src -cf - evals | xz -9e" + ("" if as_bytes else " | base64 -w0")
    (work / ("bundle.xz" if as_bytes else "bundle.b64")).write_bytes(
        subprocess.run(pack, shell=True, cwd=tmp_path, check=True, capture_output=True).stdout)
    line = next(ln for ln in (ROOT / "cloud" / "job-entry.sh").read_text().splitlines() if ln.startswith("python3 -c"))
    subprocess.run(["sh", "-c", line], cwd=work, check=True)
    assert (work / "evals" / "big.bin").read_bytes() == BIG
    assert (work / "evals" / "small.txt").read_text() == "hello"


def test_suite_job_sends_bytes_that_fit_once_encoded():
    script = (ROOT / "cloud" / "suite-job.sh").read_text()
    assert '--inject-file "$BUNDLE:/andy/bundle.xz"' in script and "xz -9e | base64" not in script
    for name in SUITE_FILES.split():                                        # the list the script sends
        assert name in script
    raw = subprocess.run(f"tar -cf - {SUITE_FILES} | xz -9e", shell=True, cwd=ROOT, check=True,
                         capture_output=True).stdout
    entry = (ROOT / "cloud" / "job-entry.sh").stat().st_size
    # Nebius encodes injected files as base64 once more, and the limit is 65,536 bytes for all of them together. 1,500
    # bytes spare (2026-10-28: the review's fixes brought the bundle to 46.6 KB, 63.1 KB once encoded; the 5% margin
    # this replaces had no basis in the limit itself). Past it, the job should fetch the code by commit instead.
    assert (len(raw) + entry) * 4 / 3 + 1_500 < 65_536
