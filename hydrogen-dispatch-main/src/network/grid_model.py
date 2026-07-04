"""pandapower replica of the ETAP reference network (Phase 2).

Rebuilds, parameter for parameter, the two-bus network of ETAP project
``electrolyzer-demo`` (ETAP 20.6.0, study case ``LF``) recorded in
``data/etap_parameters.md``:

    U1 (utility grid, swing, 1.000 pu / 0 deg)
       |
    MainBus (11 kV)
       |
    T1 (2 MVA, 11/0.415 kV, %Z = 6.25, X/R = 6)
       |
    SecondaryBus (0.415 kV)
       |---- ELY   electrolyzer, 800 kW at 0.95 pf lagging, constant power
       |---- PVA1  PV array + inverter, 534.2 kW AC at full sun, unity pf

Exposes:
    build_network()                       -> net at base-case (SUNNY) values
    run_case(net, pv_mw, ely_in_service)  -> dict of the quantities validated
                                             against ETAP section 4 targets

The ETAP-vs-pandapower comparison lives in notebooks/validation.ipynb and is
the hard gate for every later phase (PROJECT_PLAN.md, Phase 2).
"""

import pandapower as pp

# Element ratings from data/etap_parameters.md section 2.
ELY_P_MW = 0.8           # rated real power; constant-power load draws exactly this
ELY_Q_MVAR = 0.2629      # 800 kW at 0.95 pf lagging -> 262.9 kvar
PV_FULL_SUN_MW = 0.5342  # AC injection after inverter losses (not the 600 kWp DC rating)


def build_network():
    """Build the ETAP reference network (data/etap_parameters.md sections 2 and 6).

    All elements are created at their base-case (SUNNY) values: ELY in service
    drawing 800 kW / 262.9 kvar, PVA1 injecting 534.2 kW at unity power
    factor. Use run_case() to move to another operating point.

    Returns:
        pandapower net with buses MainBus / SecondaryBus and elements
        U1 (ext_grid), T1 (trafo), ELY (load), PVA1 (sgen).
    """
    net = pp.create_empty_network(name="electrolyzer-demo", f_hz=50.0)

    main_bus = pp.create_bus(net, vn_kv=11.0, name="MainBus")
    secondary_bus = pp.create_bus(net, vn_kv=0.415, name="SecondaryBus")

    # U1 — swing source holding MainBus at 1.000 pu / 0 deg. The short-circuit
    # data (500 MVAsc, X/R = 10) is recorded for completeness; it only enters
    # short-circuit studies, not the load flow.
    pp.create_ext_grid(net, bus=main_bus, vm_pu=1.0, va_degree=0.0,
                       s_sc_max_mva=500.0, rx_max=0.1, name="U1")

    # T1 — %Z = 6.25 with X/R = 6 gives %R = 1.027 (%X = 6.165 follows from
    # vk/vkr). ETAP models no excitation branch: pfe_kw = 0, i0_percent = 0.
    pp.create_transformer_from_parameters(
        net, hv_bus=main_bus, lv_bus=secondary_bus,
        sn_mva=2.0, vn_hv_kv=11.0, vn_lv_kv=0.415,
        vk_percent=6.25, vkr_percent=1.027,
        pfe_kw=0.0, i0_percent=0.0, shift_degree=0,
        name="T1",
    )

    # ELY — rectifier-fed electrolyzer: constant power regardless of small AC
    # voltage deviations. pandapower's default load model is constant power,
    # matching ETAP's lumped load with 100 % constant-kVA fraction.
    pp.create_load(net, bus=secondary_bus, p_mw=ELY_P_MW, q_mvar=ELY_Q_MVAR,
                   name="ELY")

    # PVA1 — inverter-coupled PV as a static generator at unity power factor.
    pp.create_sgen(net, bus=secondary_bus, p_mw=PV_FULL_SUN_MW, q_mvar=0.0,
                   name="PVA1")

    return net


def _element_index(table, name):
    """Index of the uniquely named element in a pandapower element table."""
    matches = table.index[table["name"] == name]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one element named {name!r}, "
                         f"found {len(matches)}")
    return matches[0]


def run_case(net, pv_mw, ely_in_service, ely_p_mw=None):
    """Set an operating point, run a Newton-Raphson load flow, return results.

    Mutates ``net`` (PVA1 output, ELY setpoint and service state) and leaves
    the pandapower result tables on it. Every operating-point quantity is set
    on every call (nothing is carried over), so a single net instance can be
    reused across many calls — src.pipeline relies on this. Raises
    pandapower's LoadflowNotConverged if the Newton-Raphson solve fails.

    Args:
        net: network from build_network().
        pv_mw: PVA1 AC injection in MW (0.5342 = full sun, 0.0 = night).
        ely_in_service: True -> ELY draws its setpoint; False -> electrolyzer
            disconnected.
        ely_p_mw: electrolyzer real-power setpoint [MW] (Phase 4 dispatch).
            None (default) resets ELY to its rated 800 kW / 262.9 kvar — the
            validated Phase 2 operating points. When given, Q scales with P to
            hold the rated 0.95 lagging power factor (the rectifier draws the
            commanded power at its rated pf): q = p * ELY_Q_MVAR / ELY_P_MW.

    Returns:
        dict with keys
            converged              Newton-Raphson convergence flag (bool)
            v_main_pu              MainBus voltage [pu] (slack, 1.0 by construction)
            v_secondary_pu         SecondaryBus voltage [pu]
            trafo_loading_percent  T1 loading [%] = input-side MVA / 2 MVA
            trafo_p_loss_mw        T1 real losses [MW]
            trafo_q_loss_mvar      T1 reactive losses [Mvar]
            grid_p_mw              slack P [MW]; positive = grid supplies,
                                   negative = grid absorbs (reverse flow)
            grid_q_mvar            slack Q [Mvar]
            ely_p_mw               electrolyzer drawn P [MW] (0 when out of service)
            ely_q_mvar             electrolyzer drawn Q [Mvar] (0 when out of service)
    """
    ely = _element_index(net.load, "ELY")
    pva1 = _element_index(net.sgen, "PVA1")
    t1 = _element_index(net.trafo, "T1")
    u1 = _element_index(net.ext_grid, "U1")
    main_bus = _element_index(net.bus, "MainBus")
    secondary_bus = _element_index(net.bus, "SecondaryBus")

    if ely_p_mw is None:
        ely_p, ely_q = ELY_P_MW, ELY_Q_MVAR
    else:
        ely_p = float(ely_p_mw)
        ely_q = ely_p * (ELY_Q_MVAR / ELY_P_MW)

    net.sgen.at[pva1, "p_mw"] = float(pv_mw)
    net.load.at[ely, "p_mw"] = ely_p
    net.load.at[ely, "q_mvar"] = ely_q
    net.load.at[ely, "in_service"] = bool(ely_in_service)

    # Newton-Raphson to match ETAP's solver. trafo_loading="power" reproduces
    # ETAP's loading definition (input-side MVA / rated MVA): with no shunt
    # branch the input side always carries the larger apparent power, which is
    # exactly pandapower's max(S_hv, S_lv). numba=False: a JIT brings nothing
    # for a 2-bus network and numba is not part of the Phase 0 environment.
    pp.runpp(net, algorithm="nr", trafo_loading="power", numba=False)

    in_service = bool(ely_in_service)
    return {
        "converged": bool(net.converged),
        "v_main_pu": float(net.res_bus.at[main_bus, "vm_pu"]),
        "v_secondary_pu": float(net.res_bus.at[secondary_bus, "vm_pu"]),
        "trafo_loading_percent": float(net.res_trafo.at[t1, "loading_percent"]),
        "trafo_p_loss_mw": float(net.res_trafo.at[t1, "pl_mw"]),
        "trafo_q_loss_mvar": float(net.res_trafo.at[t1, "ql_mvar"]),
        "grid_p_mw": float(net.res_ext_grid.at[u1, "p_mw"]),
        "grid_q_mvar": float(net.res_ext_grid.at[u1, "q_mvar"]),
        "ely_p_mw": float(net.res_load.at[ely, "p_mw"]) if in_service else 0.0,
        "ely_q_mvar": float(net.res_load.at[ely, "q_mvar"]) if in_service else 0.0,
    }
