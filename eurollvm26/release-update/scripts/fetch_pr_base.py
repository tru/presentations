"""
Fetch the base branch for every merged PR in the milestone.
Cached to data/base_<release>.json — delete to re-fetch.
"""
import json
import subprocess
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
RELEASES = ["20.x", "21.x", "22.x"]
BATCH = 50


def gh_graphql(query: str) -> dict:
    result = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={query}"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


def build_query(pr_numbers: list[int]) -> str:
    aliases = "\n".join(
        f'  pr{n}: pullRequest(number: {n}) {{ baseRefName }}'
        for n in pr_numbers
    )
    return f'{{\n  repository(owner: "llvm", name: "llvm-project") {{\n{aliases}\n  }}\n}}'


def fetch_base(release: str) -> dict[int, str]:
    key   = release.replace(".", "_")
    cache = DATA_DIR / f"base_{key}.json"

    if cache.exists():
        print(f"  [cache] {cache.name}")
        data = json.load(cache.open())
        return {int(k): v for k, v in data.items()}

    prs    = json.load((DATA_DIR / f"prs_{key}.json").open())
    merged = [pr["number"] for pr in prs if pr.get("merged_at")]

    print(f"  fetching base branch for {len(merged)} PRs in {release} …")
    result: dict[int, str] = {}

    for i in range(0, len(merged), BATCH):
        batch = merged[i : i + BATCH]
        data  = gh_graphql(build_query(batch))
        repo  = data["data"]["repository"]
        for n in batch:
            pr_data = repo.get(f"pr{n}")
            result[n] = pr_data["baseRefName"] if pr_data else "unknown"
        print(f"    {min(i + BATCH, len(merged))}/{len(merged)}")

    with cache.open("w") as f:
        json.dump({str(k): v for k, v in result.items()}, f, indent=2)
    print(f"  saved → {cache.name}")
    return result


def main():
    for release in RELEASES:
        print(f"\n=== {release} ===")
        bases = fetch_base(release)
        release_branch = f"release/{release}"
        on_release = sum(1 for b in bases.values() if b == release_branch)
        on_main    = sum(1 for b in bases.values() if b == "main")
        other      = sum(1 for b in bases.values() if b not in (release_branch, "main"))
        print(f"  base={release_branch}: {on_release}")
        print(f"  base=main:             {on_main}")
        print(f"  other:                 {other}")


if __name__ == "__main__":
    main()
