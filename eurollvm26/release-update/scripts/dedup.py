"""
Deduplication helper for release PR data.

When a fix goes to main and then gets cherry-picked to a release branch,
both PRs end up tagged with the milestone. This module filters out the
parent (main-branch) PR so each fix is counted exactly once via its
cherry-pick PR.

Cherry-pick PRs follow the convention:
  "release/22.x: <original title> (#<parent_number>)"
"""
import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def deduped_merged(release: str, prs: list[dict] | None = None) -> list[dict]:
    """Return merged PRs for a release with duplicate parent PRs removed."""
    if prs is None:
        key = release.replace(".", "_")
        prs = json.load((DATA_DIR / f"prs_{key}.json").open())

    merged = [p for p in prs if p.get("merged_at")]

    prefix = f"release/{release}:"
    parent_nums: set[int] = set()
    for pr in merged:
        if pr["title"].startswith(prefix):
            m = re.search(r"\(#(\d+)\)\s*$", pr["title"])
            if m:
                parent_nums.add(int(m.group(1)))

    return [p for p in merged if p["number"] not in parent_nums]
