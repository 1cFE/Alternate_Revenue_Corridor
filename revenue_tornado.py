"""What moves each alternate-revenue stream: one tornado per co-product.

Every bar is one lever taken alone from its tier-0 setting to the deepest value
the evidence ladder reaches for it, measured as the LCOE reduction it buys.

The levers are evaluated ON THE TIER-3 PLANT, not the design basis, and that
choice matters.  At tier-0 economics none of these co-products pay: heat's
offtake lever is worth -$10.75 there, because $20/MWh-th sits below the
LCOE_e x eta_gen threshold of $44.20 and every extra MW-th diverted loses money.
A tornado anchored at the design basis would show the levers as harmful, which
is true but says more about the plant than about the co-product.  Anchoring at
tier 3 answers the question the dispatch actually asks -- once the plant is
cheap, what moves each stream.

The "all levers" bar is drawn hollow because for heat and synfuel it is much
larger than the sum of the parts: price and volume compound, so heat's three
levers are worth $18.4 separately and $45.4 together.  Gold's are nearly
additive ($22.4 vs $23.4) because its credit is a fixed dollar stream.

Reads the ladder model from revenue_tier_ladder.py.
Writes figures/revenue_tornado.png.
"""
import sys
import types
sys.modules.setdefault("plistlib", types.ModuleType("plistlib"))

import contextlib
import importlib.util
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_spec = importlib.util.spec_from_file_location("rev", "revenue_tier_ladder.py")
R = importlib.util.module_from_spec(_spec)
with contextlib.redirect_stdout(io.StringIO()):
    _spec.loader.exec_module(R)

T = 3                                    # evaluate on the tier-3 plant
TAILS = R.HG_TAILS_RESOLD
SUB2, DOT = "₂", "·"

# anchors: each stream at its TIER-0 co-product settings, tier-3 plant
H0 = R.heat(T, 20.0, h=200.0)
G0 = R.gold(T, R.KG1, 100, 14.0)
S0 = R.synfuel(T, 1.50, R.KWH_LTE, capex=700.0, e_mw=80.0)

PANELS = [
    ("+ heat", "#D55E00", H0, [
        ("heat price  $20 → $80/MWh-th", R.heat(T, 80.0, h=200.0), False),
        ("offtake  200 → 500 MW-th", R.heat(T, 20.0, h=500.0), False),
        ("4 h TES + $140/kW-yr capacity",
         R.heat(T, 20.0, tes=True, cap_kw_yr=140.0, h=200.0), False),
        ("all three together",
         R.heat(T, 80.0, tes=True, cap_kw_yr=140.0, h=500.0), True),
    ]),
    ("+ gold", "#E69F00", G0, [
        ("Hg content  100 → 415 t/GW-th", R.gold(T, R.KG2, 415, 14.0), False),
        ("mercury tails resold",
         R.gold(T, R.KG1, 100, 14.0, feed_usd_per_kg_enr=TAILS), False),
        ("blanket markup  10% → 0",
         R.gold(T, R.KG1, 100, 14.0, blanket=0.0), False),
        ("all ladder levers", R.GOLD[3], True),
    ]),
    (f"+ synfuel", "#009E73", S0, [
        (f"H{SUB2} price  $1.50 → $6.00/kg",
         R.synfuel(T, 6.00, R.KWH_LTE, capex=700.0, e_mw=80.0), False),
        ("stack capex  $700 → $130/kW",
         R.synfuel(T, 1.50, R.KWH_LTE, capex=130.0, e_mw=80.0), False),
        ("electrolyzer  80 → 200 MW",
         R.synfuel(T, 1.50, R.KWH_LTE, capex=700.0, e_mw=200.0), False),
        ("all three together", R.SYN[3], True),
    ]),
]

SURFACE, INK, MUTED, RULE = "#fcfcfb", "#1a1c20", "#6a6f78", "#c9c6bf"
fig, axes = plt.subplots(1, 3, figsize=(15.2, 5.0), facecolor=SURFACE)

lo = min(a - v for _, _, a, rows in PANELS for _, v, _ in rows)
hi = max(a - v for _, _, a, rows in PANELS for _, v, _ in rows)
span = hi - lo

for ax, (title, color, anchor, rows) in zip(axes, PANELS):
    ax.set_facecolor(SURFACE)
    labels = [r[0] for r in rows]
    vals = [anchor - r[1] for r in rows]
    order = sorted(range(len(vals)), key=lambda i: (rows[i][2], vals[i]))
    labels = [labels[i] for i in order]
    vals = [vals[i] for i in order]
    hollow = [rows[i][2] for i in order]

    for y, (v, ho) in enumerate(zip(vals, hollow)):
        ax.barh(y, v, 0.62, zorder=3,
                color="none" if ho else color,
                edgecolor=color, linewidth=1.8 if ho else 0.0,
                hatch="///" if ho else None)
        # negative bars extend LEFT, so their label goes just right of zero --
        # putting it at the bar end would collide with the y tick labels
        ax.text(v + span * 0.02 if v >= 0 else span * 0.02, y,
                f"{v:+.2f}" if abs(v) < 0.1 else f"{v:+.1f}", va="center", ha="left",
                fontsize=9.6, color=INK, fontweight="600", zorder=4)

    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=9.6, color=INK)
    ax.set_xlim(lo - span * 0.10, hi + span * 0.16)
    ax.set_ylim(-0.7, len(labels) - 0.3)
    ax.axvline(0, lw=0.9, color=RULE, zorder=2)
    ax.set_title(title, fontsize=13, color=INK, fontweight="600", loc="left", pad=10)
    ax.grid(axis="x", color=RULE, lw=0.6, alpha=0.45, zorder=0)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(RULE)
    ax.tick_params(axis="x", colors=MUTED, labelsize=9.5, length=0)
    ax.tick_params(axis="y", colors=INK, labelsize=9.6, length=0)

# matplotlib reads a PAIR of "$" as mathtext delimiters; escape every literal one
D_ = "\\$"
fig.text(0.005, 0.972, "What moves each revenue stream",
         fontsize=16, color=INK, fontweight="600", ha="left", va="top")
fig.text(0.005, 0.914,
         f"reduction in LCOE [{D_}/MWh] {DOT} each lever alone, tier-0 setting → its "
         f"deepest ladder value {DOT} on the tier-3 plant ({D_}{R.PLANT[3]:.2f}/MWh)"
         f" {DOT} hatched = all levers at once",
         fontsize=10.6, color=MUTED, ha="left", va="top")
fig.text(0.005, 0.075,
         f"For scale: making the plant itself cheaper is worth {D_}"
         f"{R.PLANT[0]-R.PLANT[3]:.1f} per megawatt-hour across the same four tiers "
         f"— more than any of these co-products buys.",
         fontsize=9.6, color=MUTED, ha="left", va="bottom")
fig.text(0.005, 0.020,
         "The striped bar is not the sum of the solid ones. For heat and synfuel, price and "
         "volume multiply, so raising both together is worth far more than raising either "
         "alone. Gold has no price lever, so its bars very nearly do add up.",
         fontsize=9.6, color=MUTED, ha="left", va="bottom")

fig.subplots_adjust(left=0.165, right=0.995, top=0.800, bottom=0.185, wspace=0.70)
OUT = "figures/revenue_tornado.png"

if __name__ == "__main__":
    fig.savefig(OUT, dpi=160, facecolor=SURFACE)
    plt.close(fig)
    print(f"wrote {OUT}\n")
    for title, _, anchor, rows in PANELS:
        print(f"  {title}   anchor ${anchor:.2f}")
        for lab, v, ho in rows:
            clean = lab.replace(SUB2, "2").replace("→", "->")
            print(f"    {clean:<42}{anchor - v:>+8.2f}{'   (hatched)' if ho else ''}")
