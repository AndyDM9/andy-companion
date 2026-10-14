"""No key or token on a command line in the cloud scripts: a command line is readable by every process on a
shared computer (`ps`, /proc), the same reason the voice server takes its key from the environment
(review, 2026-10-14). Keys travel on a pipe into a 0600 request file (cloud/secret.sh) or as Nebius secrets."""

import re
from pathlib import Path

import pytest

CLOUD = Path(__file__).resolve().parents[1] / "cloud"
SCRIPTS = ("suite-job.sh", "vision-endpoint.sh", "guard-endpoint.sh", "secret.sh")

# The only lines allowed to mention a secret's variable: making it, checking it is there, writing it into a
# pipe with the shell's own printf, or saving it to the private env file with the scripts' save function.
ALLOWED = (
    r'^\s*TOKEN="\$\(openssl rand -hex 32\)"$',
    r"""^\s*KEY="\$\(sed -n 's/\^NEBIUS_API_KEY=//p' "\$ENV_FILE" \| tail -1\)"$""",
    r'^\s*\[ -n "\$KEY" \] \|\|',
    r"""^\s*printf '%s' "\$(TOKEN|KEY)" \| store_secret """,
    r'^\s*save ANDY_(VISION|GUARD)_TOKEN "\$TOKEN"$',
)


@pytest.mark.parametrize("name", SCRIPTS)
def test_no_secret_is_passed_as_an_argument(name):
    for line in (CLOUD / name).read_text().splitlines():
        if line.lstrip().startswith("#"):
            continue
        if re.search(r"\$\{?(TOKEN|KEY|PAYLOAD)\b", line):
            assert any(re.search(p, line) for p in ALLOWED), f"{name}: {line.strip()}"
    text = "\n".join(line for line in (CLOUD / name).read_text().splitlines() if not line.lstrip().startswith("#"))
    for risky in ("--api-key", '--token "', "--secret-version-payload", "--payload ", "sys.argv[1]}]"):
        assert risky not in text, f"{name}: {risky}"


@pytest.mark.parametrize("name, served", [("vision-endpoint.sh", "nemotron-vl"), ("guard-endpoint.sh", "nemotron-guard")])
def test_endpoints_take_their_token_from_nebius_secrets(name, served):
    text = (CLOUD / name).read_text()
    assert f"--served-model-name {served}" in text
    # Nebius checks the token at the HTTPS address; vLLM reads VLLM_API_KEY in place of --api-key.
    assert '--auth token --token-secret "$NAME-auth"' in text
    assert '--env-secret "VLLM_API_KEY=$NAME-vllm"' in text
    assert 'store_secret "$NAME-auth" AUTH_TOKEN' in text and 'store_secret "$NAME-vllm" VLLM_API_KEY' in text


def test_the_suite_job_key_reaches_the_secret_store_through_a_pipe():
    text = (CLOUD / "suite-job.sh").read_text()
    assert '. "$ROOT/cloud/secret.sh"' in text and '--env-secret "NEBIUS_API_KEY=$SECRET"' in text
    helper = (CLOUD / "secret.sh").read_text()
    assert "sys.stdin.read()" in helper and '--file "$req"' in helper
    assert "umask 077; mktemp" in helper and "rm -f" in helper and "trap" in helper


def test_store_secret_writes_an_owner_only_request_and_removes_it(tmp_path):
    """Run store_secret with a stand-in `nebius` that records the request file it was handed."""
    import os
    import stat
    import subprocess

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    seen = tmp_path / "seen"
    fake = bin_dir / "nebius"
    fake.write_text(f"""#!/bin/sh
case "$*" in
  *get-by-name*) exit 1 ;;
  *"config get"*) echo project-1 ;;
  *--file*) f="$(echo "$*" | sed 's/.*--file //')"; stat -c %a "$f" > {seen}.mode; cat "$f" > {seen}.json;
            echo "$*" > {seen}.args ;;
esac
""")
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    out = subprocess.run(["bash", "-c", f'. "{CLOUD / "secret.sh"}"; printf "%s" "s3cr3t-value" | '
                                        'store_secret andy-test AUTH_TOKEN "A test"'],
                         capture_output=True, text=True, env={**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"},
                         timeout=30)
    assert out.returncode == 0, out.stderr
    assert "Secret andy-test stored." in out.stdout and "s3cr3t" not in out.stdout + out.stderr
    assert (tmp_path / "seen.mode").read_text().strip() == "600"
    assert "s3cr3t" not in (tmp_path / "seen.args").read_text()
    import json

    request = json.loads((tmp_path / "seen.json").read_text())
    assert request["metadata"] == {"name": "andy-test", "parent_id": "project-1"}
    assert request["spec"]["secret_version"]["payload"] == [{"key": "AUTH_TOKEN", "string_value": "s3cr3t-value"}]
    request_file = (tmp_path / "seen.args").read_text().split("--file ")[1].strip()
    assert not Path(request_file).exists()
