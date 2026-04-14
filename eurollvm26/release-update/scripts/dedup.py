"""
Filter release PR data to only PRs actually merged into the release branch.

When a fix goes to main and then gets cherry-picked to a release branch,
both PRs end up tagged with the milestone. This module uses the PR's base
branch field (fetched via fetch_pr_base.py) to keep only PRs whose base
is the release branch itself — the authoritative ground truth.
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def deduped_merged(release: str, prs: list[dict] | None = None) -> list[dict]:
    """Return only merged PRs that targeted the release branch."""
    key = release.replace(".", "_")
    if prs is None:
        prs = json.load((DATA_DIR / f"prs_{key}.json").open())

    bases = json.load((DATA_DIR / f"base_{key}.json").open())
    rel_branch = f"release/{release}"

    return [
        p for p in prs
        if p.get("merged_at") and bases.get(str(p["number"])) == rel_branch
    ]
