"""Exporter checks with invented releases and loopback HTTP fixtures; no external network or hardware."""

import importlib.util
import http.client
import io
import json
from pathlib import Path
import re
import subprocess
import threading
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("devpost_for_tests", ROOT / "scripts" / "devpost.py")
devpost = importlib.util.module_from_spec(spec)
spec.loader.exec_module(devpost)


def test_the_form_fields_come_from_the_submission_text():
    f = devpost.fields((ROOT / "docs" / "submission.md").read_text())
    assert f["Project name"] == "Hey Andy"
    assert 0 < len(f["Tagline"]) <= 200 and not f["Tagline"].startswith("(")
    tags = [t for t in f["Built with"].split(",") if t.strip()]
    assert 0 < len(tags) <= 25
    testing = f["Testing instructions"]
    assert "no connected" in testing and "do not" in testing and "purchase credits" in testing
    assert "robot" in testing and "organisers" in testing
    story = f["About the project"]
    assert story.startswith("## For the judges") and "\n### " not in story          # Devpost's own heading level
    for heading in ("Inspiration", "What it does", "How we built it", "Challenges we ran into",
                    "Accomplishments that we're proud of", "What we learned", "What's next for Andy"):
        assert f"## {heading}" in story, heading


def test_a_draft_points_its_evidence_at_a_ref_that_exists():
    text = "[x](https://github.com/AndyDM9/andy-companion/blob/hackathon-submission/evals/results/a.json)"
    assert devpost.at_ref(text, "main") == "[x](https://github.com/AndyDM9/andy-companion/blob/main/evals/results/a.json)"
    assert devpost.links(devpost.at_ref(text, "main")) == ["https://github.com/AndyDM9/andy-companion/blob/main/evals/results/a.json"]


@pytest.mark.parametrize("status,blocked", [(404, False), (403, True)])
def test_failed_citations_stay_failed_and_a_404_is_not_excused_as_blocking(monkeypatch, capsys, status, blocked):
    monkeypatch.setattr(devpost, "opens", lambda url: status if "ftc.gov" in url else 200)
    assert devpost.main(["--check"]) == 1
    report = capsys.readouterr().err
    ftc_url = next(u for u in devpost.links((ROOT / "docs/submission.md").read_text()) if "ftc.gov" in u)
    assert f"{status}  {ftc_url}" in report
    assert ("an FTC request was blocked" in report) == blocked


@pytest.fixture
def release_tree(tmp_path):
    root = tmp_path / "release"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                    "commit", "--allow-empty", "-qm", "test release"], check=True, capture_output=True)
    (root / "reachy_app").mkdir()
    (root / "reachy_app/pyproject.toml").write_text(
        '[project]\ndependencies = ["andy-companion[robot] @ git+https://github.com/AndyDM9/andy-companion@main"]\n')
    return root


def commit_release(root):
    subprocess.run(["git", "-C", str(root), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                    "commit", "-qm", "final files"], check=True, capture_output=True)


def test_final_export_blocks_a_draft_before_printing_or_network(release_tree, monkeypatch, capsys):
    (release_tree / "docs").mkdir()
    source = (ROOT / "docs/submission.md").read_text()
    source = re.sub(r"^- \*\*Video:\*\*.*$", "- **Video:** *[the YouTube link]*", source, flags=re.M)
    (release_tree / "docs/submission.md").write_text(source)
    monkeypatch.setattr(devpost, "ROOT", release_tree)
    monkeypatch.setattr(devpost, "opens", lambda url: pytest.fail("An incomplete final export should stop before networking"))
    monkeypatch.setattr(devpost, "published_release_problems", lambda root: pytest.fail("Local gaps must stop before public metadata checks"))
    assert devpost.main(["--ref", "hackathon-submission", "--final"]) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "Video placeholder" in output.err and "Pin the app" in output.err


def test_final_export_also_checks_public_links_after_local_release_checks(release_tree, monkeypatch, capsys):
    (release_tree / "docs").mkdir()
    source = (ROOT / "docs/submission.md").read_text()
    source = re.sub(r"^- \*\*Video:\*\*.*$", "- **Video:** https://youtu.be/abcdefghijk", source, flags=re.M)
    (release_tree / "docs/submission.md").write_text(source)
    (release_tree / "docs/feedback.md").write_text("# Feedback\nInvented feedback.\n")
    app = release_tree / "reachy_app/pyproject.toml"
    app.write_text(app.read_text().replace("@main", "@hackathon-submission"))
    commit_release(release_tree)
    subprocess.run(["git", "-C", str(release_tree), "tag", "hackathon-submission"], check=True, capture_output=True)
    monkeypatch.setattr(devpost, "ROOT", release_tree)
    monkeypatch.setattr(devpost, "published_release_problems", lambda root: [])
    checked = []

    def opens(url):
        checked.append(url)
        return 404 if "/blob/hackathon-submission/" in url else 200

    monkeypatch.setattr(devpost, "opens", opens)
    assert devpost.main(["--ref", "hackathon-submission", "--final"]) == 1
    assert any("/blob/hackathon-submission/" in url for url in checked)
    output = capsys.readouterr()
    assert "404" in output.err and output.out == ""


def test_real_release_tag_and_app_pin_are_required(release_tree):
    form = {"Video": "https://youtu.be/abcdefghijk", "Tagline": "An invented tagline", "Built with": "python"}
    problems = devpost.final_problems(form, "hackathon-submission", release_tree)
    assert any("missing locally" in p for p in problems) and any("Pin the app" in p for p in problems)
    (release_tree / "docs").mkdir()
    (release_tree / "docs/submission.md").write_text("Invented final submission.\n")
    (release_tree / "docs/feedback.md").write_text("Invented final feedback.\n")
    app = release_tree / "reachy_app/pyproject.toml"
    app.write_text(app.read_text().replace("@main", "@hackathon-submission"))
    commit_release(release_tree)
    subprocess.run(["git", "-C", str(release_tree), "tag", "hackathon-submission"], check=True, capture_output=True)
    assert devpost.final_problems(form, "hackathon-submission", release_tree) == []
    assert any("Use --ref" in p for p in devpost.final_problems(form, "main", release_tree))


@pytest.mark.parametrize("change", ["tracked", "staged", "new_commit", "untracked_input"])
def test_final_export_rejects_files_that_are_not_in_its_tag(release_tree, change):
    form = {"Video": "https://youtu.be/abcdefghijk", "Tagline": "Invented", "Built with": "python"}
    docs = release_tree / "docs"
    docs.mkdir()
    (docs / "submission.md").write_text("Invented final submission.\n")
    (docs / "feedback.md").write_text("Invented final feedback.\n")
    app = release_tree / "reachy_app/pyproject.toml"
    app.write_text(app.read_text().replace("@main", "@hackathon-submission"))
    runtime = release_tree / "runtime.py"
    runtime.write_text("# Invented version one\n")
    if change == "untracked_input":
        # Even otherwise clean exports must not accept required files absent from the snapshot.
        subprocess.run(["git", "-C", str(release_tree), "tag", "hackathon-submission"], check=True, capture_output=True)
    else:
        commit_release(release_tree)
        subprocess.run(["git", "-C", str(release_tree), "tag", "hackathon-submission"], check=True, capture_output=True)
        assert devpost.final_problems(form, "hackathon-submission", release_tree) == []
        runtime.write_text("# Invented version two\n")
        if change == "staged":
            subprocess.run(["git", "-C", str(release_tree), "add", "runtime.py"], check=True, capture_output=True)
        elif change == "new_commit":
            commit_release(release_tree)
    assert any("working files differ" in p for p in devpost.final_problems(form, "hackathon-submission", release_tree))


@pytest.mark.parametrize("url", ["*[the YouTube link]*", "https://youtube.com/", "https://youtube.com/watch?v=TODO",
                                 "https://youtube.com/playlist?list=abcdefghijk", "https://youtube.com.evil.example/watch?v=abcdefghijk",
                                 "http://youtu.be/abcdefghijk", "https://[broken"])
def test_placeholders_and_nonvideo_links_are_not_final_video_urls(url):
    assert not devpost.youtube_video(url)


@pytest.mark.parametrize("url", ["https://youtu.be/abcdefghijk", "https://www.youtube.com/watch?v=abcdefghijk&t=1s",
                                 "[Video](https://www.youtube.com/watch?v=abcdefghijk)"])
def test_real_video_url_shapes_are_accepted_without_claiming_they_are_public(url):
    assert devpost.youtube_video(url)


@pytest.fixture
def ready_release(release_tree):
    """Invented release files only, with a real local Git snapshot; no actual release tag is changed."""
    (release_tree / "docs").mkdir()
    (release_tree / "docs/submission.md").write_text(
        "# Submission\n## Form fields\n- **Project name:** Invented\n- **Video:** https://youtu.be/abcdefghijk\n"
        "- **Tagline:** Invented release\n- **Built with:** python\n## The story\nInvented story.\n")
    (release_tree / "docs/feedback.md").write_text("# Feedback\nInvented feedback.\n")
    app = release_tree / "reachy_app/pyproject.toml"
    app.write_text(app.read_text().replace("@main", "@hackathon-submission"))
    commit_release(release_tree)
    subprocess.run(["git", "-C", str(release_tree), "tag", "hackathon-submission"], check=True, capture_output=True)
    return release_tree


def release_commit(root):
    return subprocess.check_output(["git", "-C", str(root), "rev-parse", "refs/tags/hackathon-submission^{commit}"], text=True).strip()


@pytest.mark.parametrize("manifest", ["project = []\n", 'project = "invented"\n',
    '[project]\ndependencies = "PIN"\n', '[project]\ndependencies = [12, "PIN"]\n',
    '[project]\ndependencies = {}\n'])
def test_a_string_or_wrong_shaped_dependency_list_cannot_satisfy_the_app_pin(ready_release, manifest):
    app = ready_release / "reachy_app/pyproject.toml"
    app.write_text(manifest.replace("PIN", f"andy-companion[robot] @ git+{devpost.REPO}@hackathon-submission"))
    commit_release(ready_release)
    subprocess.run(["git", "-C", str(ready_release), "tag", "-f", "hackathon-submission"], check=True, capture_output=True)
    form = {"Video": "https://youtu.be/abcdefghijk", "Tagline": "Invented", "Built with": "python"}
    problems = devpost.final_problems(form, "hackathon-submission", ready_release)
    assert len(problems) == 1 and "Pin the app" in problems[0]


def public_ref(sha, kind="commit"):
    return {"ref": "refs/tags/hackathon-submission", "object": {"type": kind, "sha": sha}}


@pytest.mark.parametrize("annotated", [False, True])
def test_public_tag_resolves_lightweight_and_annotated_refs_without_trusting_urls(monkeypatch, annotated):
    calls = []
    tag_sha, commit_sha = "a" * 40, "b" * 40

    def read(url):
        calls.append(url)
        data = public_ref(tag_sha, "tag") if annotated and len(calls) == 1 else public_ref(commit_sha)
        if len(calls) == 2:
            data["sha"] = tag_sha
        data["object"]["url"] = "https://invented.invalid/do-not-follow"
        return json.dumps(data).encode()

    monkeypatch.setattr(devpost, "_public_bytes", read)
    assert devpost.published_tag_commit() == commit_sha
    expected = [f"{devpost.PUBLIC_API}/git/ref/tags/hackathon-submission"]
    if annotated:
        expected.append(f"{devpost.PUBLIC_API}/git/tags/{tag_sha}")
    assert calls == expected


@pytest.mark.parametrize("data", [[], None, {}, {"ref": "refs/heads/hackathon-submission"},
    {"ref": "refs/tags/hackathon-submission", "object": []}, public_ref("invalid"),
    public_ref("c" * 40, "tree"), public_ref("c" * 40, "blob"), public_ref(10)])
def test_wrong_public_ref_or_object_schema_cannot_approve_release(monkeypatch, data):
    monkeypatch.setattr(devpost, "_public_bytes", lambda url: json.dumps(data).encode())
    with pytest.raises(ValueError):
        devpost.published_tag_commit()


@pytest.mark.parametrize("mode", ["wrong-object", "cycle", "too-deep", "missing-object"])
def test_annotated_tag_resolution_is_consistent_and_bounded(monkeypatch, mode):
    calls = []

    def read(url):
        calls.append(url)
        if len(calls) == 1:
            return json.dumps(public_ref("a" * 40, "tag")).encode()
        if mode == "missing-object":
            raise urllib.error.HTTPError(url, 404, "invented private error", {}, None)
        requested = url.rsplit("/", 1)[-1]
        following = requested if mode == "cycle" else f"{len(calls):040x}"
        return json.dumps({"sha": "wrong" if mode == "wrong-object" else requested,
                           "object": {"type": "tag", "sha": following}}).encode()

    monkeypatch.setattr(devpost, "_public_bytes", read)
    with pytest.raises((ValueError, urllib.error.HTTPError)):
        devpost.published_tag_commit()
    assert len(calls) <= devpost.MAX_TAG_DEPTH + 1


@pytest.mark.parametrize("status", [404, 403, 429, 500])
def test_only_missing_reference_404_is_treated_as_an_absent_public_tag(monkeypatch, status):
    def read(url):
        raise urllib.error.HTTPError(url, status, "invented private error", {}, None)

    monkeypatch.setattr(devpost, "_public_bytes", read)
    if status == 404:
        assert devpost.published_tag_commit() is None
    else:
        with pytest.raises(urllib.error.HTTPError):
            devpost.published_tag_commit()


@pytest.mark.parametrize("failure", [TimeoutError("invented private error"), ValueError("invented private error"),
                                     urllib.error.URLError("invented private error"), RecursionError("invented private error"),
                                     http.client.BadStatusLine("invented private error")])
def test_public_lookup_failure_is_fixed_non_echoing_and_blocks_export(ready_release, monkeypatch, capsys, failure):
    monkeypatch.setattr(devpost, "ROOT", ready_release)

    def read(url):
        raise failure

    monkeypatch.setattr(devpost, "_public_bytes", read)
    monkeypatch.setattr(devpost, "opens", lambda url: pytest.fail("A failed release check must stop before citation checks"))
    assert devpost.main(["--final", "--ref", "hackathon-submission"]) == 2
    output = capsys.readouterr()
    assert output.out == "" and "could not be verified" in output.err and "invented private error" not in output.err


def test_a_different_public_commit_cannot_pass_even_when_all_pages_would_return_200(ready_release, tmp_path, monkeypatch, capsys):
    # A real bare fixture keeps the old tag while the local release is moved to newer committed files.
    remote = tmp_path / "published.git"
    subprocess.run(["git", "clone", "--bare", "-q", str(ready_release), str(remote)], check=True, capture_output=True)
    old = release_commit(ready_release)
    (ready_release / "docs/feedback.md").write_text("# Feedback\nInvented newer snapshot.\n")
    commit_release(ready_release)
    subprocess.run(["git", "-C", str(ready_release), "tag", "-f", "hackathon-submission"], check=True, capture_output=True)
    assert old != release_commit(ready_release)
    assert subprocess.check_output(["git", "--git-dir", str(remote), "rev-parse", "refs/tags/hackathon-submission"], text=True).strip() == old
    monkeypatch.setattr(devpost, "ROOT", ready_release)
    monkeypatch.setattr(devpost, "_public_bytes", lambda url: json.dumps(public_ref(old)).encode())
    page_checks = []
    monkeypatch.setattr(devpost, "opens", lambda url: page_checks.append(url) or 200)
    assert devpost.main(["--final", "--ref", "hackathon-submission"]) == 2
    out = capsys.readouterr()
    assert "does not match the local tested commit" in out.err and out.out == "" and page_checks == []


@pytest.mark.parametrize("app_data", [b"[project]\ndependencies = []\n", b"<html>Invented login page</html>",
                                      b"not TOML", b"", b"invented older app metadata"])
def test_matching_tag_with_different_published_app_is_rejected(ready_release, monkeypatch, app_data):
    sha = release_commit(ready_release)
    monkeypatch.setattr(devpost, "_public_bytes", lambda url: app_data if url == devpost.PUBLIC_APP else json.dumps(public_ref(sha)).encode())
    assert "published Reachy Mini app package metadata differs" in devpost.published_release_problems(ready_release)[0]


def test_missing_published_tag_stops_before_checking_app_metadata(ready_release, monkeypatch):
    calls = []

    def read(url):
        calls.append(url)
        raise urllib.error.HTTPError(url, 404, "invented", {}, None)

    monkeypatch.setattr(devpost, "_public_bytes", read)
    assert "absent from GitHub" in devpost.published_release_problems(ready_release)[0]
    assert len(calls) == 1


@pytest.mark.parametrize("data", [b"", b"not json", b"\xff", b"{invalid"])
def test_bad_json_or_encoding_is_a_fixed_release_failure(ready_release, monkeypatch, data):
    monkeypatch.setattr(devpost, "_public_bytes", lambda url: data)
    problems = devpost.published_release_problems(ready_release)
    assert problems and "could not be verified" in problems[0]


@pytest.mark.parametrize("size,accepted", [(65_536, True), (65_537, False)])
def test_public_download_is_size_bounded_and_has_no_provider_credentials(monkeypatch, size, accepted):
    monkeypatch.setenv("NEBIUS_API_KEY", "invented-private-key")
    seen = []

    def opener(request, timeout):
        seen.append((request, timeout))
        return io.BytesIO(b"x" * size)

    monkeypatch.setattr(devpost.urllib.request, "urlopen", opener)
    if accepted:
        assert len(devpost._public_bytes(devpost.PUBLIC_APP)) == size
    else:
        with pytest.raises(ValueError, match="supported size"):
            devpost._public_bytes(devpost.PUBLIC_APP)
    request, timeout = seen[0]
    assert request.get_method() == "GET" and timeout == 5
    assert not any("invented-private-key" in v for _, v in request.header_items())
    assert not {"authorization", "cookie"} & {k.lower() for k, _ in request.header_items()}


@pytest.mark.parametrize("annotated", [False, True])
def test_actual_http_metadata_then_full_final_export_uses_the_same_release(ready_release, monkeypatch, capsys, annotated):
    """Only a loopback HTTP fixture; no real GitHub/HF request, model, key or household data."""
    if annotated:
        subprocess.run(["git", "-C", str(ready_release), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                        "tag", "-f", "-a", "hackathon-submission", "-m", "Invented annotated release"], check=True, capture_output=True)
    sha, tag_sha = release_commit(ready_release), "d" * 40
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            requests.append((self.path, self.headers.get("Authorization"), self.headers.get("Cookie")))
            if self.path == "/api/git/ref/tags/hackathon-submission":
                data = json.dumps(public_ref(tag_sha, "tag") if annotated else public_ref(sha)).encode()
            elif self.path == f"/api/git/tags/{tag_sha}":
                data = json.dumps({"sha": tag_sha, "object": {"type": "commit", "sha": sha}}).encode()
            elif self.path == "/app.toml":
                data = (ready_release / "reachy_app/pyproject.toml").read_bytes()
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    monkeypatch.setattr(devpost, "ROOT", ready_release)
    monkeypatch.setattr(devpost, "PUBLIC_API", base + "/api")
    monkeypatch.setattr(devpost, "PUBLIC_APP", base + "/app.toml")
    checked = []
    monkeypatch.setattr(devpost, "opens", lambda url: checked.append(url) or 200)
    try:
        assert devpost.main(["--final", "--ref", "hackathon-submission"]) == 0
        assert "=== Project name" in capsys.readouterr().out and checked
        assert [r[0] for r in requests] == (["/api/git/ref/tags/hackathon-submission"] +
            ([f"/api/git/tags/{tag_sha}"] if annotated else []) + ["/app.toml"])
        assert all(auth is None and cookie is None for _, auth, cookie in requests)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
