"""The Devpost form's fields, ready to paste, from docs/submission.md (and docs/feedback.md), and every link checked.

    uv run python scripts/devpost.py                     the draft: evidence links point at main, which exists now
    uv run python scripts/devpost.py --ref hackathon-submission --final
                                                         at submission: links at the submitted tag, each one opened

docs/submission.md keeps its links at the hackathon-submission tag, so the submitted text never changes under a
judge; until that tag is pushed they would not open, so a draft points them at another ref. --check opens every link
as a logged-out visitor would (no token sent) and lists any that doesn't open (any 2xx answer). Writes nothing.
--final first rejects a missing YouTube URL, final tag or app pin, then opens the public links. It requires
the tracked working files and export inputs to match the tagged snapshot, the published tag to resolve
to that same commit, and the published app's package metadata to match. It does not certify video
visibility, duration, hardware behavior, rights, or the actual Devpost submission.
"""

from __future__ import annotations

import argparse
import http.client
import json
import re
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent.parent
TAG_LINK = "github.com/AndyDM9/andy-companion/blob/hackathon-submission/"
REPO = "https://github.com/AndyDM9/andy-companion"
FINAL_TAG = "hackathon-submission"
PUBLIC_API = "https://api.github.com/repos/AndyDM9/andy-companion"
PUBLIC_APP = "https://huggingface.co/spaces/andydm/andy-companion-app/resolve/main/pyproject.toml"
PUBLIC_MAX_BYTES = 65_536
PUBLIC_TIMEOUT_S = 5
MAX_TAG_DEPTH = 5


def fields(text: str) -> dict:
    """The form fields (bullets under "## Form fields") and the story (everything under "## The story")."""
    form = text.split("## Form fields", 1)[1].split("## The story", 1)[0]
    out = {}
    # "- **Name:** value", or "- **Name** (a note): value"
    for m in re.finditer(r"^- \*\*([^*]+?):?\*\*(?: \([^)]*\))?:? (.*?)(?=^- \*\*|\Z)", form, re.S | re.M):
        out[m.group(1)] = " ".join(m.group(2).split())
    story = text.split("## The story", 1)[1].split("\n", 1)[1].strip()
    out["About the project"] = re.sub(r"^###", "##", story, flags=re.M)     # Devpost's headings are one level up
    return out


def at_ref(text: str, ref: str) -> str:
    return text.replace(TAG_LINK, f"github.com/AndyDM9/andy-companion/blob/{ref}/")


def links(text: str) -> list:
    return sorted(set(re.findall(r"https?://[^\s)\]>\"'*]+", text)))


def opens(url: str) -> int:
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "andy-devpost-check/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def youtube_video(value: str) -> bool:
    """A video-shaped HTTPS YouTube link, not a placeholder, playlist, or lookalike host."""
    urls = links(value)
    if len(urls) != 1:
        return False
    try:
        url = urlsplit(urls[0])
    except ValueError:
        return False
    if url.scheme != "https" or url.username or url.password:
        return False
    if url.hostname == "youtu.be":
        video_id = url.path.strip("/")
    elif url.hostname in ("youtube.com", "www.youtube.com", "m.youtube.com"):
        if url.path == "/watch":
            video_id = parse_qs(url.query).get("v", [""])[0]
        elif url.path.startswith(("/shorts/", "/embed/")):
            video_id = url.path.rstrip("/").rsplit("/", 1)[-1]
        else:
            return False
    else:
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id))


def final_problems(form: dict, ref: str, root: Path) -> list[str]:
    """Repository release checks only. Passing these does not mean the entry is submitted or eligible."""
    problems = []
    if not youtube_video(form.get("Video", "")):
        problems.append("Replace the Video placeholder with the real HTTPS YouTube video URL.")
    if ref != FINAL_TAG:
        problems.append(f"Use --ref {FINAL_TAG} for the final export.")
    try:
        tag = subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", f"refs/tags/{FINAL_TAG}^{{commit}}"],
                             capture_output=True, text=True, timeout=5)
        tag_exists = tag.returncode == 0
    except (OSError, subprocess.SubprocessError):
        tag_exists = False
    if not tag_exists:
        problems.append(f"Create and publish the {FINAL_TAG} tag after final validation; it is missing locally.")
    else:
        try:
            snapshot = subprocess.run(["git", "-C", str(root), "diff", "--quiet", f"refs/tags/{FINAL_TAG}", "--"],
                                      capture_output=True, timeout=5)
            matches = snapshot.returncode == 0
            # git diff ignores untracked files: all three export inputs must exist in the tag too.
            for path in ("docs/submission.md", "docs/feedback.md", "reachy_app/pyproject.toml"):
                saved = subprocess.run(["git", "-C", str(root), "show", f"refs/tags/{FINAL_TAG}:{path}"],
                                       capture_output=True, timeout=5)
                matches = matches and saved.returncode == 0 and saved.stdout == (root / path).read_bytes()
        except (OSError, subprocess.SubprocessError):
            matches = False
        if not matches:
            problems.append("The working files differ from the release tag or its export inputs are missing. "
                            "Validate and commit the final files before tagging; export from that unchanged snapshot.")
    try:
        project = tomllib.loads((root / "reachy_app/pyproject.toml").read_text())["project"]
        dependencies = project.get("dependencies") if isinstance(project, dict) else None
        pinned = (isinstance(dependencies, list) and all(isinstance(d, str) for d in dependencies)
                  and f"andy-companion[robot] @ git+{REPO}@{FINAL_TAG}" in dependencies)
    except (OSError, ValueError, KeyError):
        pinned = False
    if not pinned:
        problems.append(f"Pin the app's andy-companion dependency to {FINAL_TAG} instead of main.")
    if not 0 < len(form.get("Tagline", "")) <= 200:
        problems.append("The tagline must contain 1 to 200 characters.")
    if not 0 < len([t for t in form.get("Built with", "").split(",") if t.strip()]) <= 25:
        problems.append("The built-with list must contain 1 to 25 tags.")
    return problems


def _public_bytes(url: str) -> bytes:
    """A bounded anonymous GET; no provider configuration, cookies or authorization headers."""
    request = urllib.request.Request(url, headers={"User-Agent": "andy-final-release-check/1.0", "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(request, timeout=PUBLIC_TIMEOUT_S) as response:
            data = response.read(PUBLIC_MAX_BYTES + 1)
    except urllib.error.HTTPError as error:
        error.close()
        raise
    if len(data) > PUBLIC_MAX_BYTES:
        raise ValueError("Public release metadata exceeded the supported size.")
    return data


def published_tag_commit() -> str | None:
    """Resolve the exact public ref, then bounded annotated-tag objects, without following supplied URLs."""
    try:
        data = json.loads(_public_bytes(f"{PUBLIC_API}/git/ref/tags/{FINAL_TAG}"))
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise
    if not isinstance(data, dict) or data.get("ref") != f"refs/tags/{FINAL_TAG}":
        raise ValueError("Public release reference metadata is not supported.")
    seen = set()
    for depth in range(MAX_TAG_DEPTH + 1):
        obj = data.get("object")
        if not isinstance(obj, dict) or not isinstance(obj.get("sha"), str) or not re.fullmatch(r"[0-9a-f]{40}", obj["sha"]):
            raise ValueError("Public release object metadata is not supported.")
        sha = obj["sha"]
        if obj.get("type") == "commit":
            return sha
        if obj.get("type") != "tag" or sha in seen or depth == MAX_TAG_DEPTH:
            raise ValueError("Public release tag cannot be resolved to a commit.")
        seen.add(sha)
        data = json.loads(_public_bytes(f"{PUBLIC_API}/git/tags/{sha}"))
        if not isinstance(data, dict) or data.get("sha") != sha:
            raise ValueError("Public annotated-tag metadata is not supported.")
    raise ValueError("Public release tag cannot be resolved to a commit.")


def published_release_problems(root: Path) -> list[str]:
    """Run only after local release checks. HTTP 200 links alone cannot prove the same release is published."""
    try:
        local = subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", f"refs/tags/{FINAL_TAG}^{{commit}}"],
                               capture_output=True, text=True, timeout=5, check=True).stdout.strip()
        published = published_tag_commit()
        if published is None:
            return [f"Publish {FINAL_TAG} publicly before final export; the tag is absent from GitHub."]
        if published != local:
            return ["The published release tag does not match the local tested commit. Resolve the release refs before exporting."]
        if _public_bytes(PUBLIC_APP) != (root / "reachy_app/pyproject.toml").read_bytes():
            return ["The published Reachy Mini app package metadata differs from the tested release. Publish the matching app files before exporting."]
    except (OSError, ValueError, TypeError, KeyError, RecursionError, http.client.HTTPException, subprocess.SubprocessError):
        return ["Published release metadata could not be verified. Check public GitHub/Hugging Face access and retry; no final export was produced."]
    return []


def check_links(text: str) -> int:
    urls = [u.rstrip(".,;") for u in links(text) if "[" not in u]
    with ThreadPoolExecutor(8) as pool:
        codes = dict(zip(urls, pool.map(opens, urls), strict=True))
    bad = {u: c for u, c in codes.items() if not 200 <= c < 300}      # PubMed answers robots 203
    if any("ftc.gov" in u and code in (0, 403, 429) for u, code in bad.items()):
        print("--- an FTC request was blocked or unavailable; verify the source from another network",
              file=sys.stderr)
    print(f"--- {len(urls)} links opened: {len(urls) - len(bad)} open" +
          ("" if not bad else "; these don't:\n" + "\n".join(f"  {c}  {u}" for u, c in sorted(bad.items()))),
          file=sys.stderr)
    return 1 if bad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ref", default="main", help="the git ref the evidence links point at (default: main)")
    ap.add_argument("--check", action="store_true", help="open every link and list any that doesn't open (a 2xx answer)")
    ap.add_argument("--final", action="store_true", help="require final video/local and published tag/app pin, then check links; manual video and hardware checks still required")
    args = ap.parse_args(argv)
    text = at_ref((ROOT / "docs" / "submission.md").read_text(), args.ref)
    f = fields(text)
    if args.final:
        problems = final_problems(f, args.ref, ROOT)
        if not problems:
            problems = published_release_problems(ROOT)
        if problems:
            print("Not ready for final export:\n" + "\n".join(f"  - {problem}" for problem in problems), file=sys.stderr)
            return 2
        args.check = True
    feedback = (ROOT / "docs" / "feedback.md").read_text()
    if args.final:
        code = check_links(text + feedback)
        if code:
            return code  # a failed final check must not emit copy-ready submission fields
    order = ["Project name", "Tagline", "Track", "Video", "Code", "Try it", "Testing instructions", "Built with", "Prior work"]
    for name in order:
        if name in f:
            value = f[name]
            if name == "Code":
                value = f"{REPO}/tree/{args.ref}"
            print(f"=== {name}\n{value}\n")
    print(f"=== About the project (Markdown)\n{f['About the project']}\n")
    print("=== Feedback (from docs/feedback.md)\n" + feedback.split("\n", 1)[1].strip() + "\n")
    tagline = f.get("Tagline", "")
    print(f"--- tagline: {len(tagline)} characters (Devpost allows 200); built-with tags: "
          f"{len([t for t in f.get('Built with', '').split(',') if t.strip()])}", file=sys.stderr)
    if args.check and not args.final:
        return check_links(text + feedback)
    return 0


if __name__ == "__main__":
    sys.exit(main())
