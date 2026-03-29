"""
Drill down into llvm/ activity across releases.

Two charts:
  llvm_backends.png   — which backends (llvm/lib/Target/*) appear in most PRs
  llvm_subsystems.png — which llvm/lib subsystems appear in most PRs

Attribution: a PR is counted for a backend/subsystem if it touches ≥1 file
there. A PR can appear in multiple buckets (e.g. a fix touching both AArch64
and CodeGen). This gives a more honest picture than "winner takes all".
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

# Subsystem map: llvm/lib/<key> → label
SUBSYSTEM_MAP = {
    "Target":          "Backends",
    "Transforms":      "Transforms",
    "CodeGen":         "CodeGen",
    "MC":              "MC",
    "Analysis":        "Analysis",
    "IR":              "IR",
    "Support":         "Support",
    "ExecutionEngine": "ExecutionEngine",
    "ObjCopy":         "ObjCopy",
    "TargetParser":    "TargetParser",
    "DTLTO":           "DTLTO",
    "LTO":             "LTO",
    "Object":          "Object",
    "DebugInfo":       "DebugInfo",
}

BACKEND_IGNORE = {"TargetLoweringObjectFile.cpp", "CMakeLists.txt"}


def load(release: str):
    key   = release.replace(".", "_")
    prs   = json.load((DATA_DIR / f"prs_{key}.json").open())
    files = json.load((DATA_DIR / f"files_{key}.json").open())
    merged = [pr for pr in prs if pr.get("merged_at")]
    return merged, {int(k): v for k, v in files.items()}


def count_backends(merged, files) -> collections.Counter:
    """Count PRs per backend. A PR touching multiple backends counts for each."""
    ctr: collections.Counter = collections.Counter()
    for pr in merged:
        backends: set[str] = set()
        for path in files.get(pr["number"], []):
            parts = path.split("/")
            # llvm/lib/Target/<Backend>/...
            if (len(parts) >= 4
                    and parts[0] == "llvm"
                    and parts[1] == "lib"
                    and parts[2] == "Target"
                    and parts[3] not in BACKEND_IGNORE):
                backends.add(parts[3])
        for b in backends:
            ctr[b] += 1
    return ctr


def count_subsystems(merged, files) -> collections.Counter:
    """Count PRs per llvm/lib subsystem. A PR can count for multiple."""
    ctr: collections.Counter = collections.Counter()
    for pr in merged:
        subsystems: set[str] = set()
        for path in files.get(pr["number"], []):
            parts = path.split("/")
            # llvm/lib/<Subsystem>/...
            if len(parts) >= 3 and parts[0] == "llvm" and parts[1] == "lib":
                label = SUBSYSTEM_MAP.get(parts[2])
                if label:
                    subsystems.add(label)
        for s in subsystems:
            ctr[s] += 1
    return ctr


# ── aggregate ──────────────────────────────────────────────────────────────

backend_by_release:   dict[str, collections.Counter] = {}
subsystem_by_release: dict[str, collections.Counter] = {}

for release in RELEASES:
    merged, files = load(release)
    backend_by_release[release]   = count_backends(merged, files)
    subsystem_by_release[release] = count_subsystems(merged, files)

    print(f"{release} backends:   {backend_by_release[release].most_common(5)}")
    print(f"{release} subsystems: {subsystem_by_release[release].most_common(5)}")


def top_n_combined(by_release: dict, n: int) -> list[str]:
    combined: collections.Counter = collections.Counter()
    for c in by_release.values():
        combined.update(c)
    return [k for k, _ in combined.most_common(n)]


def grouped_bar(by_release: dict, labels: list[str],
                out_path: Path, ylabel: str = "PRs touching") -> None:
    n_releases = len(RELEASES)
    bar_w = 0.22
    x     = np.arange(len(labels)) * (n_releases * bar_w + 0.18)

    fig, ax = plt.subplots(figsize=(max(11, len(labels) * 1.05), 5.5))
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
                        bar.get_height() + 0.3,
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


top_backends   = top_n_combined(backend_by_release,   12)
top_subsystems = top_n_combined(subsystem_by_release, 12)

grouped_bar(backend_by_release,   top_backends,
            OUT_DIR / "llvm_backends.png",
            ylabel="PRs touching backend")

grouped_bar(subsystem_by_release, top_subsystems,
            OUT_DIR / "llvm_subsystems.png",
            ylabel="PRs touching subsystem")
