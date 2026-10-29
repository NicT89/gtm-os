"""Brand-colored chart helpers (matplotlib). Each function writes a PNG and returns its path.

  from charts import Style, bar, line, gates, plan
  st = Style(primary="#F56A00", dark="#132b4a", accent="#31b7b9", font="DejaVu Sans")

Charts the report uses: bar (compare prices or counts), line (price history), gates (the five-gate
chevron strip), plan (30/60/90 columns). Draw only what the data supports: no estimated bars
without an "estimate" label, no axis that starts above zero for bars.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon


class Style:
    def __init__(self, primary="#F56A00", dark="#132b4a", accent="#31b7b9", ink="#0B2545", grid="#DDE3E8", font="DejaVu Sans"):
        self.primary, self.dark, self.accent, self.ink, self.grid, self.font = primary, dark, accent, ink, grid, font
        plt.rcParams.update({"font.family": font, "text.color": ink, "axes.edgecolor": grid, "axes.labelcolor": ink,
                             "xtick.color": ink, "ytick.color": ink, "axes.spines.top": False, "axes.spines.right": False})


def _money(label):  # matplotlib mathtext eats "$": always escape
    return str(label).replace("$", r"\$")


def bar(st, path, labels, values, title, unit="", highlight=None, estimate=()):
    fig, ax = plt.subplots(figsize=(7.2, 3.0), dpi=200)
    cols = [st.primary if (highlight is not None and i == highlight) else st.dark for i in range(len(values))]
    bars = ax.bar(labels, values, color=cols, width=0.55, hatch=None)
    for i, b in enumerate(bars):
        if i in estimate: b.set_hatch("//"); b.set_facecolor("white"); b.set_edgecolor(st.primary)
        ax.text(b.get_x() + b.get_width() / 2, b.get_height(), _money(f"{unit}{values[i]:,.0f}" + (" (est.)" if i in estimate else "")), ha="center", va="bottom", fontsize=8)
    ax.set_title(_money(title), loc="left", fontsize=10, color=st.dark, fontweight="bold")
    ax.yaxis.grid(True, color=st.grid, linewidth=0.6); ax.set_axisbelow(True); ax.set_ylim(0, max(values) * 1.18)
    fig.tight_layout(); fig.savefig(path); plt.close(fig); return path


def line(st, path, xs, ys, title, unit=""):
    fig, ax = plt.subplots(figsize=(7.2, 3.0), dpi=200)
    ax.plot(xs, ys, color=st.primary, marker="o", linewidth=2)
    for x, y in zip(xs, ys): ax.annotate(_money(f"{unit}{y:,.0f}"), (x, y), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8)
    ax.set_title(_money(title), loc="left", fontsize=10, color=st.dark, fontweight="bold")
    ax.yaxis.grid(True, color=st.grid, linewidth=0.6); ax.set_ylim(0, max(ys) * 1.25)
    fig.tight_layout(); fig.savefig(path); plt.close(fig); return path


def gates(st, path, names=("Pull", "Prove", "Pay", "Use", "Keep"), captions=None):
    """Chevron strip. captions: list of short strings under each gate (keep under 28 characters)."""
    fig, ax = plt.subplots(figsize=(7.2, 1.9), dpi=200); ax.set_xlim(0, len(names) * 2.0 + 0.4); ax.set_ylim(-1.2, 1.2); ax.axis("off")
    for i, n in enumerate(names):
        x = i * 2.0
        ax.add_patch(Polygon([(x, 0.7), (x + 1.7, 0.7), (x + 2.1, 0), (x + 1.7, -0.7), (x, -0.7), (x + 0.4, 0)], closed=True, color=st.dark if i % 2 == 0 else st.primary))
        ax.text(x + 1.0, 0, n, ha="center", va="center", color="white", fontsize=11, fontweight="bold")
        if captions: ax.text(x + 1.0, -0.98, captions[i], ha="center", va="center", fontsize=6.4, color=st.ink)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.05); plt.close(fig); return path


def plan(st, path, cols):
    """cols: [("Days 1 to 30", ["deliverable", ...]), ("Days 31 to 60", [...]), ("Days 61 to 90", [...])]; keep bullets under 38 characters."""
    fig, ax = plt.subplots(figsize=(7.2, 3.1), dpi=200); ax.set_xlim(0, 3); ax.set_ylim(0, 1); ax.axis("off")
    for i, (head, items) in enumerate(cols):
        ax.add_patch(FancyBboxPatch((i + 0.04, 0.05), 0.92, 0.9, boxstyle="round,pad=0.0,rounding_size=0.03", fc="#F4F6F9", ec=st.grid))
        ax.add_patch(FancyBboxPatch((i + 0.04, 0.80), 0.92, 0.15, boxstyle="round,pad=0.0,rounding_size=0.03", fc=st.dark if i != 1 else st.primary, ec="none"))
        ax.text(i + 0.5, 0.875, head, ha="center", va="center", color="white", fontsize=9, fontweight="bold")
        for j, it in enumerate(items[:5]): ax.text(i + 0.08, 0.72 - j * 0.14, "• " + _money(it), fontsize=6.6, va="top", color=st.ink, wrap=True)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.05); plt.close(fig); return path
