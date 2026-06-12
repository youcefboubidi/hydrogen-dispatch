"""Engineering PV array model (Phase 3) — AC power from irradiance and ambient temperature.

Implements the linear engineering model of Chapter 2, eq. 2.8,

    P = P_ref * (G / G_ref) * [1 + gamma * (Tc - Tc_ref)]

with the standard NOCT cell-temperature model

    Tc = Ta + (NOCT - 20) / 800 * G        [°C, with G in W/m²]

for the array PVA1 of ``data/etap_parameters.md`` section 2 (20s x 76p JA Solar
JAM72S09-395, ~600 kWp DC, 630 kVA inverter at unity power factor).

Anchoring: the reference pair (P_ref, Tc_ref) is taken at the Phase-2 validated
full-sun operating point — G = 1000 W/m², Ta = 25 °C, at which ETAP/pandapower
inject exactly 534.2 kW AC — rather than at STC. The model therefore passes
through the validated point bit-exactly (eq. 2.8 is unchanged; only the
reference point of the linearization is moved). The equivalent STC-referenced
rating implied by this anchoring is P_ref / [1 + gamma*(25 - 56.25)] ≈ 0.5998 MW
at 25 °C cell temperature.

Pure module: no I/O, no pandapower. All functions take and return floats.
Run the hand checks with:  python src/physics/pv_model.py
"""

# Panel coefficients (JA Solar JAM72S09 datasheet values).
GAMMA_PER_C = -0.0035   # power temperature coefficient gamma_Pmax = -0.35 %/°C [1/°C]
NOCT_C = 45.0           # nominal operating cell temperature (datasheet 45 ± 2 °C) [°C]

# Reference (anchor) condition = the Phase-2 validated full-sun operating point.
G_REF_WM2 = 1000.0      # reference irradiance [W/m²]
T_AMB_REF_C = 25.0      # ambient temperature at the anchor point [°C]
P_REF_MW = 0.5342       # validated AC injection at the anchor point (ETAP/pandapower,
                        # data/etap_parameters.md section 2) [MW]

# Inverter limit: 630 kVA at unity power factor -> 0.630 MW AC cap.
P_MAX_AC_MW = 0.630     # inverter apparent-power rating [MVA] = MW at unity pf


def cell_temperature_c(g_wm2, t_amb_c):
    """NOCT cell-temperature model: Tc = Ta + (NOCT - 20)/800 * G.

    The NOCT condition (800 W/m², 20 °C ambient) defines the linear
    irradiance-to-heating coefficient (NOCT - 20)/800 [°C per W/m²].

    Args:
        g_wm2: plane-of-array irradiance G [W/m²].
        t_amb_c: ambient temperature Ta [°C].

    Returns:
        Cell temperature Tc [°C].
    """
    return t_amb_c + (NOCT_C - 20.0) / 800.0 * g_wm2


# Reference cell temperature: NOCT model evaluated at the anchor condition
# (G = 1000 W/m², Ta = 25 °C) -> 25 + 25/800 * 1000 = 56.25 °C. Computed through
# cell_temperature_c() so the anchor reproduces P_REF_MW bit-exactly.
TC_REF_C = cell_temperature_c(G_REF_WM2, T_AMB_REF_C)


def pv_ac_power_mw(g_wm2, t_amb_c):
    """AC-side PV power from irradiance and ambient temperature (eq. 2.8).

    P = P_ref * (G/G_ref) * [1 + gamma * (Tc - Tc_ref)], Tc from the NOCT
    model, clamped to [0, P_MAX_AC_MW] (inverter rating, unity power factor).
    At the anchor point (G = 1000 W/m², Ta = 25 °C) returns exactly 0.5342 MW,
    the Phase-2 validated full-sun injection.

    Args:
        g_wm2: plane-of-array irradiance G [W/m²]; G <= 0 returns 0.
        t_amb_c: ambient temperature Ta [°C].

    Returns:
        AC power at the inverter terminals [MW], in [0, 0.630].
    """
    if g_wm2 <= 0.0:
        return 0.0
    tc_c = cell_temperature_c(g_wm2, t_amb_c)
    p_mw = P_REF_MW * (g_wm2 / G_REF_WM2) * (1.0 + GAMMA_PER_C * (tc_c - TC_REF_C))
    return max(0.0, min(p_mw, P_MAX_AC_MW))


if __name__ == "__main__":
    failures = []

    # (a) Anchor point must reproduce the validated full-sun injection exactly.
    p_a = pv_ac_power_mw(1000.0, 25.0)
    ok_a = p_a == 0.5342
    print(f"(a) G=1000 W/m2, Ta=25 C -> {p_a:.10f} MW "
          f"(expected exactly 0.5342) {'OK' if ok_a else 'FAIL'}")
    if not ok_a:
        failures.append("(a) anchor point not exact")

    # (b) No irradiance -> no power.
    p_b = pv_ac_power_mw(0.0, 25.0)
    ok_b = p_b == 0.0
    print(f"(b) G=0              -> {p_b:.10f} MW (expected 0) "
          f"{'OK' if ok_b else 'FAIL'}")
    if not ok_b:
        failures.append("(b) zero-irradiance not zero")

    # (c) Half irradiance, same ambient: cells run cooler than at full sun
    # (Tc = 40.6 C vs 56.25 C), so output exceeds half of the full-sun value.
    p_c = pv_ac_power_mw(500.0, 25.0)
    half_a = p_a / 2.0
    ok_c = p_c > half_a
    print(f"(c) G=500,  Ta=25 C  -> {p_c:.6f} MW vs half of (a) = {half_a:.6f} MW "
          f"({(p_c / half_a - 1.0) * 100.0:+.2f} %) "
          f"{'OK (more than half, cooler cells)' if ok_c else 'FAIL'}")
    if not ok_c:
        failures.append("(c) half irradiance not above half power")

    # (d) Hotter ambient at full sun -> lower output (gamma < 0).
    p_d_hot = pv_ac_power_mw(1000.0, 45.0)
    ok_d = p_d_hot < p_a
    print(f"(d) G=1000, Ta=45 C  -> {p_d_hot:.6f} MW vs Ta=25 C -> {p_a:.6f} MW "
          f"{'OK (hotter -> lower)' if ok_d else 'FAIL'}")
    if not ok_d:
        failures.append("(d) hot ambient not below anchor")

    if failures:
        print(f"\n{len(failures)} HAND CHECK(S) OUT OF RANGE: {failures}")
        raise SystemExit(1)
    print("\nAll PV hand checks OK.")
