"""
Fetch mergedBy and approving reviewers for every merged PR.
Cached to data/reviews_<release>.json — delete to re-fetch.

Usage (from presentations/ root):
    uv run eurollvm26/release-update/fetch_pr_reviews.py
"""

import json
import subprocess
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
RELEASES = ["20.x", "21.x", "22.x"]
BATCH    = 50


def gh_graphql(query: str) -> dict:
    result = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={query}"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


def build_query(pr_numbers: list[int]) -> str:
    aliases = "\n".join(
        f'  pr{n}: pullRequest(number: {n}) {{'
        f'    mergedBy {{ login }}'
        f'    reviews(first: 30, states: [APPROVED]) {{ nodes {{ author {{ login }} }} }}'
        f'  }}'
        for n in pr_numbers
    )
    return f'{{\n  repository(owner: "llvm", name: "llvm-project") {{\n{aliases}\n  }}\n}}'


def fetch_reviews(release: str) -> dict[int, dict]:
    key   = release.replace(".", "_")
    cache = DATA_DIR / f"reviews_{key}.json"

    if cache.exists():
        print(f"  [cache] {cache.name}")
        data = json.load(cache.open())
        return {int(k): v for k, v in data.items()}

    prs    = json.load((DATA_DIR / f"prs_{key}.json").open())
    merged = [pr["number"] for pr in prs if pr.get("merged_at")]

    print(f"  fetching reviews for {len(merged)} PRs in {release} …")
    result: dict[int, dict] = {}

    for i in range(0, len(merged), BATCH):
        batch = merged[i : i + BATCH]
        data  = gh_graphql(build_query(batch))
        repo  = data["data"]["repository"]

        for n in batch:
            pr_data = repo.get(f"pr{n}", {})
            merged_by = None
            if pr_data.get("mergedBy"):
                merged_by = pr_data["mergedBy"]["login"]
            approvers = [
                r["author"]["login"]
                for r in (pr_data.get("reviews") or {}).get("nodes", [])
                if r.get("author")
            ]
            result[n] = {"merged_by": merged_by, "approvers": approvers}

        print(f"    {min(i + BATCH, len(merged))}/{len(merged)}")

    with cache.open("w") as f:
        json.dump({str(k): v for k, v in result.items()}, f, indent=2)
    print(f"  saved → {cache.name}")
    return result


def main():
    for release in RELEASES:
        print(f"\n=== {release} ===")
        reviews = fetch_reviews(release)
        print(f"  {len(reviews)} PRs fetched")


if __name__ == "__main__":
    main()
