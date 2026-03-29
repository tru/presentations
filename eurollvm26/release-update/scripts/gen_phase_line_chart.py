"""
Line chart: PRs merged per phase window, one line per release.
X-axis = milestone (RC1, RC2, …, Final, 1.1, 1.2, …)
Y-axis = PRs merged in the window *ending* at that milestone.
"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
OUT_FILE = Path(__file__).parent.parent / "phase_line_chart.png"

BACKGROUND = "#ffffff"
TEXT_COLOR  = "#1a1a2e"
GRID_COLOR  = "#e8e0f5"

RELEASE_STYLE = {
    "20.x": {"color": "#9575cd", "lw": 2.5, "marker": "o", "ms": 7},
    "21.x": {"color": "#512da8", "lw": 2.5, "marker": "s", "ms": 7},
    "22.x": {"color": "#1a0050", "lw": 2.5, "marker": "^", "ms": 8},
}

# Complete milestone dates per release, in order
MILESTONES = {
    "20.x": [
        ("branch", "2025-01-14T00:00:00Z"),
        ("RC1",    "2025-02-02T02:07:38Z"),
        ("RC2",    "2025-02-12T06:07:31Z"),
        ("RC3",    "2025-02-26T02:03:45Z"),
        ("Final",  "2025-03-04T20:05:00Z"),
        ("1.1",    "2025-03-18T23:22:59Z"),
        ("1.2",    "2025-04-02T00:16:12Z"),
        ("1.3",    "2025-04-16T00:31:25Z"),
        ("1.4",    "2025-04-30T00:24:15Z"),
        ("1.5",    "2025-05-14T18:15:37Z"),
        ("1.6",    "2025-05-28T18:40:36Z"),
        ("1.7",    "2025-06-13T04:56:21Z"),
        ("1.8",    "2025-07-09T03:18:35Z"),
    ],
    "21.x": [
        ("branch", "2025-07-08T00:00:00Z"),
        ("RC1",    "2025-07-17T19:06:25Z"),
        ("RC2",    "2025-07-29T14:36:22Z"),
        ("RC3",    "2025-08-12T09:04:38Z"),
        ("Final",  "2025-08-26T14:21:33Z"),
        ("1.1",    "2025-09-10T07:49:19Z"),
        ("1.2",    "2025-09-23T21:14:14Z"),
        ("1.3",    "2025-10-07T12:54:32Z"),
        ("1.4",    "2025-10-21T08:23:17Z"),
        ("1.5",    "2025-11-04T08:49:10Z"),
        ("1.6",    "2025-11-18T10:38:16Z"),
        ("1.7",    "2025-12-02T07:57:57Z"),
        ("1.8",    "2025-12-16T10:21:34Z"),
    ],
    "22.x": [
        ("branch", "2026-01-13T00:00:00Z"),
        ("RC1",    "2026-01-16T09:13:22Z"),
        ("RC2",    "2026-01-27T08:33:55Z"),
        ("RC3",    "2026-02-10T07:57:37Z"),
        ("Final",  "2026-02-24T07:36:08Z"),
        ("1.1",    "2026-03-11T00:33:19Z"),
        ("1.2",    "2026-03-24T20:04:07Z"),
    ],
}

# The full x-axis label sequence (union of all windows, excluding "branch")
X_LABELS = ["RC1", "RC2", "RC3", "Final",
             "1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8"]


def parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def bucket_prs(release: str) -> dict[str, int]:
    """Return {label: count} for each window in this release."""
    key   = release.replace(".", "_")
    prs   = json.load((DATA_DIR / f"prs_{key}.json").open())
    merged_prs = [pr for pr in prs if pr.get("merged_at")]

    milestones = MILESTONES[release]
    # Build list of (label, start_dt, end_dt)
    windows = []
    for i in range(1, len(milestones)):
        label    = milestones[i][0]
        start_dt = parse_dt(milestones[i - 1][1])
        end_dt   = parse_dt(milestones[i][1])
        windows.append((label, start_dt, end_dt))

    counts = {label: 0 for label, _, _ in windows}
    for pr in merged_prs:
        t = parse_dt(pr["merged_at"])
        for label, start, end in windows:
            if start <= t < end:
                counts[label] += 1
                break

    return counts


# ── compute ────────────────────────────────────────────────────────────────

release_data: dict[str, dict[str, int]] = {}
for release in MILESTONES:
    release_data[release] = bucket_prs(release)
    print(f"{release}: {release_data[release]}")

# ── plot ───────────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=(14, 5.5))
fig.patch.set_facecolor(BACKGROUND)
ax.set_facecolor(BACKGROUND)

for release, counts in release_data.items():
    style   = RELEASE_STYLE[release]
    ms_list = MILESTONES[release]
    # x positions = index of each label in the full X_LABELS list
    xs, ys = [], []
    for label, _, _ in [(m[0], None, None) for m in ms_list[1:]]:
        if label in X_LABELS:
            xs.append(X_LABELS.index(label))
            ys.append(counts.get(label, 0))

    ax.plot(xs, ys,
            color=style["color"],
            linewidth=style["lw"],
            marker=style["marker"],
            markersize=style["ms"],
            markerfacecolor="#ffffff",
            markeredgecolor=style["color"],
            markeredgewidth=2,
            label=f"LLVM {release}",
            zorder=3)

    # value labels above each point
    for x, y in zip(xs, ys):
        ax.annotate(str(y),
                    xy=(x, y),
                    xytext=(0, 9),
                    textcoords="offset points",
                    ha="center", va="bottom",
                    fontsize=8.5, fontweight="bold",
                    color=style["color"])

# shaded RC region
ax.axvspan(-0.5, 3.5, color="#f5f0ff", zorder=0, label="_nolegend_")
ax.text(1.5, ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 140,
        "← RC period →", ha="center", va="top",
        fontsize=9, color="#7c4dbd", style="italic")

# vertical line at Final
ax.axvline(3, color="#c0b0e0", linewidth=1, linestyle="--", zorder=1)

ax.set_xticks(range(len(X_LABELS)))
ax.set_xticklabels(X_LABELS, fontsize=11, color=TEXT_COLOR)
ax.set_ylabel("PRs merged in window", fontsize=11, color=TEXT_COLOR, labelpad=8)
ax.tick_params(axis="y", labelsize=9, colors=TEXT_COLOR)
ax.tick_params(axis="x", length=0)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.spines["bottom"].set_color(GRID_COLOR)
ax.yaxis.grid(True, color=GRID_COLOR, linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
ax.set_xlim(-0.5, len(X_LABELS) - 0.5)

legend = ax.legend(fontsize=11, frameon=False,
                   labelcolor=TEXT_COLOR, loc="upper right")

plt.tight_layout(pad=0.5)
plt.savefig(OUT_FILE, dpi=180, bbox_inches="tight",
            facecolor=BACKGROUND, edgecolor="none")
print(f"\nSaved → {OUT_FILE}")
