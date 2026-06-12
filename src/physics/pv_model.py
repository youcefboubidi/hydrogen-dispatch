"""PV array power model — Phase 3 stub, not yet implemented.

Will compute the available AC-side solar power from irradiance G and ambient
temperature T:

    P_pv = P_stc * (G / G_stc) * (1 + gamma * (T_cell - T_stc))

followed by the inverter efficiency and its rating clip. Reference array is
PVA1 from data/etap_parameters.md section 2: ~600 kWp DC (20s x 76p JA Solar
JAM72S09-395), 630 kVA inverter at 90 % efficiency, unity power factor,
534.2 kW AC at full sun. Implemented in Phase 3 of PROJECT_PLAN.md.
"""
