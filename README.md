# Alternate Revenue Corridor

Techno-economic analysis of what a D-T fusion plant could sell **other than electrons**.
Three co-products — industrial heat, gold transmutation and synthetic fuel — are each
credited against the same 1 GWe D-T tokamak and graded on one evidence-tier ladder.

Companion to the [1cFE](https://1cf.energy) corridor dispatch of the same name.

## Result

Every co-product is credited against the same plant, and the plant's own cost-down
levers track the mature corridor's ladder at every rung — so a tier here grades the
market evidence for the co-product *and* the plant evidence beneath it together.

| Evidence tier | electricity only | + heat | + gold | + synfuel |
|---|---|---|---|---|
| 0 · design basis | $110.50 | $116.23 | $89.35 | $112.80 |
| 1 · applicable record | $85.33 | $83.94 | $63.07 | $90.08 |
| 2 · extrapolation with a known mechanism | $38.86 | $22.47 | $15.95 | $37.03 |
| 3 · speculation, no mechanism | $23.14 | **−$24.38** | **−$22.84** | **$5.49** |

All figures $/MWh. At the design basis **only gold pays** — heat and synfuel both *raise*
the cost of electricity, because the plant is too expensive for its own heat or hydrogen
to be worth diverting. The plant's own levers carry $87.4/MWh of the descent, more than
any co-product buys.

## Reproducing

The ladder and tornado are self-contained: they need no 1costingFE checkout and no
patch.

```bash
git clone https://github.com/1cFE/Alternate_Revenue_Corridor
cd Alternate_Revenue_Corridor

python revenue_tier_ladder.py      # figures/revenue_tier_ladder.png
python revenue_tornado.py          # figures/revenue_tornado.png
```

`revenue_tier_ladder.py` should print:

```
  rung                      elec only    + heat    + gold  + synfuel
  0: design basis              110.50    116.23     89.35     112.80
  1: applicable record          85.33     83.94     63.07      90.08
  2: extrapolation              38.86     22.47     15.95      37.03
  3: speculation                23.14    -24.38    -22.84       5.49
```

The gold co-product ledger and the three interactive tools were produced against a
1costingFE working tree; see [Why a patch](#why-a-patch) if you want to reproduce those.

### A note on the pin

The commit above is pinned deliberately. `master` has moved on, and re-deriving the cost
points against it shifts the 1 GWe D-T tokamak baseline by a measured **-1.5%**:

| | pinned `6276a84` | `master` at `44434d9` |
|---|---|---|
| LCOE | $110.54/MWh | **$108.87/MWh** |

Almost all of that is one change. ICRF was repriced from $4.38/MW to $1.00/MW and LHCD
from $4.23 to $1.00, both restated as explicit NOAK estimates rather than implied
anchors. The default D-T tokamak heating mix carries 15 MW of ICRF, so the heating
account C220104 falls $99.8M and the installation fraction riding on it another $14.0M. A
smaller change in the other direction re-bases the primary coolant account on thermal
rather than net electric power, worth +$10.1M here. The first-wall and coil accounts are
untouched.

Nothing in this repository depends on which commit you use -- the committed datasets are
the ones the published figures were drawn from. The shift matters only if you re-derive
the cost points yourself, and it moves every rung down by about the same proportion, so
no conclusion changes.

## What each file does

| File | Role |
|---|---|
| `revenue_tier_ladder.py` | The whole model. Plant levers by tier, the gold ledger, the fixed-P_fus cogen calculation, and a port of the H₂ tool validated against it to four decimals. Writes the ladder figure. |
| `revenue_tornado.py` | Single-lever sensitivity per stream, each lever alone from its tier-0 setting to its deepest ladder value. |
| `tools/flexible_cogen_tool.html` | Interactive cogeneration: plant sizing against the heat-to-power price ratio, thermal storage, capacity revenue. |
| `tools/h2_led_plant_tool.html` | Interactive H₂-led plant: busbar split, the H₂ floor price, byproduct-credit LCOE and NPV. |
| `tools/gold_revenue_ledger.html` | The gold co-product ledger as a standalone page. |
| `costingfe-revenue-corridor.patch` | The 1costingFE revenue-offset overlay. Not needed for the figures above. |

Open the tools directly in a browser — each is a single self-contained file.

## Why a patch

The gold ledger and the stream-comparison numbers quoted in the dispatch were produced
against a 1costingFE working tree carrying a revenue-offset overlay that is not on
`master`. It is vendored here so those numbers reproduce exactly:

```bash
git clone https://github.com/1cFE/1costingfe
cd 1costingfe
git checkout 6276a84
git apply ../Alternate_Revenue_Corridor/costingfe-revenue-corridor.patch
```

The patch adds `src/costingfe/revenue_offsets.py` — a non-invasive overlay with
`gold_on` / `heat_on` / `h2_on` toggles, hard-gated to tokamak + D-T and anchored to the
model's own energy denominator so that all-off reproduces `costs.lcoe` exactly — plus
seven driver scripts for the cogen and heat-arbitrage studies. **Nothing in this patch is
required to reproduce the ladder or the tornado**, which carry their own model.

## Scope and limits

- **Effective LCOE is the wrong metric for a diverting co-product past a point.** It
  credits the co-product against a shrinking electricity denominator, so it crosses zero
  at roughly 11% of output diverted and is meaningless beyond that. Heat and synfuel are
  therefore capped at matched diversion — 8% to 20% of output across the ladder — and a
  genuinely heat-led plant has to be judged on margin or NPV instead.
- **Grid volatility cannot reach the LCOE.** There is no price term for the electricity
  sold, so the real benefit of a volatile grid — diverting the cheapest hours, worth about
  $10M/yr at tier 2 — appears in NPV and captured price, not here. It is held fixed.
- **Gold's tier 0 is not a design-basis rung.** The published basis discounts the
  fourteen-year cooldown at 3% rather than the plant's own 7% WACC, and excludes the
  enrichment plant. Heat and synfuel get no equivalent head start. This asymmetry is
  deliberate and documented, not accidental.
- **The enrichment plant is excluded at every rung.** Photon economics put it at
  $40–500M, or $0.25–3.07/MWh — small, but not zero. Priced on a gas-centrifuge basis it
  would have been $2.6B; the difference is that photochemical separation prices on optical
  power, and the photon budget for the whole inventory is about 20 kW of average UV.
- **The heat price row is the least sourced part of the analysis.** The $20, $40 and
  $50/MWh-th values and the $40/kW-yr capacity payment are estimates, not citations.
- **Gold production saturates.** Output is read off Marathon's own neutronics scan rather
  than assumed: doubling the mercury buys about +51%, and their reference blanket costs
  4.15× the mercury for 1.9× the gold.
- The plant ladder is the mature corridor's compact-tokamak result rescaled onto this
  dispatch's 1 GWe D-T baseline, not a direct 1costingFE run of this machine.

## Contact

Questions or challenges to the assumptions and methodology are welcome at
[1cf.energy/contact](https://1cf.energy/contact).
