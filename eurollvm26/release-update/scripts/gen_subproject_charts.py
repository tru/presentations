"""
Generate subproject and contributor charts from file-path data.

For each merged PR, the subproject is determined by the top-level directory
with the most files changed (majority rules). This is more accurate than
parsing PR titles.

Outputs:
  subproject_chart.png  — top subprojects across all releases
  contributor_chart.png — top contributors across all releases
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
RELEASE_COLORS = {
    "20.x": "#b39ddb",
    "21.x": "#7c4dbd",
    "22.x": "#3b1f7a",
}

# Map top-level repo directory → canonical subproject label
DIR_TO_SUBPROJECT = {
    "llvm":                "LLVM Core",
    "clang":               "Clang",
    "clang-tools-extra":   "Clang",       # clangd, clang-tidy, etc.
    "libcxx":              "libc++",
    "libcxxabi":           "libc++",
    "libunwind":           "libc++",
    "lldb":                "LLDB",
    "lld":                 "LLD",
    "flang":               "Flang",
    "flang-rt":            "Flang",
    "compiler-rt":         "compiler-rt",
    "mlir":                "MLIR",
    "openmp":              "OpenMP",
    "bolt":                "BOLT",
    "libc":                "libc",
    "libclc":              "libclc",
    "offload":             "Offload",
    "polly":               "Polly",
    "cross-project-tests": "Testing",
    ".github":             "Infra",
    "cmake":               "Infra",
    ".ci":                 "Infra",
    "third-party":         "Infra",
}


def subproject_for_pr(paths: list[str]) -> str:
    """Assign PR to the subproject with the most files changed."""
    if not paths:
        return "Unknown"
    counts: collections.Counter = collections.Counter()
    for p in paths:
        top = p.split("/")[0]
        label = DIR_TO_SUBPROJECT.get(top, top)  # fallback: raw dir name
        counts[label] += 1
    return counts.most_common(1)[0][0]


def load_data(release: str):
    key = release.replace(".", "_")
    prs   = json.load((DATA_DIR / f"prs_{key}.json").open())
    files = json.load((DATA_DIR / f"files_{key}.json").open())
    # files keys are strings
    merged = [pr for pr in prs if pr.get("merged_at")]
    return merged, {int(k): v for k, v in files.items()}


INFRA_LABELS = {"Infra", "Testing", "Unknown"}

# ── aggregate ──────────────────────────────────────────────────────────────

subproject_by_release: dict[str, collections.Counter] = {}
author_by_release:     dict[str, collections.Counter] = {}

for release in RELEASES:
    merged, files = load_data(release)
    sp_ctr   = collections.Counter()
    auth_ctr = collections.Counter()
    for pr in merged:
        sp     = subproject_for_pr(files.get(pr["number"], []))
        author = pr.get("author", "unknown")
        sp_ctr[sp] += 1
        if sp not in INFRA_LABELS:
            auth_ctr[author] += 1
    subproject_by_release[release] = sp_ctr
    author_by_release[release]     = auth_ctr
    print(f"{release}: top subprojects → {sp_ctr.most_common(5)}")


def top_n_combined(by_release: dict, n: int,
                   exclude: list[str] | None = None) -> list[str]:
    combined: collections.Counter = collections.Counter()
    for ctr in by_release.values():
        combined.update(ctr)
    for key in (exclude or []):
        combined.pop(key, None)
    return [k for k, _ in combined.most_common(n)]


def grouped_bar(by_release: dict, labels: list[str],
                out_path: Path, ylabel: str = "PRs merged") -> None:
    n_groups   = len(labels)
    n_releases = len(RELEASES)
    bar_w = 0.22
    gap   = 0.08
    x     = np.arange(n_groups) * (n_releases * bar_w + gap + 0.06)

    fig, ax = plt.subplots(figsize=(max(12, n_groups * 1.05), 5.5))
    fig.patch.set_facecolor(BACKGROUND)
    ax.set_facecolor(BACKGROUND)

    for i, release in enumerate(RELEASES):
        counts = [by_release[release].get(lbl, 0) for lbl in labels]
        offset = (i - (n_releases - 1) / 2) * bar_w
        bars = ax.bar(x + offset, counts, bar_w,
                      color=RELEASE_COLORS[release],
                      label=f"LLVM {release}", zorder=3)
        for bar, count in zip(bars, counts):
            if count > 0:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.4,
                        str(count),
                        ha="center", va="bottom",
                        fontsize=8, fontweight="bold",
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


# ── subproject chart — exclude bot and infra noise ─────────────────────────
top_sp = top_n_combined(subproject_by_release, 12,
                        exclude=["Infra", "Testing", "Unknown"])
grouped_bar(subproject_by_release, top_sp,
            OUT_DIR / "subproject_chart.png")

# ── contributor chart — exclude llvmbot and infra PRs ─────────────────────
top_auth = top_n_combined(author_by_release, 15, exclude=["llvmbot"])
grouped_bar(author_by_release, top_auth,
            OUT_DIR / "contributor_chart.png",
            ylabel="PRs merged (code only, excl. infra)")

# ── print summary ──────────────────────────────────────────────────────────
print("\n── Subprojects (combined, all releases) ──")
combined_sp: collections.Counter = collections.Counter()
for c in subproject_by_release.values():
    combined_sp.update(c)
for sp, n in combined_sp.most_common():
    print(f"  {n:4d}  {sp}")

print("\n── Top contributors (code PRs only, excluding llvmbot) ──")
combined_auth: collections.Counter = collections.Counter()
for c in author_by_release.values():
    combined_auth.update(c)
combined_auth.pop("llvmbot", None)
for auth, n in combined_auth.most_common(20):
    print(f"  {n:4d}  {auth}")
