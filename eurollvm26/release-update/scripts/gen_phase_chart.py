"""Generate a grouped bar chart of PRs merged per RC phase per release."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "release_stats.json"
OUT_FILE  = Path(__file__).parent.parent / "phase_chart.png"

BACKGROUND = "#ffffff"
TEXT_COLOR  = "#1a1a2e"
PURPLE      = "#3b1f7a"

PHASE_LABELS = {
    "branch→rc1": "Branch\n→ RC1",
    "rc1→rc2":    "RC1\n→ RC2",
    "rc2→rc3":    "RC2\n→ RC3",
    "rc3→final":  "RC3\n→ Final",
    "post-final":  "Point\nReleases",
}
PHASES = list(PHASE_LABELS.keys())

RELEASE_COLORS = {
    "20.x": "#b39ddb",   # light purple
    "21.x": "#7c4dbd",   # mid purple
    "22.x": "#3b1f7a",   # dark purple
}

with DATA_FILE.open() as f:
    stats = json.load(f)

releases = list(stats.keys())
n_phases  = len(PHASES)
n_releases = len(releases)

bar_w  = 0.22
gap    = 0.08
group_w = n_releases * bar_w + gap
x = np.arange(n_phases) * (group_w + 0.18)

fig, ax = plt.subplots(figsize=(13, 5.5))
fig.patch.set_facecolor(BACKGROUND)
ax.set_facecolor(BACKGROUND)

for i, release in enumerate(releases):
    counts = [stats[release]["phase_counts"][p] for p in PHASES]
    offset = (i - (n_releases - 1) / 2) * bar_w
    bars = ax.bar(
        x + offset, counts, bar_w,
        color=RELEASE_COLORS[release],
        label=f"LLVM {release}",
        zorder=3,
    )
    # value labels on top of each bar
    for bar, count in zip(bars, counts):
        if count > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 3,
                str(count),
                ha="center", va="bottom",
                fontsize=9, fontweight="bold",
                color=TEXT_COLOR,
            )

# Styling
ax.set_xticks(x)
ax.set_xticklabels([PHASE_LABELS[p] for p in PHASES],
                   fontsize=12, color=TEXT_COLOR, linespacing=1.4)
ax.set_ylabel("PRs merged", fontsize=12, color=TEXT_COLOR, labelpad=10)
ax.tick_params(axis="y", labelsize=10, colors=TEXT_COLOR)
ax.tick_params(axis="x", length=0)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.spines["bottom"].set_color("#e0d7f5")
ax.yaxis.grid(True, color="#e0d7f5", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)

legend = ax.legend(
    fontsize=11,
    frameon=False,
    labelcolor=TEXT_COLOR,
    loc="upper right",
)

plt.tight_layout(pad=0.5)
plt.savefig(OUT_FILE, dpi=180, bbox_inches="tight",
            facecolor=BACKGROUND, edgecolor="none")
print(f"Saved → {OUT_FILE}")
