# ETAP Model Parameters & Validation Targets

**Purpose:** Complete handoff from Phase 1 (ETAP reference model) to Phase 2 (pandapower replica). Records every network parameter exactly as entered in ETAP, the operating-point definitions, and the load-flow results that the pandapower model **must reproduce within tolerance** before any later work is trusted.

**Source:** ETAP 20.6.0, project `electrolyzer-demo`, study case `LF`, Newton-Raphson solver. All three cases converged in 2 iterations with zero system mismatch.

---

## 1. Network topology

```
U1 (utility grid, swing)
   |
MainBus  (11 kV)
   |
T1  (2 MVA, 11/0.415 kV transformer)
   |
SecondaryBus  (0.415 kV)
   |---- ELY    (electrolyzer, constant-kVA controllable load)
   |---- PVA1   (PV array + inverter, generation)
```

---

## 2. Element parameters (as entered in ETAP)

### U1 — Power Grid (utility source)
| Parameter | Value |
|---|---|
| Connected bus | MainBus |
| Nominal voltage | 11 kV |
| Operating mode | **Swing / slack** |
| Short-circuit rating | 500 MVAsc (3-phase) |
| X/R | 10 |

For load flow this acts as the slack bus at **Vm = 1.000 pu, angle = 0°**.

### MainBus
| Parameter | Value |
|---|---|
| Nominal voltage | 11 kV |

### T1 — Two-Winding Transformer
| Parameter | Value |
|---|---|
| Rated power | 2 MVA |
| HV / LV voltage | 11 kV / 0.415 kV |
| Impedance %Z (positive) | 6.25 % |
| X/R | 6 |
| Derived %X | 6.165 % |
| Derived %R | 1.027 % |
| Standard / type | IEC, Liquid-Fill, 65 °C |
| No-load loss / exciting current | 0 (not modeled) |
| Tap | nominal (0 %) |

### SecondaryBus
| Parameter | Value |
|---|---|
| Nominal voltage | 0.415 kV |

### ELY — Electrolyzer (constant-kVA load)
| Parameter | Value |
|---|---|
| Element ID | ELY |
| ETAP element type | **Lumped Load, 100 % constant-kVA fraction** |
| Connected bus | SecondaryBus |
| Rated real power | 800 kW |
| Power factor | 0.95 lagging |
| Rated apparent power | 842.1 kVA |
| Rated reactive power | 262.9 kvar |
| Connection | 3-phase |

> **Load-model decision (resolved).** A regulated rectifier-fed electrolyzer holds the commanded power regardless of small AC-voltage variations, so the correct steady-state representation is **constant power (constant kVA)**. Note that ETAP's *Static Load* element is modeled as **constant impedance** in load flow (per ETAP's own Load Flow workshop documentation), which is why the lumped-load element with a 100 % constant-kVA fraction is used instead. With this model the electrolyzer draws **exactly 800 kW** at every studied operating point — commanded = drawn — which matches the dispatch semantics of the optimization framework.

### PVA1 — PV Array + Inverter (generation)
| Parameter | Value |
|---|---|
| Connected bus | SecondaryBus |
| Panel model | JA Solar JAM72S09-395 (~395 W, monocrystalline, 72-cell) |
| Array layout | 20 in series × 76 parallel ≈ 1520 panels |
| Array rating (DC) | ≈ 600 kWp |
| Inverter rating (AC) | 630 kVA |
| Inverter efficiency | 90 % |
| Inverter power factor | unity (1.0) |
| **AC output at full sun** | **534.2 kW** |

> Use 534.2 kW (the AC injection after inverter losses), not 600, as the PV input for the full-sun case.

---

## 3. Operating-point definitions

| Case | PVA1 | ELY | Meaning |
|---|---|---|---|
| **SUNNY** (base) | full output (534.2 kW AC) | in service (800 kW) | Daytime, full sun, electrolyzer at full load |
| **NIGHT** | out of service (0) | in service (800 kW) | No sun; grid supplies the whole load |
| **PV_EXPORT** | full output (534.2 kW AC) | out of service (0) | Surplus PV; power flows back to the grid |

---

## 4. Validation targets — pandapower MUST reproduce these

Tolerance: bus voltage within **±1 %** (±0.01 pu); transformer loading within **a few %**; power flows within **~2 %**. With matched models, near-exact agreement is expected.

### Bus voltages (per unit)
| Bus | SUNNY | NIGHT | PV_EXPORT |
|---|---|---|---|
| MainBus (slack) | 1.00000 | 1.00000 | 1.00000 |
| SecondaryBus | 0.99042 | 0.98735 | 1.00260 |

### Transformer T1
| Quantity | SUNNY | NIGHT | PV_EXPORT |
|---|---|---|---|
| Loading % (input side) | 18.87 % | 42.64 % | 26.71 % |
| Power through T1 (MVA, input) | 0.3774 | 0.8529 | 0.5342 |
| Real losses (kW) | 0.732 | 3.737 | 1.459 |
| Reactive losses (kvar) | 4.390 | 22.421 | 8.752 |
| Voltage drop across T1 | 0.958 % | 1.265 % | 0.260 % |

### Power flows (MW / Mvar)
| Quantity | SUNNY | NIGHT | PV_EXPORT |
|---|---|---|---|
| Grid (slack) P | +0.2665 (supply) | +0.8037 (supply) | **−0.5328 (absorb)** |
| Grid (slack) Q | +0.2672 | +0.2852 | +0.0088 |
| PV output P | 0.5342 | 0 | 0.5342 |
| Electrolyzer load P | **0.8000** | **0.8000** | 0 |
| Electrolyzer load Q | 0.2628 | 0.2628 | 0 |

> The electrolyzer draws exactly its 800 kW rating in both in-service cases (constant-kVA model). The negative grid P in PV_EXPORT confirms **reverse power flow**; the pandapower model must reproduce this sign change.

---

## 5. Constraint limits (from ETAP alert settings — use as optimizer constraints)

| Quantity | Marginal | Critical (hard limit) |
|---|---|---|
| Bus voltage (under) | 0.98 pu | **0.95 pu** |
| Bus voltage (over) | 1.02 pu | **1.05 pu** |
| Transformer / branch loading | 95 % | **100 %** |

All three validated operating points sit comfortably inside these limits (no alarms in any case).

---

## 6. pandapower mapping (build hints for Phase 2)

| ETAP element | pandapower object | Key arguments |
|---|---|---|
| MainBus | `create_bus` | `vn_kv = 11.0` |
| SecondaryBus | `create_bus` | `vn_kv = 0.415` |
| U1 | `create_ext_grid` | `vm_pu = 1.0`, `va_degree = 0` |
| T1 | `create_transformer_from_parameters` | `sn_mva = 2.0`, `vn_hv_kv = 11`, `vn_lv_kv = 0.415`, `vk_percent = 6.25`, `vkr_percent = 1.027`, `pfe_kw = 0`, `i0_percent = 0`, `shift_degree = 0` |
| ELY | `create_load` | `p_mw = 0.8`, `q_mvar = 0.2629` (plain constant-power load — pandapower's default; no `const_z_percent` needed) |
| PVA1 | `create_sgen` | `p_mw = 0.5342`, `q_mvar = 0.0` (full sun); `p_mw = 0` or `in_service = False` for night |

Notes:
- Run with `pp.runpp(net, algorithm='nr')` (Newton-Raphson) to match ETAP's solver.
- `shift_degree = 0` is fine for voltage-magnitude validation in this radial network.
- To reproduce each case, toggle ELY / PVA1 `in_service` (or set power to 0).

---

## 7. Phase 2 checklist

1. Build the network in `src/network/grid_model.py` from the parameters above.
2. Run all three cases and compare against section 4 in `notebooks/validation.ipynb`.
3. **Hard gate:** all three SecondaryBus voltages within ±1 %, T1 loading within a few %, electrolyzer drawing exactly 0.8 MW when in service, and the PV_EXPORT grid flow correctly negative. Do not proceed past Phase 2 until this passes.
4. Record the ETAP-vs-pandapower comparison table — it becomes a validation figure in Chapter 4.
