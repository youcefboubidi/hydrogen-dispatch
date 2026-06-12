"""Single-operating-point dispatch evaluation (Phase 4).

Chains the Phase 2/3 building blocks for one operating point — irradiance,
ambient temperature, grid tariff, electrolyzer setpoint — in the order of
PROJECT_PLAN.md section 4:

    PV model -> operating-window check -> pandapower load flow (feasibility)
             -> Faraday H2 rate -> grid cost per hour and per kg

This is the function the Phase 5 optimizer will wrap. It never raises on an
infeasible point: it returns a structured result with ``feasible=False`` and
a human-readable ``reason``. Evaluation stops at the first failed stage;
every field past the stop point stays None.

Run the three demo points with:  python -m src.pipeline   (from the repo root)
"""

from src.network.grid_model import build_network, run_case
from src.physics.electrolyzer_model import P_MIN_MW, P_RATED_MW, mdot_h2_kg_per_h
from src.physics.pv_model import pv_ac_power_mw

# Default grid tariff [DA/kWh] (Algerian dinar). User-configurable default:
# evaluate_dispatch() takes the tariff explicitly, so callers (dashboard
# slider, optimizer, scenario sweeps) pass their own value and this constant
# is only the starting point.
TARIFF_DA_PER_KWH = 4.68

# Network constraint limits — the critical (hard) limits of
# data/etap_parameters.md section 5, the optimizer constraints of Phase 5.
V_MIN_PU = 0.95            # bus undervoltage limit [pu]
V_MAX_PU = 1.05            # bus overvoltage limit [pu]
LOADING_MAX_PERCENT = 100.0  # transformer/branch loading limit [%]


def evaluate_dispatch(g_wm2, t_amb_c, tariff_per_kwh, p_elz_mw):
    """Evaluate one dispatch decision end to end.

    Args:
        g_wm2: plane-of-array irradiance G [W/m²].
        t_amb_c: ambient temperature Ta [°C].
        tariff_per_kwh: grid import tariff [currency/kWh], e.g.
            TARIFF_DA_PER_KWH.
        p_elz_mw: electrolyzer real-power setpoint [MW]; 0 = off, otherwise
            must lie in [P_MIN_MW, P_RATED_MW] = [0.080, 0.800] MW.

    Returns:
        dict with keys
            feasible               point passes window + network checks (bool)
            reason                 None when feasible, else what failed (str)
            pv_mw                  available PV AC power [MW]
            grid_p_mw              dispatch balance p_elz - pv at the LV bus
                                   [MW]; positive = import, negative = export.
                                   Excludes T1 losses (~kW here); the slack
                                   value including losses comes from run_case.
            v_secondary_pu         SecondaryBus voltage [pu]
            trafo_loading_percent  T1 loading [%]
            h2_kg_per_h            hydrogen production [kg/h]
            cost_per_h             grid energy cost [currency/h]; import only,
                                   export is not remunerated
            cost_per_kg            cost_per_h / h2_kg_per_h [currency/kg];
                                   0 when no H2 is produced (then cost_per_h
                                   is 0 too) or when PV covers the whole load
    """
    result = {
        "feasible": False,
        "reason": None,
        "pv_mw": None,
        "grid_p_mw": None,
        "v_secondary_pu": None,
        "trafo_loading_percent": None,
        "h2_kg_per_h": None,
        "cost_per_h": None,
        "cost_per_kg": None,
    }

    # a. Available solar power.
    pv_mw = pv_ac_power_mw(g_wm2, t_amb_c)
    result["pv_mw"] = pv_mw

    # b. Electrolyzer operating window: off (exactly 0) or within turndown.
    if p_elz_mw != 0.0 and not (P_MIN_MW <= p_elz_mw <= P_RATED_MW):
        result["reason"] = (
            f"electrolyzer setpoint {p_elz_mw} MW outside the operating "
            f"window: 0 (off) or [{P_MIN_MW}, {P_RATED_MW}] MW")
        return result

    # c. Network feasibility at this dispatch (fresh net: stateless evaluation).
    ely_on = p_elz_mw > 0.0
    case = run_case(build_network(), pv_mw=pv_mw, ely_in_service=ely_on,
                    ely_p_mw=p_elz_mw if ely_on else None)
    result["v_secondary_pu"] = case["v_secondary_pu"]
    result["trafo_loading_percent"] = case["trafo_loading_percent"]

    if not case["converged"]:  # defensive: runpp raises before this normally
        result["reason"] = "load flow did not converge"
        return result

    violations = []
    for bus, v_pu in (("MainBus", case["v_main_pu"]),
                      ("SecondaryBus", case["v_secondary_pu"])):
        if not V_MIN_PU <= v_pu <= V_MAX_PU:
            violations.append(f"{bus} voltage {v_pu:.5f} pu outside "
                              f"[{V_MIN_PU}, {V_MAX_PU}] pu")
    if case["trafo_loading_percent"] > LOADING_MAX_PERCENT:
        violations.append(f"T1 loading {case['trafo_loading_percent']:.2f} % "
                          f"above {LOADING_MAX_PERCENT} %")
    if violations:
        result["reason"] = "; ".join(violations)
        return result

    # d. Hydrogen production and grid cost. Import is billed at the tariff,
    # export is not remunerated (max(grid_p, 0)).
    h2_kg_per_h = mdot_h2_kg_per_h(p_elz_mw) if ely_on else 0.0
    grid_p_mw = p_elz_mw - pv_mw
    cost_per_h = tariff_per_kwh * max(grid_p_mw, 0.0) * 1000.0
    cost_per_kg = cost_per_h / h2_kg_per_h if h2_kg_per_h > 0.0 else 0.0

    result.update(feasible=True, grid_p_mw=grid_p_mw,
                  h2_kg_per_h=h2_kg_per_h, cost_per_h=cost_per_h,
                  cost_per_kg=cost_per_kg)
    return result


if __name__ == "__main__":
    demo_points = [
        ("SUNNY, electrolyzer at rated", (1000.0, 25.0, TARIFF_DA_PER_KWH, 0.800)),
        ("NIGHT, electrolyzer at rated", (0.0, 25.0, TARIFF_DA_PER_KWH, 0.800)),
        ("SUNNY, part load (PV surplus)", (1000.0, 25.0, TARIFF_DA_PER_KWH, 0.300)),
    ]
    for label, args in demo_points:
        g, ta, tariff, p_elz = args
        print(f"--- {label}: G={g:g} W/m2, Ta={ta:g} C, "
              f"tariff={tariff} DA/kWh, P_elz={p_elz:g} MW")
        for key, value in evaluate_dispatch(*args).items():
            shown = f"{value:.6g}" if isinstance(value, float) else value
            print(f"    {key:>22}: {shown}")
        print()
