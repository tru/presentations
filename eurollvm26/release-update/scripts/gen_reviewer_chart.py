"""
Generate charts showing who merges and who reviews PRs into release branches.
Infra-only PRs are excluded.
"""
import json
import collections
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
OUT_DIR  = Path(__file__).parent.parent
RELEASES = ["20.x", "21.x", "22.x"]

BACKGROUND = "#ffffff"
TEXT_COLOR  = "#1a1a2e"
RELEASE_COLORS = {"20.x": "#b39ddb", "21.x": "#7c4dbd", "22.x": "#3b1f7a"}

INFRA_DIRS = {".github", "cmake", ".ci", "third-party"}


def is_infra(num: int, files: dict) -> bool:
    paths = files.get(str(num), [])
    return bool(paths) and all(p.split("/")[0] in INFRA_DIRS for p in paths)


def load(release: str):
    key = release.replace(".", "_")
    prs     = json.load((DATA_DIR / f"prs_{key}.json").open())
    reviews = json.load((DATA_DIR / f"reviews_{key}.json").open())
    files   = json.load((DATA_DIR / f"files_{key}.json").open())
    merged_nums = {str(p["number"]) for p in prs if p.get("merged_at")}
    return merged_nums, reviews, files


# ── aggregate ──────────────────────────────────────────────────────────────

merger_by_release:   dict[str, collections.Counter] = {}
approver_by_release: dict[str, collections.Counter] = {}

for release in RELEASES:
    merged_nums, reviews, files = load(release)
    merger_ctr   = collections.Counter()
    approver_ctr = collections.Counter()

    for num, rv in reviews.items():
        if num not in merged_nums:
            continue
        if is_infra(int(num), files):
            continue
        mb = rv.get("merged_by")
        if mb:
            merger_ctr[mb] += 1
        for a in rv.get("approvers", []):
            approver_ctr[a] += 1

    merger_by_release[release]   = merger_ctr
    approver_by_release[release] = approver_ctr

    total = sum(merger_ctr.values())
    top_merger, top_n = merger_ctr.most_common(1)[0]
    print(f"{release}: {top_merger} merged {top_n}/{total} ({top_n/total*100:.0f}%)")


def top_n_combined(by_release: dict, n: int,
                   exclude: list[str] | None = None) -> list[str]:
    combined: collections.Counter = collections.Counter()
    for c in by_release.values():
        combined.update(c)
    for k in (exclude or []):
        combined.pop(k, None)
    return [k for k, _ in combined.most_common(n)]


def grouped_bar(by_release: dict, labels: list[str],
                out_path: Path, ylabel: str) -> None:
    n_releases = len(RELEASES)
    bar_w = 0.22
    x     = np.arange(len(labels)) * (n_releases * bar_w + 0.20)

    fig, ax = plt.subplots(figsize=(max(12, len(labels) * 1.1), 5.5))
    fig.patch.set_facecolor(BACKGROUND)
    ax.set_facecolor(BACKGROUND)

    for i, release in enumerate(RELEASES):
        counts = [by_release[release].get(lbl, 0) for lbl in labels]
        offset = (i - (n_releases - 1) / 2) * bar_w
        bars   = ax.bar(x + offset, counts, bar_w,
                        color=RELEASE_COLORS[release],
                        label=f"LLVM {release}", zorder=3)
        for bar, count in zip(bars, counts):
            if count > 0:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 1,
                        str(count),
                        ha="center", va="bottom",
                        fontsize=8.5, fontweight="bold",
                        color=TEXT_COLOR)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11, color=TEXT_COLOR,
                       rotation=30, ha="right")
    ax.set_ylabel(ylabel, fontsize=11, color=TEXT_COLOR, labelpad=8)
    ax.tick_params(axis="y", labelsize=9, colors=TEXT_COLOR)
    ax.tick_params(axis="x", length=0)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#e0d7f5")
    ax.yaxis.grid(True, color="#e0d7f5", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(fontsize=10, frameon=False, labelcolor=TEXT_COLOR, loc="upper right")

    plt.tight_layout(pad=0.6)
    plt.savefig(out_path, dpi=180, bbox_inches="tight",
                facecolor=BACKGROUND, edgecolor="none")
    plt.close()
    print(f"Saved → {out_path}")


# ── merger chart ───────────────────────────────────────────────────────────
top_mergers = top_n_combined(merger_by_release, 12)
grouped_bar(merger_by_release, top_mergers,
            OUT_DIR / "merger_chart.png",
            ylabel="PRs merged into release branch")

# ── approver chart ─────────────────────────────────────────────────────────
# exclude people who primarily appear as mergers to avoid double-counting
top_approvers = top_n_combined(approver_by_release, 12)
grouped_bar(approver_by_release, top_approvers,
            OUT_DIR / "approver_chart.png",
            ylabel="PRs approved")

# ── print summary ──────────────────────────────────────────────────────────
print("\n── Merger share per release ──")
for release in RELEASES:
    ctr   = merger_by_release[release]
    total = sum(ctr.values())
    for name, n in ctr.most_common(3):
        print(f"  {release} {name}: {n}/{total} ({n/total*100:.0f}%)")

print("\n── Top approvers (combined) ──")
combined: collections.Counter = collections.Counter()
for c in approver_by_release.values():
    combined.update(c)
for name, n in combined.most_common(15):
    print(f"  {n:4d}  {name}")
