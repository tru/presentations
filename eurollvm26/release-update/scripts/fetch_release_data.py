"""
Fetch LLVM release PR data from GitHub and save to data/.

Usage (run from the presentations/ root):
    uv run eurollvm26/release-update/fetch_release_data.py

Requires `gh` CLI to be authenticated (gh auth login).
Raw PR data is cached in data/prs_<release>.json so subsequent runs
are fast. Delete a cache file to force a re-fetch.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Release configuration
# ---------------------------------------------------------------------------

RELEASES = {
    "20.x": {
        "milestone_number": 26,
        "branch":  "2025-01-14T00:00:00Z",
        "rc1":     "2025-02-02T02:07:38Z",
        "rc2":     "2025-02-12T06:07:31Z",
        "rc3":     "2025-02-26T02:03:45Z",
        "final":   "2025-03-04T20:05:00Z",
    },
    "21.x": {
        "milestone_number": 27,
        "branch":  "2025-07-08T00:00:00Z",
        "rc1":     "2025-07-17T19:06:25Z",
        "rc2":     "2025-07-29T14:36:22Z",
        "rc3":     "2025-08-12T09:04:38Z",
        "final":   "2025-08-26T14:21:33Z",
    },
    "22.x": {
        "milestone_number": 29,
        "branch":  "2026-01-13T00:00:00Z",
        "rc1":     "2026-01-16T09:13:22Z",
        "rc2":     "2026-01-27T08:33:55Z",
        "rc3":     "2026-02-10T07:57:37Z",
        "final":   "2026-02-24T07:36:08Z",
    },
}

PHASES = ["branch→rc1", "rc1→rc2", "rc2→rc3", "rc3→final", "post-final"]

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# GitHub GraphQL fetch (only the fields we need — much faster than REST)
# ---------------------------------------------------------------------------

GQL_QUERY = """
query($owner: String!, $repo: String!, $milestone: Int!, $after: String) {
  repository(owner: $owner, name: $repo) {
    pullRequests(
      first: 100
      after: $after
      states: [OPEN, CLOSED, MERGED]
      orderBy: {field: CREATED_AT, direction: ASC}
    ) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number
        state
        createdAt
        mergedAt
        closedAt
        milestone { number }
      }
    }
  }
}
"""

# GraphQL doesn't support filtering by milestone, so we fetch all PRs and
# filter client-side by milestone number. We page through until done.
# For a repo the size of llvm-project this is ~thousands of pages — too slow.
#
# Instead use the REST issues endpoint which supports milestone filtering
# and returns only lightweight issue/PR records when we ask for minimal fields
# via the issues API (PRs appear as issues).

def fetch_prs_rest(release: str, milestone_number: int) -> list[dict]:
    """Fetch via REST /issues?milestone=N&pull_request (fast, paginated)."""
    cache = DATA_DIR / f"prs_{release.replace('.', '_')}.json"

    if cache.exists():
        print(f"  [cache] {cache.name}")
        with cache.open() as f:
            return json.load(f)

    print(f"  [fetch] milestone {milestone_number} for {release} (this may take a minute) ...", flush=True)

    all_prs = []
    page = 1
    while True:
        url = (
            f"repos/llvm/llvm-project/issues"
            f"?milestone={milestone_number}&state=all&per_page=100&page={page}"
        )
        result = subprocess.run(
            ["gh", "api", url],
            capture_output=True, text=True, check=True,
        )
        items = json.loads(result.stdout)
        if not items:
            break

        for item in items:
            # Issues endpoint returns both issues and PRs; filter to PRs only
            if "pull_request" not in item:
                continue
            all_prs.append({
                "number":     item["number"],
                "title":      item["title"],
                "author":     item["user"]["login"],
                "state":      item["state"],
                "created_at": item["created_at"],
                "closed_at":  item.get("closed_at"),
                "merged_at":  item["pull_request"].get("merged_at"),
            })

        print(f"    page {page}: {len(items)} items, {len(all_prs)} PRs so far")
        if len(items) < 100:
            break
        page += 1

    with cache.open("w") as f:
        json.dump(all_prs, f, indent=2)
    print(f"  saved {len(all_prs)} PRs → {cache.name}")
    return all_prs


# ---------------------------------------------------------------------------
# Phase bucketing
# ---------------------------------------------------------------------------

def parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def phase_for(merged_at: str | None, cfg: dict) -> str | None:
    if not merged_at:
        return None
    t = parse_dt(merged_at)
    if t < parse_dt(cfg["branch"]):
        return None
    if t < parse_dt(cfg["rc1"]):
        return "branch→rc1"
    if t < parse_dt(cfg["rc2"]):
        return "rc1→rc2"
    if t < parse_dt(cfg["rc3"]):
        return "rc2→rc3"
    if t < parse_dt(cfg["final"]):
        return "rc3→final"
    return "post-final"


def compute_stats(release: str, prs: list[dict], cfg: dict) -> dict:
    merged   = [pr for pr in prs if pr["merged_at"]]
    rejected = [pr for pr in prs if not pr["merged_at"] and pr["state"] == "closed"]

    phase_counts = {p: 0 for p in PHASES}
    for pr in merged:
        p = phase_for(pr["merged_at"], cfg)
        if p:
            phase_counts[p] += 1

    return {
        "release":      release,
        "total_prs":    len(prs),
        "merged":       len(merged),
        "rejected":     len(rejected),
        "phase_counts": phase_counts,
        "dates":        {k: cfg[k] for k in ("branch", "rc1", "rc2", "rc3", "final")},
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    all_stats = {}

    for release, cfg in RELEASES.items():
        print(f"\n=== {release} ===")
        prs = fetch_prs_rest(release, cfg["milestone_number"])
        stats = compute_stats(release, prs, cfg)
        all_stats[release] = stats

        print(f"  merged: {stats['merged']}  rejected: {stats['rejected']}")
        for phase, count in stats["phase_counts"].items():
            bar = "█" * (count // 5)
            print(f"  {phase:15s} {count:4d}  {bar}")

    out = DATA_DIR / "release_stats.json"
    with out.open("w") as f:
        json.dump(all_stats, f, indent=2)
    print(f"\nSaved summary → {out}")


if __name__ == "__main__":
    main()
