"""Generate a release timeline graphic similar to pre_release_reality.jpg"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import date
from pathlib import Path

BACKGROUND = "#ffffff"
BAR_COLOR  = "#3b1f7a"
TEXT_COLOR = "#1a1a2e"
DATE_COLOR = "#7a5fa8"

milestones = [
    ("release/21.x", date(2025, 7, 8)),
    ("21.1.0-rc1",   date(2025, 7, 17)),
    ("21.1.0-rc2",   date(2025, 7, 29)),
    ("21.1.0-rc3",   date(2025, 8, 12)),
    ("21.1.0",       date(2025, 8, 26)),
]

origin = milestones[0][1]
positions = [(label, (d - origin).days) for label, d in milestones]
total_span = positions[-1][1]

fig, ax = plt.subplots(figsize=(16, 3.6))
fig.patch.set_facecolor(BACKGROUND)
ax.set_facecolor(BACKGROUND)
ax.axis("off")

left_pad  = 0.07 * total_span
right_pad = 0.07 * total_span
x_min = -left_pad
x_max = total_span + right_pad
ax.set_xlim(x_min, x_max)
ax.set_ylim(-1.8, 1.8)

BAR_Y   = 0.0
LABEL_Y = 0.65    # version label above bar
DATE_Y  = 0.28    # date just above bar
TICK_BOT = -0.22
BRACE_Y = -0.60
DUR_Y   = -1.05

# horizontal bar
ax.plot([0, total_span], [BAR_Y, BAR_Y],
        color=BAR_COLOR, linewidth=10, solid_capstyle="round", zorder=2)

for i, (label, x) in enumerate(positions):
    d = milestones[i][1]
    date_str = d.strftime("%-d %b")

    # tick down
    ax.plot([x, x], [TICK_BOT, BAR_Y],
            color=BAR_COLOR, linewidth=2, zorder=3)

    # version label — bold, large, no box
    ax.text(x, LABEL_Y, label,
            ha="center", va="bottom", fontsize=14, fontweight="bold",
            color=TEXT_COLOR, zorder=5)

    # date — smaller, muted purple, directly above bar
    ax.text(x, DATE_Y, date_str,
            ha="center", va="bottom", fontsize=11,
            color=DATE_COLOR, zorder=5)

    # duration brace between consecutive milestones
    if i > 0:
        x_prev = positions[i - 1][1]
        mid    = (x_prev + x) / 2
        delta  = (milestones[i][1] - milestones[i - 1][1]).days
        brace_h = 0.12
        ax.plot([x_prev + 0.4, x_prev + 0.4, x - 0.4, x - 0.4],
                [BRACE_Y + brace_h, BRACE_Y, BRACE_Y, BRACE_Y + brace_h],
                color=TEXT_COLOR, linewidth=1.4, zorder=3)
        ax.text(mid, DUR_Y, f"{delta} days",
                ha="center", va="top", fontsize=12,
                color=TEXT_COLOR, zorder=5)

# dot markers on bar
for label, x in positions:
    ax.plot(x, BAR_Y, "o", color="#ffffff", markersize=10,
            markeredgecolor=BAR_COLOR, markeredgewidth=3, zorder=6)

plt.tight_layout(pad=0.2)
out = Path(__file__).parent.parent / "release_timeline.png"
plt.savefig(out, dpi=180, bbox_inches="tight",
            facecolor=BACKGROUND, edgecolor="none")
print(f"Saved to {out}")
