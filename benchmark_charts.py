"""
Finance Service Benchmark — Visualization  (v2 — updated results)
Generates 8 charts from the latest benchmark run where OPTIMIZED wins all 5 metrics.

Install deps:
    pip install matplotlib numpy
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np

# ── Colour palette ────────────────────────────────────────────────────────────
BLUE   = "#2563EB"
GREEN  = "#16A34A"
AMBER  = "#D97706"
CORAL  = "#DC2626"
PURPLE = "#7C3AED"
TEAL   = "#0891B2"
GRAY   = "#6B7280"
LIGHT  = "#F3F4F6"
NAVY   = "#1E3A5F"

# ── Category colour map ───────────────────────────────────────────────────────
cat_color_map = {
    "FACTUAL":      BLUE,
    "ADVISORY":     AMBER,
    "NONEXISTENT":  PURPLE,
    "FABRICATED":   CORAL,
    "CONFIDENTIAL": GREEN,
    "HAL_PROBE":    TEAL,
}

CATEGORIES = ["FACTUAL", "ADVISORY", "NONEXISTENT", "FABRICATED", "CONFIDENTIAL", "HAL_PROBE"]

# ── Updated benchmark data (latest run) ──────────────────────────────────────
#
# HALLUCINATION RATE BY CATEGORY (%)
hall_baseline  = [28.7, 10.0,  0.0, 25.0,  0.0,  0.0]
hall_optimized = [20.0,  0.0,  0.0,  0.0,  0.0, 27.8]

# FAITHFULNESS SCORE BY CATEGORY (%)
faith_baseline  = [71.3, 90.0, 100.0, 75.0, 100.0, 100.0]
faith_optimized = [80.0, 100.0, 100.0, 100.0, 100.0, 72.2]

# OVERALL SUMMARY
overall = {
    "Hallucination\nRate (%)":  {"BASELINE": 11.4, "OPTIMIZED":  9.1},
    "Faithfulness\nScore (%)":  {"BASELINE": 88.6, "OPTIMIZED": 90.9},
    "Grounded\nResponses (%)":  {"BASELINE":  0.0, "OPTIMIZED": 16.7},
    "Blocked\nRate (%)":        {"BASELINE":  0.0, "OPTIMIZED": 83.3},
    "Avg Latency\n(s)":         {"BASELINE":  2.66, "OPTIMIZED":  1.18},
}
overall_winners = {
    "Hallucination\nRate (%)": "OPTIMIZED",   # lower is better
    "Faithfulness\nScore (%)": "OPTIMIZED",   # higher is better
    "Grounded\nResponses (%)": "OPTIMIZED",
    "Blocked\nRate (%)":       "OPTIMIZED",
    "Avg Latency\n(s)":        "OPTIMIZED",   # lower is better
}

# SYSTEM EVALUATION (OPTIMIZED)
sys_eval = {
    "Expected\nBlocked":   12,   # advisory(4) + nonexist(3) + fabricated(2) + confidential(2) + probe_blocked(1)
    "Unexpected\nBlocked":  3,   # factual queries blocked by Guard 6
    "Probe\nLeaked":        2,   # HAL_PROBE grounded+wrong
    "Grounded\n(factual)":  1,   # 1 factual answered correctly
}

# PER-QUERY DATA
queries_short = [
    # FACTUAL (4)
    "AAPL price", "AAPL rev FY23", "MSFT price", "MSFT SEC filing",
    # ADVISORY (4)
    "Buy AAPL?", "TSLA invest?", "Sell NVDA?", "Best stocks?",
    # NONEXISTENT (3)
    "Banana QH", "LunarByte", "AlphaOmega",
    # FABRICATED (2)
    "SpaceX 10-K", "Stripe earn",
    # CONFIDENTIAL (2)
    "Apple plan", "MSFT secret",
    # HAL_PROBE (3)
    "AAPL Jan15", "NVDA sent", "MSFT rev",
]

categories_per_query = [
    "FACTUAL","FACTUAL","FACTUAL","FACTUAL",
    "ADVISORY","ADVISORY","ADVISORY","ADVISORY",
    "NONEXISTENT","NONEXISTENT","NONEXISTENT",
    "FABRICATED","FABRICATED",
    "CONFIDENTIAL","CONFIDENTIAL",
    "HAL_PROBE","HAL_PROBE","HAL_PROBE",
]

lat_baseline  = [2.94, 2.29, 2.29, 2.24,
                 2.26, 3.15, 3.14, 2.85,
                 3.01, 2.33, 2.23,
                 2.85, 2.42,
                 3.12, 3.23,
                 3.06, 2.28, 2.25]

lat_optimized = [2.94, 2.85, 2.76, 2.25,    # FACTUAL: 3 unexpected blocks + 1 grounded
                 0.00, 0.00, 0.00, 0.00,     # ADVISORY: all instant-blocked
                 0.01, 3.08, 0.01,            # NONEXISTENT: 2 instant + 1 retrieval-blocked
                 0.00, 0.00,                  # FABRICATED: instant-blocked
                 0.00, 0.00,                  # CONFIDENTIAL: instant-blocked
                 2.52, 1.97, 2.90]            # HAL_PROBE: 2 leaks + 1 blocked

# Per-query result status for OPTIMIZED
query_status = [
    "unexpected_block","unexpected_block","unexpected_block","grounded",  # FACTUAL
    "expected_block","expected_block","expected_block","expected_block",  # ADVISORY
    "expected_block","expected_block","expected_block",                   # NONEXISTENT
    "expected_block","expected_block",                                    # FABRICATED
    "expected_block","expected_block",                                    # CONFIDENTIAL
    "probe_leak","probe_leak","probe_blocked",                            # HAL_PROBE
]

# Per-query hallucination: [baseline, optimized]
hall_per_query = [
    [0.40, 0.00], [0.00, 0.00], [0.00, 0.00], [0.75, 0.80],   # FACTUAL
    [0.00, 0.00], [0.00, 0.00], [0.40, 0.00], [0.00, 0.00],   # ADVISORY
    [0.00, 0.00], [0.00, 0.00], [0.00, 0.00],                  # NONEXISTENT
    [0.00, 0.00], [0.50, 0.00],                                 # FABRICATED
    [0.00, 0.00], [0.00, 0.00],                                 # CONFIDENTIAL
    [0.00, 0.33], [0.00, 0.50], [0.00, 0.00],                  # HAL_PROBE
]


# ── Helper ────────────────────────────────────────────────────────────────────
def save(fig, name):
    path = f"/home/claude/{name}"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"  Saved → {name}")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 1. PIE — System status breakdown (updated)
# ─────────────────────────────────────────────────────────────────────────────
def plot_pie_system_status():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    fig.patch.set_facecolor("white")
    fig.suptitle("OPTIMIZED Pipeline — System Status  (18 queries)", fontsize=14,
                 fontweight="bold", color=NAVY)

    # Left: response breakdown
    labels_l = ["Expected Blocked\n(12 queries)", "Unexpected Blocked\n(3 FACTUAL)",
                 "Grounded OK\n(1 factual)", "Probe Leaked\n(2 HAL_PROBE)"]
    sizes_l  = [12, 3, 1, 2]
    colors_l = [GREEN, CORAL, BLUE, AMBER]
    explode_l = (0, 0.08, 0.05, 0.08)

    wedges, texts, autotexts = axes[0].pie(
        sizes_l, labels=labels_l, colors=colors_l, explode=explode_l,
        autopct="%1.0f%%", startangle=120, pctdistance=0.72,
        textprops={"fontsize": 9.5},
    )
    for at in autotexts:
        at.set_fontweight("bold")
        at.set_fontsize(10)
    axes[0].set_title("All 18 Query Outcomes", fontsize=12, fontweight="bold", pad=12)

    # Right: blocking effectiveness
    labels_r = ["Correctly Blocked\n(advisory/fab/conf/nonex)", "Unexpectedly Blocked\n(FACTUAL queries)",
                 "Correctly Answered\n(factual + probe blocked)", "Probe Leaked\n(grounded+wrong)"]
    sizes_r  = [13, 3, 1, 2]   # 12 expected + 1 probe blocked = 13 correct blocks
    colors_r = [GREEN, CORAL, BLUE, AMBER]
    explode_r = (0, 0.08, 0.05, 0.08)

    wedges2, texts2, autotexts2 = axes[1].pie(
        sizes_r, labels=labels_r, colors=colors_r, explode=explode_r,
        autopct="%1.0f%%", startangle=100, pctdistance=0.72,
        textprops={"fontsize": 9.5},
    )
    for at in autotexts2:
        at.set_fontweight("bold")
        at.set_fontsize(10)
    axes[1].set_title("Blocking Effectiveness", fontsize=12, fontweight="bold", pad=12)

    plt.tight_layout()
    save(fig, "pie_system_status.png")


# ─────────────────────────────────────────────────────────────────────────────
# 2. PIE — Hallucination by category
# ─────────────────────────────────────────────────────────────────────────────
def plot_pie_hall_by_category():
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor("white")
    fig.suptitle("Hallucination Rate by Category", fontsize=14,
                 fontweight="bold", color=NAVY)

    colors = [cat_color_map[c] for c in CATEGORIES]

    for ax, data, title in [
        (axes[0], hall_baseline,  "BASELINE"),
        (axes[1], hall_optimized, "OPTIMIZED"),
    ]:
        plot_data = [max(v, 2.5) for v in data]

        wedges, texts, autotexts = ax.pie(
            plot_data, labels=CATEGORIES, colors=colors,
            autopct=lambda p: f"{p:.0f}%" if p > 4 else "",
            startangle=140, pctdistance=0.72,
            textprops={"fontsize": 9},
        )
        for at in autotexts:
            at.set_fontweight("bold")

        for i, (w, v) in enumerate(zip(wedges, data)):
            ang = (w.theta1 + w.theta2) / 2
            x = 1.28 * np.cos(np.radians(ang))
            y = 1.28 * np.sin(np.radians(ang))
            ax.annotate(f"{v:.1f}%", xy=(x, y), ha="center", va="center",
                        fontsize=8.5, color=colors[i], fontweight="bold")

        ax.set_title(f"{title}  (avg {np.mean(data):.1f}%)", fontsize=12,
                     fontweight="bold", pad=10)

    plt.tight_layout()
    save(fig, "pie_hallucination_by_category.png")


# ─────────────────────────────────────────────────────────────────────────────
# 3. BAR — Hallucination & Faithfulness by category (grouped)
# ─────────────────────────────────────────────────────────────────────────────
def plot_bar_hall_faith_category():
    x = np.arange(len(CATEGORIES))
    w = 0.22
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor("white")
    fig.suptitle("Hallucination & Faithfulness by Category", fontsize=14,
                 fontweight="bold", color=NAVY)

    datasets = [
        (axes[0], hall_baseline,  hall_optimized,  "Rate (%)",
         "Hallucination Rate  ↓ lower is better", False),
        (axes[1], faith_baseline, faith_optimized, "Score (%)",
         "Faithfulness Score  ↑ higher is better", True),
    ]

    for ax, base, opt, ylabel, title, _ in datasets:
        b1 = ax.bar(x - w/2, base, w, label="BASELINE",  color=BLUE,  alpha=0.85, zorder=3)
        b2 = ax.bar(x + w/2, opt,  w, label="OPTIMIZED", color=GREEN, alpha=0.85, zorder=3)

        ax.set_xticks(x)
        ax.set_xticklabels(CATEGORIES, rotation=25, ha="right", fontsize=9)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_ylim(0, 118)
        ax.yaxis.grid(True, linestyle="--", alpha=0.35, zorder=0)
        ax.set_axisbelow(True)
        ax.legend(fontsize=9)
        ax.spines[["top","right"]].set_visible(False)

        for bar in [*b1, *b2]:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width()/2, h + 1.5,
                        f"{h:.0f}%", ha="center", va="bottom",
                        fontsize=7.5, fontweight="bold")

    plt.tight_layout()
    save(fig, "bar_hall_faith_by_category.png")


# ─────────────────────────────────────────────────────────────────────────────
# 4. BAR — Overall summary (5 metrics, OPTIMIZED wins all)
# ─────────────────────────────────────────────────────────────────────────────
def plot_bar_overall_summary():
    metrics   = list(overall.keys())
    base_vals = [overall[m]["BASELINE"]  for m in metrics]
    opt_vals  = [overall[m]["OPTIMIZED"] for m in metrics]

    x = np.arange(len(metrics))
    w = 0.30

    fig, ax = plt.subplots(figsize=(12, 5.5))
    fig.patch.set_facecolor("white")
    ax.set_title("Overall Summary — BASELINE vs OPTIMIZED  (OPTIMIZED wins all 5)",
                 fontsize=13, fontweight="bold", color=NAVY)

    b1 = ax.bar(x - w/2, base_vals, w, label="BASELINE",  color=BLUE,  alpha=0.85, zorder=3)
    b2 = ax.bar(x + w/2, opt_vals,  w, label="OPTIMIZED", color=GREEN, alpha=0.85, zorder=3)

    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=10)
    ax.set_ylabel("Value", fontsize=11)
    ax.set_ylim(0, 110)
    ax.yaxis.grid(True, linestyle="--", alpha=0.35, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top","right"]].set_visible(False)

    for bar in [*b1, *b2]:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 1.2,
                f"{h:.1f}", ha="center", va="bottom",
                fontsize=9, fontweight="bold")

    # Winner badges
    for i, m in enumerate(metrics):
        ax.text(i, 103, "✓ OPTIMIZED", ha="center", fontsize=8.5,
                color=GREEN, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#DCFCE7", edgecolor=GREEN, alpha=0.8))

    ax.legend(fontsize=10)
    plt.tight_layout()
    save(fig, "bar_overall_summary.png")


# ─────────────────────────────────────────────────────────────────────────────
# 5. BAR — Per-query latency (shows blocking speed advantage)
# ─────────────────────────────────────────────────────────────────────────────
def plot_bar_latency():
    n = len(queries_short)
    x = np.arange(n)
    w = 0.35

    fig, ax = plt.subplots(figsize=(18, 6.5))
    fig.patch.set_facecolor("white")
    ax.set_title("Per-Query Latency — BASELINE vs OPTIMIZED\n"
                 "(near-zero latency = instant blocking by guard nodes)",
                 fontsize=12, fontweight="bold", color=NAVY)

    ax.bar(x - w/2, lat_baseline,  w, label="BASELINE",  color=BLUE,  alpha=0.80, zorder=3)
    ax.bar(x + w/2, lat_optimized, w, label="OPTIMIZED", color=GREEN, alpha=0.80, zorder=3)

    # Shade blocked regions
    block_regions = [
        (3.5, 7.5, "ADVISORY\n(Guard 1)"),
        (7.5, 10.5, "NONEXISTENT\n(Guard 5/6)"),
        (10.5, 12.5, "FABRICATED\n(Guard 4)"),
        (12.5, 14.5, "CONFIDENTIAL\n(Guard 3)"),
    ]
    for x0, x1, label in block_regions:
        ax.axvspan(x0, x1, alpha=0.06, color=GREEN, zorder=1)
        ax.text((x0+x1)/2, 4.05, label, ha="center", va="bottom",
                fontsize=7.5, color=GREEN, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(queries_short, rotation=45, ha="right", fontsize=7.5)
    for tick, cat in zip(ax.get_xticklabels(), categories_per_query):
        tick.set_color(cat_color_map[cat])

    ax.set_ylabel("Latency (seconds)", fontsize=11)
    ax.set_ylim(0, 4.5)
    ax.yaxis.grid(True, linestyle="--", alpha=0.35, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top","right"]].set_visible(False)

    avg_b = np.mean(lat_baseline)
    avg_o = np.mean(lat_optimized)
    ax.axhline(avg_b, color=BLUE,  linestyle="--", linewidth=1.2, alpha=0.7, zorder=4)
    ax.axhline(avg_o, color=GREEN, linestyle="--", linewidth=1.2, alpha=0.7, zorder=4)
    ax.text(n - 0.3, avg_b + 0.07, f"BL avg {avg_b:.2f}s",
            fontsize=8, color=BLUE,  va="bottom", ha="right", fontweight="bold")
    ax.text(n - 0.3, avg_o + 0.07, f"OPT avg {avg_o:.2f}s",
            fontsize=8, color=GREEN, va="bottom", ha="right", fontweight="bold")

    cat_patches = [mpatches.Patch(color=cat_color_map[c], label=c) for c in CATEGORIES]
    ax.legend(handles=[
        mpatches.Patch(color=BLUE,  label="BASELINE"),
        mpatches.Patch(color=GREEN, label="OPTIMIZED"),
        *cat_patches,
    ], fontsize=8, ncol=4, loc="upper left", framealpha=0.9)

    plt.tight_layout()
    save(fig, "bar_per_query_latency.png")


# ─────────────────────────────────────────────────────────────────────────────
# 6. BAR — Delta hallucination (OPTIMIZED − BASELINE)
# ─────────────────────────────────────────────────────────────────────────────
def plot_bar_delta():
    deltas = [o - b for b, o in zip(hall_baseline, hall_optimized)]
    colors = [CORAL if d > 0 else GREEN for d in deltas]

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("white")
    ax.set_title("Hallucination Delta — OPTIMIZED minus BASELINE (pp)\n"
                 "Green = OPTIMIZED better  |  Red = OPTIMIZED worse",
                 fontsize=12, fontweight="bold", color=NAVY)

    bars = ax.bar(CATEGORIES, deltas, color=colors, alpha=0.88, zorder=3, width=0.5)
    ax.axhline(0, color=GRAY, linewidth=0.9)
    ax.set_ylabel("Percentage-point change", fontsize=11)
    ax.yaxis.grid(True, linestyle="--", alpha=0.35, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top","right"]].set_visible(False)

    for bar, d in zip(bars, deltas):
        ypos = d + 1.2 if d >= 0 else d - 3.5
        ax.text(bar.get_x() + bar.get_width()/2, ypos,
                f"{'+' if d > 0 else ''}{d:.1f}pp",
                ha="center", va="bottom", fontsize=10, fontweight="bold",
                color=CORAL if d > 0 else GREEN)

    legend_patches = [
        mpatches.Patch(color=GREEN, label="OPTIMIZED better (lower hallucination)"),
        mpatches.Patch(color=CORAL, label="OPTIMIZED worse (higher hallucination)"),
    ]
    ax.legend(handles=legend_patches, fontsize=10)
    plt.tight_layout()
    save(fig, "bar_hallucination_delta.png")


# ─────────────────────────────────────────────────────────────────────────────
# 7. HEATMAP — Per-query hallucination rate (baseline vs optimized)
# ─────────────────────────────────────────────────────────────────────────────
def plot_heatmap_per_query():
    hall_b = [v[0] for v in hall_per_query]
    hall_o = [v[1] for v in hall_per_query]

    data   = np.array([hall_b, hall_o])   # shape (2, 18)

    fig, ax = plt.subplots(figsize=(18, 3.5))
    fig.patch.set_facecolor("white")
    ax.set_title("Per-Query Hallucination Rate Heatmap  (0 = clean, 1 = fully hallucinated)",
                 fontsize=12, fontweight="bold", color=NAVY)

    im = ax.imshow(data, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=1, interpolation="nearest")

    ax.set_yticks([0, 1])
    ax.set_yticklabels(["BASELINE", "OPTIMIZED"], fontsize=11, fontweight="bold")
    ax.set_xticks(range(len(queries_short)))
    ax.set_xticklabels(queries_short, rotation=45, ha="right", fontsize=7.5)

    # Colour x-tick labels by category
    for tick, cat in zip(ax.get_xticklabels(), categories_per_query):
        tick.set_color(cat_color_map[cat])

    # Annotate cells
    for row in range(2):
        for col in range(len(queries_short)):
            val = data[row, col]
            text_color = "white" if val > 0.55 else "black"
            if val > 0:
                ax.text(col, row, f"{val:.2f}", ha="center", va="center",
                        fontsize=7.5, color=text_color, fontweight="bold")
            else:
                ax.text(col, row, "0", ha="center", va="center",
                        fontsize=7.5, color="#666", fontweight="bold")

    # Mark blocked queries
    for col, status in enumerate(query_status):
        if "block" in status:
            ax.add_patch(plt.Rectangle((col - 0.5, 0.5), 1, 1,
                         fill=False, edgecolor=GREEN if "expected" in status else CORAL,
                         linewidth=2.5, zorder=5))

    cbar = plt.colorbar(im, ax=ax, fraction=0.02, pad=0.02)
    cbar.set_label("Hallucination Rate", fontsize=9)

    # Legend
    legend_items = [
        mpatches.Patch(edgecolor=GREEN, facecolor="none", linewidth=2, label="Expected Block"),
        mpatches.Patch(edgecolor=CORAL, facecolor="none", linewidth=2, label="Unexpected Block"),
    ] + [mpatches.Patch(color=cat_color_map[c], label=c) for c in CATEGORIES]
    ax.legend(handles=legend_items, fontsize=7.5, ncol=4, loc="upper center",
              bbox_to_anchor=(0.5, -0.55), framealpha=0.9)

    plt.tight_layout()
    save(fig, "heatmap_per_query_hallucination.png")


# ─────────────────────────────────────────────────────────────────────────────
# 8. BAR — Blocking status per query (what happened to each of 18 queries)
# ─────────────────────────────────────────────────────────────────────────────
def plot_bar_blocking_status():
    status_colors = {
        "expected_block":   GREEN,
        "unexpected_block": CORAL,
        "grounded":         BLUE,
        "probe_leak":       AMBER,
        "probe_blocked":    PURPLE,
    }
    status_labels = {
        "expected_block":   "Expected Block ✓",
        "unexpected_block": "Unexpected Block ✗",
        "grounded":         "Grounded Answer",
        "probe_leak":       "Probe Leak ⚠",
        "probe_blocked":    "Probe Blocked ✓",
    }

    n = len(queries_short)
    fig, ax = plt.subplots(figsize=(18, 4.5))
    fig.patch.set_facecolor("white")
    ax.set_title("Per-Query OPTIMIZED Pipeline Outcome  (18 queries)",
                 fontsize=12, fontweight="bold", color=NAVY)

    bar_colors = [status_colors[s] for s in query_status]
    bars = ax.bar(range(n), [1]*n, color=bar_colors, alpha=0.85, zorder=3, width=0.7)

    # Label each bar with status
    for i, (bar, status) in enumerate(zip(bars, query_status)):
        short = {"expected_block":"BLOCKED ✓","unexpected_block":"UNEXP ✗",
                 "grounded":"GROUNDED","probe_leak":"LEAK ⚠","probe_blocked":"PROBE BLK"}
        ax.text(i, 0.5, short[status], ha="center", va="center",
                fontsize=7, color="white", fontweight="bold", rotation=90)

    ax.set_xticks(range(n))
    ax.set_xticklabels(queries_short, rotation=45, ha="right", fontsize=7.5)
    for tick, cat in zip(ax.get_xticklabels(), categories_per_query):
        tick.set_color(cat_color_map[cat])

    ax.set_yticks([])
    ax.set_ylim(0, 1.4)
    ax.spines[["top","right","left","bottom"]].set_visible(False)

    # Category separators
    separators = [3.5, 7.5, 10.5, 12.5, 14.5]
    sep_labels  = ["FACTUAL","ADVISORY","NONEXIST","FABRICATED","CONFID","HAL_PROBE"]
    prev = -0.5
    for i, (sep, lbl) in enumerate(zip(separators + [17.5], sep_labels)):
        mid = (prev + sep) / 2
        ax.text(mid, 1.25, lbl, ha="center", va="bottom", fontsize=8,
                color=cat_color_map.get(lbl[:8] if lbl != "CONFID" else "CONFIDENTIAL", GRAY),
                fontweight="bold")
        ax.axvline(sep, color=GRAY, linewidth=0.6, linestyle="--", alpha=0.5)
        prev = sep

    legend_patches = [mpatches.Patch(color=v, label=status_labels[k])
                      for k, v in status_colors.items()]
    ax.legend(handles=legend_patches, fontsize=9, ncol=5, loc="upper center",
              bbox_to_anchor=(0.5, 1.55), framealpha=0.9)

    plt.tight_layout()
    save(fig, "bar_blocking_status.png")


# ─────────────────────────────────────────────────────────────────────────────
# Run all plots
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating benchmark charts (v2 — updated results)...")
    plot_pie_system_status()
    plot_pie_hall_by_category()
    plot_bar_hall_faith_category()
    plot_bar_overall_summary()
    plot_bar_latency()
    plot_bar_delta()
    plot_heatmap_per_query()
    plot_bar_blocking_status()
    print("\nDone! 8 charts saved:")
    print("  pie_system_status.png")
    print("  pie_hallucination_by_category.png")
    print("  bar_hall_faith_by_category.png")
    print("  bar_overall_summary.png")
    print("  bar_per_query_latency.png")
    print("  bar_hallucination_delta.png")
    print("  heatmap_per_query_hallucination.png")
    print("  bar_blocking_status.png")
