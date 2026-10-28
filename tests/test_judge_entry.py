"""A judge's real, keyless entry point, in a separate process with no household data or robot access."""

import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import urllib.error
import urllib.request

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def public_demo(tmp_path_factory):
    temp = tmp_path_factory.mktemp("judge-demo")
    protected = temp / "household"
    protected.mkdir()
    sentinel = protected / "untouched.txt"
    sentinel.write_text("invented household sentinel")
    # An allowlist keeps the user's credentials, running-service settings and GPU choices out.
    env = {name: os.environ[name] for name in ("PATH", "LANG", "LC_ALL") if name in os.environ}
    env.update(TMPDIR=str(temp), ANDY_DATA_DIR=str(protected), ANDY_ENV_FILE=str(temp / "missing.env"),
               ANDY_DEMO_PORT="0", ANDY_DEMO_SCENE="found", PYTHONUNBUFFERED="1")
    process = subprocess.Popen([sys.executable, str(ROOT / "scripts/demo_screen.py"), "--public"],
                               cwd=temp, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    first_line = queue.Queue()
    threading.Thread(target=lambda: first_line.put(process.stdout.readline()), daemon=True).start()
    try:
        line = first_line.get(timeout=20)
        match = re.search(r"Start here:\s+(http://127\.0\.0\.1:[1-9][0-9]*)/", line)
        assert match, "The demo did not announce its actual listening address."
        yield match[1]
    finally:
        if process.poll() is None:
            process.terminate()  # only this test's child, never a running Andy service
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        process.stdout.close()
        assert sentinel.read_text() == "invented household sentinel"
        assert sorted(p.name for p in protected.iterdir()) == ["untouched.txt"]
        assert not list(temp.glob("andy-demo-*")), "The demo left its temporary sample data behind."


def request(base, path, body=None):
    req = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        response = urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.code, response.headers, response.read()


def test_public_demo_loads_real_pages_assets_and_sample_data(public_demo):
    code, _, page = request(public_demo, "/")
    assert code == 200 and b"Testing instructions" in page
    assert b"https://github.com/AndyDM9/andy-companion" in page
    assert b"The real robot is in the project's video" not in page
    for path in ("/screen?t=demo-screen", "/hood?t=demo-hood", "/family?k=demo-family", "/setup?s=demo-setup"):
        code, headers, body = request(public_demo, path)
        assert code == 200 and b"<html" in body.lower()
        assert "text/html" in headers["Content-Type"]
        assert headers["Referrer-Policy"] == "no-referrer"
    code, _, hood = request(public_demo, "/api/hood?t=demo-hood")
    assert code == 200 and json.loads(hood)["sample"] is True
    for path in ("/api/screen?t=demo-screen", "/api/family?k=demo-family", "/api/setup?s=demo-setup"):
        code, _, body = request(public_demo, path)
        assert code == 200 and isinstance(json.loads(body), dict)
    for weight in (400, 700):
        code, _, body = request(public_demo, f"/fonts/atkinson-hyperlegible-{weight}.woff2")
        assert code == 200 and body[:4] == b"wOF2"
    code, headers, body = request(public_demo, "/media/sim-search.mp4")
    assert code == 200 and headers["Content-Type"] == "video/mp4" and b"ftyp" in body[:32]


def test_public_demo_refuses_writes_and_does_not_keep_a_visitor_name(public_demo):
    _, _, before = request(public_demo, "/api/family?k=demo-family")
    body = {"name": "Invented visitor", "text": "Invented audit message", "action": "clear-private"}
    for path in ("/api/family/message?k=demo-family", "/api/family/photo?k=demo-family",
                 "/api/family/suggest?k=demo-family", "/api/setup?s=demo-setup",
                 "/api/setup/delete-all?s=demo-setup", "/api/setup/new-family-link?s=demo-setup",
                 "/api/transient?t=demo-screen", "/api/caption?t=demo-screen",
                 "/api/turn?t=demo-screen", "/api/views?t=demo-screen", "/api/screen/settings-code?t=demo-screen"):
        code, _, _ = request(public_demo, path, body)
        assert code == 403, path
    assert request(public_demo, "/api/family/look?k=demo-family", body)[0] == 200
    _, _, after = request(public_demo, "/api/family?k=demo-family")
    assert after == before and b"Invented visitor" not in after


@pytest.mark.parametrize("path", ["/api/setup", "/api/family", "/api/hood?t=demo-screen",
                                      "/api/setup?s=demo-family", "/api/screen?t=wrong",
                                      "/view?t=demo-screen&i=../../etc/passwd"])
def test_demo_does_not_open_private_routes_with_missing_or_wrong_tokens(public_demo, path):
    code, _, body = request(public_demo, path)
    if path.startswith(("/api/setup", "/api/family")):    # the replaced-link words for an open page, and nothing else
        assert code == 410 and set(json.loads(body)) == {"error", "gone"}
    else:
        assert code == 404
