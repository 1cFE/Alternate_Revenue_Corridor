"""Evidence-tier ladder for the alternate-revenue corridor.

Four series on one 1 GWe D-T tokamak: electricity only, and that same plant with
each co-product credited against it.  Unlike the earlier two-series version, the
PLANT LEVERS TRACK THE MATURE CORRIDOR at every rung -- so a tier here grades the
market evidence for the co-product *and* the plant evidence underneath it, on the
same footing as the other two dispatches.

Tier vocabulary, cumulative left to right:
  0 design basis / 1 applicable record / 2 extrapolation with a known mechanism /
  3 speculation, no mechanism.

Three modeling choices worth stating, each argued out in the dispatch:

  gold      Production is read off Marathon's own neutronics scan (Alchemy Fig. 5),
            Au(t) = A(1 - exp(-t/lambda)) with lambda = 74.2 mm, A = 3.13 t/yr at
            1500 MWth -- a SATURATING curve, not a power law.  Tiers 0-1 hold the
            published 1 t/GWth basis (100 t/GWth loading, the bottom of the paper's
            stated 100-450 t/GWth range); tiers 2-3 adopt their 415 t/GWth
            reference blanket, which buys 1.9x the gold for 4.15x the mercury.

  heat      The firm offtake is held at 200 MWth on EVERY rung and only the market
            evidence ladders (price, storage, capacity).  Tier 3 adopts the more
            realistic of the dispatch's two 1 c/kWh corridors -- $80/MWh-th with a
            $140/kW-yr capacity payment.  That pair needs 1,255 MWth of offtake on
            the DESIGN-BASIS plant, but only 162 MWth on the tier-3 plant, so the
            fixed 200 MWth already clears 1 c/kWh without any heat-led config.  Effective LCOE credits a
            diverting co-product against a shrinking electricity denominator, so it
            crosses zero at ~278 MWth diverted (11% of output) and is meaningless
            past that; a heat-led plant has to be judged on margin, not LCOE.

  synfuel   The electrolyzer is fixed at 80 MW, the MWe heat gives up, so both
            diverting streams carry the same physical kit; diversion then falls
            out as a result (1.0 -> 7.4%) instead of being imposed.  An unmatched
            pair would compare a bar at 8% against one at 56%, which mostly
            measures the denominator.  Grid volatility is held fixed -- see the
            note on the synfuel model below.

            Matching does NOT equalize heat and hydrogen, and the residual is the
            real result:
            at tier 3 heat is worth $200/MWh_e (80/MWh_th over eta_gen) against
            H2's $71.15 (4.50 - 0.80 /kg over 52 kWh/kg), so heat throws off ~2.7x
            the surplus per diverted electron.  The ratio runs 3.71x, 2.36x, 2.95x,
            2.74x across the rungs -- widest at tier 0, where hydrogen is priced at
            grey parity and is worth almost nothing per electron diverted.

Palette is Okabe-Ito, validated for the light surface (all checks pass; the gold
hue's sub-3:1 contrast is relieved by the direct value label on every bar).

Writes figures/revenue_tier_ladder.png.

matplotlib's font_manager imports plistlib -> pyexpat, blocked by policy here;
plistlib is macOS-only, so a stub lets the rest of matplotlib load.
"""
import sys
import types
sys.modules.setdefault("plistlib", types.ModuleType("plistlib"))

import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------- plant levers
# Cumulative, lifted from corridor_tiers.py's T1_REC / T2_EXT / T3_SPEC.  Tier 1
# carries no cost-of-capital record, so the 7% design basis is held there.
WACC = [0.07, 0.07, 0.05, 0.03]
LIFE = [30.0, 60.0, 80.0, 80.0]
AV = [0.85, 0.92, 0.95, 0.98]
ETA = 0.40


def crf(w, n):
    return w / (1 - (1 + w) ** -n)


CRF = [crf(w, n) for w, n in zip(WACC, LIFE)]

# Mature corridor, compact tokamak at 1 GWe, rescaled onto this dispatch's own
# published 1 GWe D-T baseline.  PROVISIONAL: wants a direct 1costingFE run with
# the lever stack applied to this machine rather than the CT ratios.
# CT is the mature corridor's compact-tokamak ladder at 1 GWe (Magnetic_DT_Corridor,
# corridor_tiers.json "tok_1g"): design basis, records, extrapolations, speculation,
# the last with lights-out O&M (fixed O&M x 0.0855) as every tier-3 in the set now carries.
CT = [114.5790, 90.3763, 41.4942, 20.8100]
PLANT = [110.5 * c / CT[0] for c in CT]


def annual(t):
    """All-in cost of the electricity-only plant at tier t, M$/yr."""
    return PLANT[t] * 1000 * 8760 * AV[t] / 1e6


# ------------------------------------------------------------------------ gold
P_GWTH, PRICE, ABUND = 3.18, 100e3, 0.0997
LAM, A_T, T_PER_MM = 74.2, 3.130, 415 / 210     # Alchemy Fig. 5 fit
HG_USD, SEP_USD = 30.0, 2.4
EXTRACT, EXTRACT_OM, REG_OM, BLANKET = 50.0, 0.05, 3.0, 49.46


def gold_kg(inv_t_per_gwth):
    """kg 197Au per GWth per year at a given 198Hg loading, from Fig. 5."""
    mm = inv_t_per_gwth / T_PER_MM
    return A_T * (1 - math.exp(-mm / LAM)) / 1.5 * 1000


# With no credit for the 198Hg-depleted tails the model charges natural Hg at
# $30/kg across the whole natural mass, an implied $301 per kg of 90%-enriched
# product.  Reselling the tails into the existing mercury market is ordinary
# commercial practice and puts it at $61/kg-enriched (1cFE slide deck, from the
# UN/USGS price series); disposing of them instead would be $775.
HG_TAILS_RESOLD = 61.0                             # $/kg of 90%-enriched product


def gold(t, kg_per_gwth, inv_t_per_gwth, cooldown_yr, rate=0.03,
         feed_usd_per_kg_enr=None, blanket=BLANKET):
    au = kg_per_gwth * P_GWTH * AV[t]
    rev = au * PRICE / 1e6 / (1 + rate) ** cooldown_yr
    inv = inv_t_per_gwth * P_GWTH
    if feed_usd_per_kg_enr is None:
        feed = inv / ABUND * 1e3 * HG_USD / 1e6        # natural Hg, no tails credit
    else:
        feed = inv * 1e3 * feed_usd_per_kg_enr / 1e6
    burn = kg_per_gwth / (inv_t_per_gwth * 1e3)
    om = EXTRACT * EXTRACT_OM + inv * 1e3 * burn * SEP_USD / 1e6 + REG_OM
    cost = (EXTRACT + feed + blanket) * CRF[t] + om
    return PLANT[t] - (rev - cost) * 1e6 / (1000 * 8760 * AV[t])


# ------------------------------------------------------------------------ heat
BOP_K, TES_K, TES_H = 200.0, 30.0, 4               # $/kW_th, $/kWh, hours
HFIRM = 200.0                                      # held on every rung


def heat(t, price_th, tes=False, cap_kw_yr=0.0, h=HFIRM):
    """P_fus fixed: diverting h MWth costs ETA*h MWe of saleable power."""
    add = BOP_K * h * 1e3 / 1e6 + (TES_K * h * TES_H * 1e3 / 1e6 if tes else 0.0)
    hrev = h * price_th * 8760 * AV[t] / 1e6
    crev = (ETA * h) * 1e3 * cap_kw_yr / 1e6       # incremental firm MW only
    pnet = 1000 - ETA * h
    return (annual(t) + CRF[t] * add - hrev - crev) * 1e6 / (pnet * 8760 * AV[t])


# --------------------------------------------------------------------- synfuel
# Electrolyzer capacity is MATCHED to the MWe heat gives up (eta x 200 MWth =
# 80 MWe) rather than to its energy share, so both diverting streams carry the
# same physical kit and the same capex, and the diversion falls out as a result
# instead of being imposed.  It peaks at 7.4%, just under heat's 8%, so the cap
# keeps the metric inside its valid range on its own.
#
# Grid volatility is HELD FIXED rather than laddered.  Effective LCOE has no
# price term for the electricity sold, so volatility's real benefit -- that you
# divert the cheapest hours, worth ~$10M/yr at tier 2 -- cannot reach the number;
# it lives in NPV and captured price, which is how h2_led_plant_tool.html reports
# it.  Laddering volatility here would pick up only its small adverse effect on
# electrolyzer utilization and miss the large favorable one.
ELY_CAPEX, ELY_OM, LOG = 700.0, 0.03, 0.80
ELY_MW = ETA * HFIRM                               # 80 MW, matched to heat
GRID_MEAN, GRID_VOL = 40.0, 1.0
KWH_LTE, KWH_SOEC = 52.0, 40.0                     # low-temp vs solid-oxide


def _duration(mean, vol, n=200):
    out = []
    for i in range(n):
        x = i / (n - 1)
        base = (1 if x > 0.5 else -1) * abs(2 * (x - 0.5)) ** 1.5
        spike = ((x - 0.9) / 0.1) ** 2 * 3 if x > 0.9 else 0.0
        out.append(mean + vol * (base * 40 + spike * 40))
    return out


def synfuel(t, h2_price, kwh_per_kg, capex=ELY_CAPEX, e_mw=ELY_MW,
            mean=GRID_MEAN, vol=GRID_VOL, detail=False):
    """Port of h2_led_plant_tool.html's evaluate(), electrolyzer given in MW.

    The stack runs whenever the grid price sits below the H2 floor -- the $/MWh
    at which a kg of hydrogen is worth more than the power it takes -- and excess
    power is curtailed rather than sold at a negative price, both per the tool.
    """
    kg_per_mwh = 1000 / kwh_per_kg
    floor = kg_per_mwh * (h2_price - LOG)
    pr = _duration(mean, vol)
    grid_mwh = h2_mwh = 0.0
    for p in pr:
        hrs = 8760 * AV[t] / len(pr)
        if p > floor:
            grid_mwh += 1000 * hrs
        else:
            h2_mwh += e_mw * hrs
            grid_mwh += (1000 - e_mw) * hrs if p > 0 else 0.0
    mass = h2_mwh * kg_per_mwh
    ely = e_mw * 1e3 * capex * (CRF[t] + ELY_OM) / 1e6
    lcoe = (annual(t) + ely + mass * LOG / 1e6
            - mass * h2_price / 1e6) * 1e6 / grid_mwh
    if detail:
        return lcoe, h2_mwh / (grid_mwh + h2_mwh), mass / 1e6, floor
    return lcoe


# ------------------------------------------------------------------ the ladder
KG1 = 1000.0                       # published 1 t/GWth basis, tiers 0-1
KG2 = gold_kg(415)                 # Marathon reference blanket, tiers 2-3

ELEC = PLANT
# The firm offtake grows with the rung -- 200/300/400/500 MWth -- alongside the
# price.  Diversion tops out at 20% of output (800 MWe still sold) and the price
# sensitivity at 0.6 $/MWh per $1/MWh-th, so the metric stays well inside its
# valid range; a steeper schedule compounds with the plant's own descent and runs
# away (200/300/500/800 reaches -$66 at tier 3, 200/400/800/1255 reaches -$168).
HEAT_MWTH = [200.0, 300.0, 400.0, 500.0]
HEAT = [heat(0, 20.0, h=HEAT_MWTH[0]),
        heat(1, 40.0, h=HEAT_MWTH[1]),
        heat(2, 50.0, tes=True, cap_kw_yr=40.0, h=HEAT_MWTH[2]),
        heat(3, 80.0, tes=True, cap_kw_yr=140.0, h=HEAT_MWTH[3])]
# The cooldown is set by a regulatory threshold, not by taste.  Marathon give
# three: 6.8 yr to reach NRC Class-A low-level waste, 13.7 yr to need no
# radioactive labeling at all (Class 7, 2700 pCi/g for 197Au), and 17.7 yr to
# fall below banana-equivalent activity.  The dispatch's non-fungibility argument
# rests on the PLACARD, which clears at 13.7 yr, so the published 14 yr IS that
# threshold and it is held at every rung.
#
# The rungs are therefore: tails resale (an existing Hg market) at tier 1; the
# blanket complexity markup retired at tier 2 -- the Hg (n,2n) layer replaces a
# Be/Pb multiplier the blanket needs anyway, and Hg is cheap; and Marathon's own
# 415 t/GWth reference blanket at tier 3, which doubles production but needs
# 4.15x the mercury -- 4.7 years of the world's Minamata-compliant supply for one
# plant, which is what makes it speculation rather than extrapolation.
#
# Gold has no price lever ($100k/kg is spot), so its only escalating input is
# volume, and that escalation lands entirely at tier 3.  Heat and synfuel ramp
# both price and volume every rung.  The shapes do not match; the total tier-3
# ask does (gold 4.15x on one input, the others 2.5x volume AND 4x price).
GOLD = [gold(0, KG1, 100, 14.0),
        gold(1, KG1, 100, 14.0, feed_usd_per_kg_enr=HG_TAILS_RESOLD),
        gold(2, KG1, 100, 14.0, feed_usd_per_kg_enr=HG_TAILS_RESOLD, blanket=0.0),
        gold(3, KG2, 415, 14.0, feed_usd_per_kg_enr=HG_TAILS_RESOLD, blanket=0.0)]

# Synfuel: the sale price carries tiers 0-1 and the technology carries 2-3.
#   price   grey $1.50 -> $3.00, a scenario price pegged to the maximum statutory
#           rate of the US 45V clean-hydrogen production credit (a subsidy, not a
#           selling-price record) -> $3.75 -> $6.00, the mid-range of today's
#           UNSUBSIDISED green H2 production cost ($4.50-7.00).
#   capex   IRENA, "Green Hydrogen Cost Reduction" (2020) puts installed cost at
#           $650-1,000/kW in 2020 (avg ~$770; the tool's $700 sits inside it) and
#           at $130-307/kW by 2050, the range spanning 1-5 TW of deployment.
#           Tier 2 takes $307/kW, the 1 TW end; tier 3 takes $130/kW, the end
#           that needs 5 TW on the ground.
#
# Solid-oxide electrolysis on the reactor's own heat was tested as a tier-2
# mechanism and dropped: worth only $0.88/MWh at tier 2 and $1.88 at tier 3, and
# the model gave it its heat free (charging the forgone turbine output moved the
# result $0.07).  Low-temperature electrolysis at 52 kWh/kg holds at every rung.
# The electrolyzer is sized to the MWe heat gives up at the SAME rung, so the two
# diverting streams stay matched as heat's offtake grows -- 80/120/160/200 MWe
# against heat's 80/120/160/200.  And the H2 price takes heat's own optimism
# profile: heat runs $20 -> $40 -> $50 -> $80, i.e. x2.00, x1.25, x1.60, and the
# same steps on grey H2 give $1.50 -> $3.00 -> $3.75 -> $6.00 (both x4.0 overall).
ELY_MW_TIER = [ETA * h for h in HEAT_MWTH]
H2_PRICE = [1.50, 3.00, 3.75, 6.00]
KWH_PER_KG = [KWH_LTE, KWH_LTE, KWH_LTE, KWH_LTE]
ELY_CAPEX_TIER = [700.0, 700.0, 307.0, 130.0]
SYN = [synfuel(t, H2_PRICE[t], KWH_PER_KG[t], capex=ELY_CAPEX_TIER[t],
               e_mw=ELY_MW_TIER[t]) for t in range(4)]

# ----------------------------------------------------------------------- plot
SURFACE, INK, MUTED, RULE = "#fcfcfb", "#1a1c20", "#6a6f78", "#c9c6bf"
TARGET = 10.0
DOT, SUB2, TIMES = "·", "₂", "×"

SERIES = [("electricity only", ELEC, "#0072B2"),
          ("+ heat", HEAT, "#D55E00"),
          ("+ gold", GOLD, "#E69F00"),
          ("+ synfuel", SYN, "#009E73")]

TIERS = ["0: design basis", "1: applicable record",
         "2: extrapolation", "3: speculation"]

# NB: matplotlib reads a PAIR of "$" in a string as mathtext delimiters, which
# silently italicises everything between them.  Every literal dollar sign in
# these notes is escaped.
D_ = "\\$"
NOTES = [
    f"plant {DOT} as designed, 7% WACC\n"
    f"heat {DOT} 200 MW-th @ {D_}20/MWh-th\n"
    f"gold {DOT} 100 t/GW-th Hg, 14-yr cooldown\n"
    f"H{SUB2} {DOT} grey {D_}1.50/kg {DOT} 80 MW @ {D_}700/kW",

    f"plant {DOT} 7% held {DOT} 0.92 av {DOT} 60 yr\n"
    f"heat {DOT} 300 MW-th @ {D_}40/MWh-th\n"
    f"gold {DOT} enriched Hg at {D_}61/kg, tails resold\n"
    f"H{SUB2} {DOT} {D_}3.00/kg (45V rate) {DOT} 120 MW",

    f"plant {DOT} 5% WACC {DOT} 0.95 av {DOT} 80 yr\n"
    f"heat {DOT} 400 MW-th @ {D_}50 + TES + {D_}40/kW-yr\n"
    f"gold {DOT} no blanket complexity markup\n"
    f"H{SUB2} {DOT} {D_}3.75/kg {DOT} 160 MW @ {D_}307/kW",

    f"plant {DOT} 3% WACC {DOT} 0.98 av {DOT} 2.5 yr build\n"
    f"heat {DOT} 500 MW-th @ {D_}80 + {D_}140/kW-yr\n"
    f"gold {DOT} 415 t/GW-th Hg content\n"
    f"H{SUB2} {DOT} {D_}6.00/kg {DOT} 200 MW @ {D_}130/kW",
]

fig, ax = plt.subplots(figsize=(14.6, 6.9))
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)

x = range(len(TIERS))
w = 0.20
lo = min(min(s) for _, s, _ in SERIES)
hi = max(max(s) for _, s, _ in SERIES)
ylo, yhi = lo - 20.0, hi * 1.13

for k, (label, vals, color) in enumerate(SERIES):
    off = (k - 1.5) * w
    bars = ax.bar([i + off for i in x], vals, w, label=label, color=color,
                  edgecolor=SURFACE, linewidth=1.2, zorder=3)
    for bar, v in zip(bars, vals):
        pad = (yhi - ylo) * 0.011
        ax.text(bar.get_x() + bar.get_width() / 2,
                v + pad if v >= 0 else v - pad,
                f"{v:,.1f}", ha="center",
                va="bottom" if v >= 0 else "top",
                fontsize=9.4, color=INK, fontweight="600", zorder=4)

ax.set_xlim(-0.98, len(TIERS) - 0.42)
ax.set_ylim(ylo, yhi)
ax.axhline(TARGET, ls="--", lw=1.1, color="#b8891f", zorder=2)
ax.text(-0.94, TARGET + (yhi - ylo) * 0.012, "1 ¢/kWh\n($10/MWh)", fontsize=10,
        color="#b8891f", ha="left", va="bottom", zorder=5, linespacing=1.35)
ax.axhline(0, lw=0.9, color=RULE, zorder=2)

ax.set_xticks(list(x))
ax.set_xticklabels(TIERS, fontsize=12.5, color=INK, fontweight="600")
tr = ax.get_xaxis_transform()
for i, n in enumerate(NOTES):
    ax.text(i, -0.105, n, transform=tr, ha="center", va="top",
            fontsize=9.3, color=MUTED, linespacing=1.6)

ax.set_ylabel("LCOE  [$/MWh]", fontsize=12.5, color=INK, fontweight="600")
ax.set_title("Alternate revenue: evidence-tier ladder, cumulative by tier",
             fontsize=16, color=INK, fontweight="600", loc="left", pad=20)
ax.text(0, 1.018,
        f"1 GWe D-T tokamak {DOT} plant levers track the mature corridor {DOT} "
        f"heat and synfuel diverted in step, 8% to 20% of output {DOT} indirects held at 20% nominal",
        transform=ax.transAxes, fontsize=11.5, color=MUTED, va="bottom")

ax.grid(axis="y", color=RULE, lw=0.6, alpha=0.5, zorder=0)
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(RULE)
ax.tick_params(axis="y", colors=MUTED, labelsize=11.5, length=0)
ax.tick_params(axis="x", colors=INK, labelsize=12.5, length=0, pad=8)
leg = ax.legend(frameon=False, fontsize=11.5, loc="upper right", ncol=4,
                labelcolor=INK, columnspacing=1.6, handlelength=1.5)
for txt in leg.get_texts():
    txt.set_fontweight("600")

fig.subplots_adjust(left=0.065, right=0.987, top=0.855, bottom=0.262)
OUT = "figures/revenue_tier_ladder.png"

# Guarded so the model above can be imported for sensitivity work without
# rewriting the figure.
if __name__ == "__main__":
    fig.savefig(OUT, dpi=160, facecolor=SURFACE)
    plt.close(fig)

    print(f"wrote {OUT}\n")
    print(f"  gold production: tiers 0-1 {KG1:,.0f} kg/GWth/yr @ 100 t/GWth"
          f"  ({gold_kg(100):,.0f} on Fig. 5's curve)")
    print(f"                   tiers 2-3 {KG2:,.0f} kg/GWth/yr @ 415 t/GWth\n")
    print(f"  {'rung':<24}{'elec only':>11}{'+ heat':>10}{'+ gold':>10}{'+ synfuel':>11}")
    for i, t in enumerate(TIERS):
        print(f"  {t:<24}{ELEC[i]:>11.2f}{HEAT[i]:>10.2f}{GOLD[i]:>10.2f}{SYN[i]:>11.2f}")
    print(f"\n  heat threshold (LCOE_e x eta_gen), by tier:  "
          + "  ".join(f"${PLANT[t] * ETA:.2f}" for t in range(4)))
    print(f"\n  synfuel: electrolyzer matched to heat's forgone MWe, grid mean "
          f"${GRID_MEAN:.0f} at volatility {GRID_VOL:.1f}")
    print(f"  {'tier':<6}{'H2 $/kg':>9}{'ely MW':>8}{'$/kW':>7}{'floor':>8}"
          f"{'diverted':>10}{'heat div':>10}{'kt/yr':>8}")
    for i in range(4):
        _, dv, kt, fl = synfuel(i, H2_PRICE[i], KWH_PER_KG[i],
                                capex=ELY_CAPEX_TIER[i],
                                e_mw=ELY_MW_TIER[i], detail=True)
        print(f"  {i:<6}{H2_PRICE[i]:>9.2f}{ELY_MW_TIER[i]:>8.0f}"
              f"{ELY_CAPEX_TIER[i]:>7.0f}{fl:>8.1f}{dv:>9.1%}"
              f"{ETA * HEAT_MWTH[i] / 10:>9.0f}%{kt:>8.1f}")
