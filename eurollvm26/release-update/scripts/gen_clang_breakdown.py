"""
Drill down into Clang activity across releases.

Chart: clang_subsystems.png — PRs touching each Clang subsystem/tool,
grouped by release.

Attribution: a PR is counted for a subsystem if it touches ≥1 file there.
A PR can appear in multiple buckets (e.g. touching both Sema and AST).
"""
import json
import collections
from dedup import deduped_merged
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
RELEASE_COLORS = {"20.x": "#e65100", "21.x": "#1565c0", "22.x": "#2e7d32"}

# Maps (root, subpath_prefix) → display label.
# A file matches if its parts start with the given prefix tuple.
SUBSYSTEM_MAP = [
    (("clang", "lib", "Sema"),              "Sema"),
    (("clang", "lib", "AST"),               "AST"),
    (("clang", "lib", "CodeGen"),           "CodeGen"),
    (("clang", "lib", "Driver"),            "Driver"),
    (("clang", "lib", "Frontend"),          "Frontend"),
    (("clang", "lib", "Lex"),               "Lex/Parse"),
    (("clang", "lib", "Parse"),             "Lex/Parse"),
    (("clang", "lib", "Format"),            "clang-format"),
    (("clang", "tools", "clang-format"),    "clang-format"),
    (("clang", "lib", "StaticAnalyzer"),    "StaticAnalyzer"),
    (("clang", "lib", "Analysis"),          "Analysis"),
    (("clang", "lib", "Basic"),             "Basic"),
    (("clang", "lib", "Interpreter"),       "Interpreter"),
    (("clang-tools-extra", "clang-tidy"),   "clang-tidy"),
    (("clang-tools-extra", "clangd"),       "clangd"),
]


def load(release: str):
    key   = release.replace(".", "_")
    files = json.load((DATA_DIR / f"files_{key}.json").open())
    merged = deduped_merged(release)
    return merged, {int(k): v for k, v in files.items()}


def count_subsystems(merged, files) -> collections.Counter:
    ctr: collections.Counter = collections.Counter()
    for pr in merged:
        touched: set[str] = set()
        for path in files.get(pr["number"], []):
            parts = tuple(path.split("/"))
            for prefix, label in SUBSYSTEM_MAP:
                if parts[:len(prefix)] == prefix:
                    touched.add(label)
        for label in touched:
            ctr[label] += 1
    return ctr


# ── aggregate ──────────────────────────────────────────────────────────────

by_release: dict[str, collections.Counter] = {}
for release in RELEASES:
    merged, files = load(release)
    by_release[release] = count_subsystems(merged, files)
    print(f"{release}: {by_release[release].most_common()}")

# Pick labels: union across releases, sorted by combined total, top 12
combined: collections.Counter = collections.Counter()
for c in by_release.values():
    combined.update(c)
labels = [k for k, _ in combined.most_common(12)]

# ── plot ───────────────────────────────────────────────────────────────────

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
ax.set_ylabel("PRs touching subsystem", fontsize=11, color=TEXT_COLOR, labelpad=8)
ax.tick_params(axis="y", labelsize=9, colors=TEXT_COLOR)
ax.tick_params(axis="x", length=0)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.spines["bottom"].set_color("#e0d7f5")
ax.yaxis.grid(True, color="#e0d7f5", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
ax.legend(fontsize=10, frameon=False, labelcolor=TEXT_COLOR, loc="upper right")

plt.tight_layout(pad=0.6)
out = OUT_DIR / "clang_subsystems.png"
plt.savefig(out, dpi=180, bbox_inches="tight",
            facecolor=BACKGROUND, edgecolor="none")
plt.close()
print(f"Saved → {out}")
