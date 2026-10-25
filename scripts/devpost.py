"""The Devpost form's fields, ready to paste, from docs/submission.md (and docs/feedback.md), and every link checked.

    uv run python scripts/devpost.py                     the draft: evidence links point at main, which exists now
    uv run python scripts/devpost.py --ref hackathon-submission --check
                                                         at submission: links at the submitted tag, each one opened

docs/submission.md keeps its links at the hackathon-submission tag, so the submitted text never changes under a
judge; until that tag is pushed they would not open, so a draft points them at another ref. --check opens every link
as a logged-out visitor would (no token sent) and lists any that doesn't answer 200. Writes nothing.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAG_LINK = "github.com/AndyDM9/andy-companion/blob/hackathon-submission/"
REPO = "https://github.com/AndyDM9/andy-companion"


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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ref", default="main", help="the git ref the evidence links point at (default: main)")
    ap.add_argument("--check", action="store_true", help="open every link and list any that doesn't answer 200")
    args = ap.parse_args(argv)
    text = at_ref((ROOT / "docs" / "submission.md").read_text(), args.ref)
    f = fields(text)
    order = ["Project name", "Tagline", "Track", "Video", "Code", "Try it", "Built with", "Prior work"]
    for name in order:
        if name in f:
            value = f[name]
            if name == "Code":
                value = f"{REPO}/tree/{args.ref}"
            print(f"=== {name}\n{value}\n")
    print(f"=== About the project (Markdown)\n{f['About the project']}\n")
    feedback = (ROOT / "docs" / "feedback.md").read_text()
    print("=== Feedback (from docs/feedback.md)\n" + feedback.split("\n", 1)[1].strip() + "\n")
    tagline = f.get("Tagline", "")
    print(f"--- tagline: {len(tagline)} characters (Devpost allows 200); built-with tags: "
          f"{len([t for t in f.get('Built with', '').split(',') if t.strip()])}", file=sys.stderr)
    if args.check:
        urls = [u.rstrip(".,;") for u in links(text + feedback) if "[" not in u]
        with ThreadPoolExecutor(8) as pool:
            codes = dict(zip(urls, pool.map(opens, urls)))
        bad = {u: c for u, c in codes.items() if c != 200}
        if any("ftc.gov" in u for u in bad):           # it refuses some networks (a VPN here, 2026-10-25), even its home
            print("--- ftc.gov refuses some networks outright; check its links from another one before calling them broken",
                  file=sys.stderr)
        print(f"--- {len(urls)} links opened: {len(urls) - len(bad)} answer 200" +
              ("" if not bad else "; these don't:\n" + "\n".join(f"  {c}  {u}" for u, c in sorted(bad.items()))),
              file=sys.stderr)
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
