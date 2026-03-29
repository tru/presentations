"""
Fetch the list of files changed for every merged PR and save to data/.

Uses GraphQL batching (50 PRs per query) to avoid ~1500 sequential REST calls.
Cached to data/files_<release>.json — delete to force re-fetch.

Usage (run from presentations/ root):
    uv run eurollvm26/release-update/fetch_pr_files.py
"""

import json
import subprocess
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
RELEASES = ["20.x", "21.x", "22.x"]
BATCH    = 50   # PRs per GraphQL query


def gh_graphql(query: str) -> dict:
    result = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={query}"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


def build_query(pr_numbers: list[int]) -> str:
    """Build a batched GraphQL query using aliases for each PR."""
    aliases = "\n".join(
        f'  pr{n}: pullRequest(number: {n}) {{ files(first: 100) {{ nodes {{ path }} }} }}'
        for n in pr_numbers
    )
    return f"""{{
  repository(owner: "llvm", name: "llvm-project") {{
{aliases}
  }}
}}"""


def fetch_files_for_release(release: str) -> dict[int, list[str]]:
    key   = release.replace(".", "_")
    cache = DATA_DIR / f"files_{key}.json"

    if cache.exists():
        print(f"  [cache] {cache.name}")
        data = json.load(cache.open())
        return {int(k): v for k, v in data.items()}

    prs_path = DATA_DIR / f"prs_{key}.json"
    all_prs  = json.load(prs_path.open())
    merged   = [pr["number"] for pr in all_prs if pr.get("merged_at")]

    print(f"  fetching files for {len(merged)} merged PRs in {release} …")
    result: dict[int, list[str]] = {}

    for i in range(0, len(merged), BATCH):
        batch = merged[i : i + BATCH]
        query = build_query(batch)
        data  = gh_graphql(query)
        repo  = data["data"]["repository"]

        for n in batch:
            pr_data = repo.get(f"pr{n}")
            if pr_data and pr_data.get("files"):
                paths = [f["path"] for f in pr_data["files"]["nodes"]]
            else:
                paths = []
            result[n] = paths

        done = min(i + BATCH, len(merged))
        print(f"    {done}/{len(merged)}")

    # save as string keys for JSON compat
    with cache.open("w") as f:
        json.dump({str(k): v for k, v in result.items()}, f, indent=2)
    print(f"  saved → {cache.name}")
    return result


def main():
    for release in RELEASES:
        print(f"\n=== {release} ===")
        files = fetch_files_for_release(release)
        # quick sanity check
        nonempty = sum(1 for v in files.values() if v)
        print(f"  {len(files)} PRs, {nonempty} with file data")


if __name__ == "__main__":
    main()
