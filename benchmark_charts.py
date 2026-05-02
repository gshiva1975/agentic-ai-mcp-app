"""
Finance Service Benchmark — Visualization
Generates pie and bar charts from benchmark results.

Install deps:
    pip install matplotlib numpy
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Colour palette ────────────────────────────────────────────────────────────
BLUE   = "#378ADD"
GREEN  = "#1D9E75"
AMBER  = "#EF9F27"
CORAL  = "#D85A30"
PURPLE = "#7F77DD"
RED    = "#E24B4A"
GRAY   = "#888780"
LIGHT  = "#F1EFE8"

# ── Raw data ──────────────────────────────────────────────────────────────────
CATEGORIES = ["FACTUAL", "ADVISORY", "NONEXISTENT", "FABRICATED", "CONFIDENTIAL", "HAL_PROBE"]

hall_baseline  = [30.0,  0.0,  0.0, 58.3, 0.0,  0.0]
hall_optimized = [33.8, 52.1, 22.2, 41.7, 0.0, 33.3]

faith_baseline  = [70.0, 100.0, 100.0, 41.7, 100.0, 100.0]
faith_optimized = [66.2,  47.9,  77.8, 58.3, 100.0,  66.7]

# Overall summary
overall = {
    "Hallucination Rate": {"BASELINE": 13.1, "OPTIMIZED": 33.0},
    "Faithfulness Score": {"BASELINE": 86.9, "OPTIMIZED": 67.0},
    "Grounded Responses": {"BASELINE":  0.0, "OPTIMIZED": 100.0},
    "Avg Latency (×10 s)": {"BASELINE": 23.5, "OPTIMIZED": 30.3},  # scaled ×10 for readability
}

# System evaluation (OPTIMIZED)
sys_eval = {
    "Grounded":          18,
    "Hallucinated":      12,
    "Probes Leaked":      3,
    "Unexpected Passes": 11,
    "Blocked":            0,
}

# Per-query latency
queries_short = [
    "AAPL price", "AAPL rev FY23", "AAPL SEC", "MSFT price",
    "AAPL invest?", "TSLA overval?", "NVDA buy?", "AAPL predict",
    "Banana QH", "LunarByte", "AlphaOmega",
    "Apple 2028 10-K", "MSFT 2027 SEC",
    "Apple AI road", "Tesla R&D",
    "AAPL Jan15", "NVDA sentiment", "MSFT rev",
]
categories_per_query = [
    "FACTUAL","FACTUAL","FACTUAL","FACTUAL",
    "ADVISORY","ADVISORY","ADVISORY","ADVISORY",
    "NONEXISTENT","NONEXISTENT","NONEXISTENT",
    "FABRICATED","FABRICATED",
    "CONFIDENTIAL","CONFIDENTIAL",
    "HAL_PROBE","HAL_PROBE","HAL_PROBE",
]
lat_baseline  = [2.99, 2.36, 2.30, 2.24, 2.26, 2.30, 2.33, 2.30,
                 2.48, 2.30, 2.28, 2.35, 2.30, 2.27, 2.29, 2.33, 2.30, 2.29]
lat_optimized = [2.85, 3.08, 2.92, 2.94, 2.88, 3.04, 3.12, 3.13,
                 3.09, 2.94, 2.98, 2.98, 2.94, 3.21, 3.25, 3.19, 3.04, 3.01]

cat_color_map = {
    "FACTUAL":      BLUE,
    "ADVISORY":     AMBER,
    "NONEXISTENT":  PURPLE,
    "FABRICATED":   CORAL,
    "CONFIDENTIAL": GREEN,
    "HAL_PROBE":    RED,
}


# ── Helper ────────────────────────────────────────────────────────────────────
def save(fig, name):
    fig.savefig(name, dpi=150, bbox_inches="tight")
    print(f"  Saved → {name}")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 1. PIE — Overall OPTIMIZED system status
# ─────────────────────────────────────────────────────────────────────────────
def plot_pie_system_status():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("OPTIMIZED Pipeline — System Status (18 queries)", fontsize=14, fontweight="bold")

    # Left: response quality breakdown
    labels_l = ["Clean (no hallucination)", "Hallucinated (hall > 0)", "Probes Leaked"]
    sizes_l  = [18 - 12, 12 - 3, 3]        # clean=6, hallucinated-not-leaked=9, leaked=3
    colors_l = [GREEN, AMBER, RED]
    explode_l = (0, 0.05, 0.1)

    wedges, texts, autotexts = axes[0].pie(
        sizes_l, labels=labels_l, colors=colors_l, explode=explode_l,
        autopct="%1.0f%%", startangle=140, pctdistance=0.75,
        textprops={"fontsize": 10},
    )
    for at in autotexts:
        at.set_fontweight("bold")
    axes[0].set_title("Response Quality", fontsize=12)

    # Right: blocking effectiveness
    labels_r = ["Should Block — Passed", "Should Block — Blocked", "Valid Queries — Passed"]
    sizes_r  = [11, 0, 7]   # 11 unexpected passes, 0 blocked, 7 legitimate
    colors_r = [RED, GREEN, BLUE]
    explode_r = (0.08, 0, 0)

    wedges2, texts2, autotexts2 = axes[1].pie(
        sizes_r, labels=labels_r, colors=colors_r, explode=explode_r,
        autopct="%1.0f%%", startangle=90, pctdistance=0.75,
        textprops={"fontsize": 10},
    )
    for at in autotexts2:
        at.set_fontweight("bold")
    axes[1].set_title("Blocking Effectiveness", fontsize=12)

    plt.tight_layout()
    save(fig, "pie_system_status.png")


# ─────────────────────────────────────────────────────────────────────────────
# 2. PIE — Hallucination rate split by category (OPTIMIZED)
# ─────────────────────────────────────────────────────────────────────────────
def plot_pie_hall_by_category():
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Hallucination Rate by Category", fontsize=14, fontweight="bold")

    colors = [cat_color_map[c] for c in CATEGORIES]

    for ax, data, title in [
        (axes[0], hall_baseline,  "BASELINE"),
        (axes[1], hall_optimized, "OPTIMIZED"),
    ]:
        # Show all categories; zero-rate ones show as thin slice for visibility
        plot_data = [max(v, 2) for v in data]   # floor at 2 so all wedges visible
        actual    = data

        wedges, texts, autotexts = ax.pie(
            plot_data, labels=CATEGORIES, colors=colors,
            autopct=lambda p: f"{p:.0f}%" if p > 3 else "",
            startangle=140, pctdistance=0.75,
            textprops={"fontsize": 9},
        )
        for at in autotexts:
            at.set_fontweight("bold")

        # Annotate actual values
        for i, (w, v) in enumerate(zip(wedges, actual)):
            ang = (w.theta1 + w.theta2) / 2
            x = 1.25 * np.cos(np.radians(ang))
            y = 1.25 * np.sin(np.radians(ang))
            ax.annotate(f"{v:.1f}%", xy=(x, y), ha="center", va="center",
                        fontsize=8, color=colors[i], fontweight="bold")

        ax.set_title(f"{title}  (avg {np.mean(actual):.1f}%)", fontsize=12)

    plt.tight_layout()
    save(fig, "pie_hallucination_by_category.png")


# ─────────────────────────────────────────────────────────────────────────────
# 3. BAR — Hallucination & Faithfulness by category (grouped)
# ─────────────────────────────────────────────────────────────────────────────
def plot_bar_hall_faith_category():
    x = np.arange(len(CATEGORIES))
    w = 0.2
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=False)
    fig.suptitle("Hallucination & Faithfulness by Category", fontsize=14, fontweight="bold")

    for ax, base, opt, ylabel, title, flip in [
        (axes[0], hall_baseline,  hall_optimized,  "Rate (%)", "Hallucination Rate ↓ lower is better", False),
        (axes[1], faith_baseline, faith_optimized, "Score (%)","Faithfulness Score ↑ higher is better", True),
    ]:
        b1 = ax.bar(x - w/2, base, w, label="BASELINE",  color=BLUE,  alpha=0.85, zorder=3)
        b2 = ax.bar(x + w/2, opt,  w, label="OPTIMIZED", color=CORAL, alpha=0.85, zorder=3)

        ax.set_xticks(x)
        ax.set_xticklabels(CATEGORIES, rotation=25, ha="right", fontsize=9)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_title(title, fontsize=11)
        ax.set_ylim(0, 115)
        ax.yaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)
        ax.set_axisbelow(True)
        ax.legend(fontsize=9)

        for bar in [*b1, *b2]:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width()/2, h + 1.5,
                        f"{h:.0f}%", ha="center", va="bottom", fontsize=7.5, fontweight="bold")

    plt.tight_layout()
    save(fig, "bar_hall_faith_by_category.png")


# ─────────────────────────────────────────────────────────────────────────────
# 4. BAR — Overall summary comparison
# ─────────────────────────────────────────────────────────────────────────────
def plot_bar_overall_summary():
    metrics = list(overall.keys())
    base_vals = [overall[m]["BASELINE"]  for m in metrics]
    opt_vals  = [overall[m]["OPTIMIZED"] for m in metrics]

    x = np.arange(len(metrics))
    w = 0.32

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.set_title("Overall Summary — BASELINE vs OPTIMIZED", fontsize=14, fontweight="bold")

    b1 = ax.bar(x - w/2, base_vals, w, label="BASELINE",  color=BLUE,  alpha=0.88, zorder=3)
    b2 = ax.bar(x + w/2, opt_vals,  w, label="OPTIMIZED", color=CORAL, alpha=0.88, zorder=3)

    ax.set_xticks(x)
    ax.set_xticklabels(
        ["Hallucination\nRate (%)", "Faithfulness\nScore (%)", "Grounded\nResponses (%)", "Avg Latency\n(s × 10)"],
        fontsize=10,
    )
    ax.set_ylabel("Value", fontsize=11)
    ax.set_ylim(0, 120)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(fontsize=10)

    for bar in [*b1, *b2]:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 1.5,
                f"{h:.1f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    # Annotate winners
    winners = ["BASELINE", "BASELINE", "OPTIMIZED", "BASELINE"]
    win_colors = [GREEN if w == "OPTIMIZED" else AMBER for w in winners]
    for i, (wn, wc) in enumerate(zip(winners, win_colors)):
        ax.text(i, 108, f"✓ {wn}", ha="center", fontsize=8, color=wc, fontweight="bold")

    note = "* Avg Latency scaled ×10 for chart readability  (BASELINE 2.35s, OPTIMIZED 3.03s)"
    ax.text(0.01, -0.18, note, transform=ax.transAxes, fontsize=8, color=GRAY)

    plt.tight_layout()
    save(fig, "bar_overall_summary.png")


# ─────────────────────────────────────────────────────────────────────────────
# 5. BAR — Per-query latency comparison
# ─────────────────────────────────────────────────────────────────────────────
def plot_bar_latency():
    n = len(queries_short)
    x = np.arange(n)
    w = 0.35

    fig, ax = plt.subplots(figsize=(18, 6))
    ax.set_title("Per-Query Latency — BASELINE vs OPTIMIZED", fontsize=13, fontweight="bold")

    ax.bar(x - w/2, lat_baseline,  w, label="BASELINE",  color=BLUE,  alpha=0.85, zorder=3)
    ax.bar(x + w/2, lat_optimized, w, label="OPTIMIZED", color=CORAL, alpha=0.85, zorder=3)

    # Colour x-tick labels by category
    ax.set_xticks(x)
    ax.set_xticklabels(queries_short, rotation=45, ha="right", fontsize=7.5)
    for tick, cat in zip(ax.get_xticklabels(), categories_per_query):
        tick.set_color(cat_color_map[cat])

    ax.set_ylabel("Latency (seconds)", fontsize=11)
    ax.set_ylim(0, 4.2)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(fontsize=10)

    # Category legend for x-tick colours
    cat_patches = [mpatches.Patch(color=cat_color_map[c], label=c) for c in CATEGORIES]
    ax.legend(handles=[
        mpatches.Patch(color=BLUE,  label="BASELINE"),
        mpatches.Patch(color=CORAL, label="OPTIMIZED"),
        *cat_patches,
    ], fontsize=8, ncol=4, loc="upper right")

    # Avg lines
    ax.axhline(np.mean(lat_baseline),  color=BLUE,  linestyle="--", linewidth=1, alpha=0.7,
               label=f"BASELINE avg {np.mean(lat_baseline):.2f}s")
    ax.axhline(np.mean(lat_optimized), color=CORAL, linestyle="--", linewidth=1, alpha=0.7,
               label=f"OPTIMIZED avg {np.mean(lat_optimized):.2f}s")

    ax.text(n - 0.5, np.mean(lat_baseline)  + 0.05, f"BL avg {np.mean(lat_baseline):.2f}s",
            fontsize=8, color=BLUE, va="bottom", ha="right")
    ax.text(n - 0.5, np.mean(lat_optimized) + 0.05, f"OPT avg {np.mean(lat_optimized):.2f}s",
            fontsize=8, color=CORAL, va="bottom", ha="right")

    plt.tight_layout()
    save(fig, "bar_per_query_latency.png")


# ─────────────────────────────────────────────────────────────────────────────
# 6. BAR — Delta (OPTIMIZED − BASELINE) hallucination by category
# ─────────────────────────────────────────────────────────────────────────────
def plot_bar_delta():
    deltas = [o - b for b, o in zip(hall_baseline, hall_optimized)]
    colors = [RED if d > 0 else GREEN for d in deltas]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_title("Hallucination Delta — OPTIMIZED minus BASELINE (pp)", fontsize=13, fontweight="bold")

    bars = ax.bar(CATEGORIES, deltas, color=colors, alpha=0.88, zorder=3, width=0.5)
    ax.axhline(0, color=GRAY, linewidth=0.8)
    ax.set_ylabel("Percentage-point change", fontsize=11)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)
    ax.set_axisbelow(True)

    for bar, d in zip(bars, deltas):
        ypos = d + 1.2 if d >= 0 else d - 3.5
        ax.text(bar.get_x() + bar.get_width()/2, ypos,
                f"{'+' if d>0 else ''}{d:.1f}pp",
                ha="center", va="bottom", fontsize=9, fontweight="bold",
                color=RED if d > 0 else GREEN)

    legend_patches = [
        mpatches.Patch(color=RED,   label="OPTIMIZED worse (▲)"),
        mpatches.Patch(color=GREEN, label="OPTIMIZED better (▼)"),
    ]
    ax.legend(handles=legend_patches, fontsize=10)

    plt.tight_layout()
    save(fig, "bar_hallucination_delta.png")


# ─────────────────────────────────────────────────────────────────────────────
# Run all plots
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating benchmark charts...")
    plot_pie_system_status()
    plot_pie_hall_by_category()
    plot_bar_hall_faith_category()
    plot_bar_overall_summary()
    plot_bar_latency()
    plot_bar_delta()
    print("\nDone! 6 charts saved:")
    print("  pie_system_status.png")
    print("  pie_hallucination_by_category.png")
    print("  bar_hall_faith_by_category.png")
    print("  bar_overall_summary.png")
    print("  bar_per_query_latency.png")
    print("  bar_hallucination_delta.png")
