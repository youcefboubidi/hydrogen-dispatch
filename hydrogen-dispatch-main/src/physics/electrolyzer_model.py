"""PEM electrolyzer model (Phase 3) — polarization curve, Faraday's law, specific energy.

Implements the cell model of Chapter 2 with activation (Tafel form) and ohmic
overpotentials (concentration term neglected — the stack never approaches its
limiting current density at <= 2 A/cm²):

    V_cell(i) = E_rev + eta_act + eta_ohm
    eta_act   = (R * T_op / (alpha * F)) * ln(i / i0)     [lumped two-electrode Tafel]
    eta_ohm   = r_asr * i                                  [linear ohmic]

    P_stack(i) = n_cells * V_cell(i) * i * A_cell          [W, i in A/cm², A in cm²]

The inverse i(P) is solved numerically (scipy brentq; P_stack is strictly
increasing in i, so the root is unique). Hydrogen production follows Faraday's
law with a constant Faraday efficiency:

    mdot_H2 = eta_F * n_cells * (i * A_cell) / (z * F) * M_H2      [kg/s]

The electrical side is the 800 kW constant-power load ELY of
``data/etap_parameters.md`` section 2; the stack is sized so rated power is
exactly 0.800 MW at the rated current density.

Pure module: no I/O, no pandapower. Run the hand checks with:
    python src/physics/electrolyzer_model.py
"""

from math import log

from scipy.optimize import brentq

# Physical constants (CODATA 2018).
R_GAS = 8.314462618      # molar gas constant [J/(mol*K)]
F_C_PER_MOL = 96485.33212  # Faraday constant [C/mol]
Z_ELECTRONS = 2          # electrons transferred per H2 molecule [-]
M_H2_KG_PER_MOL = 2.016e-3  # molar mass of H2 [kg/mol]

# Representative PEM cell parameters (literature values, e.g. Carmo et al. 2013
# review; Garcia-Valverde et al. 2012 model).
T_OP_K = 333.15          # operating temperature 60 °C — typical PEM range 50-80 °C [K]
ALPHA = 0.5              # charge-transfer coefficient, symmetric barrier [-]
I0_A_CM2 = 1.0e-3        # effective exchange current density of the lumped
                         # single-Tafel cell (absorbs both electrodes) [A/cm²]
R_ASR_OHM_CM2 = 0.20     # area-specific resistance, membrane + contacts;
                         # mid of the 0.15-0.25 ohm*cm² literature band [ohm*cm²]
I_RATED_A_CM2 = 2.0      # rated current density — modern PEM stacks run 1-3 A/cm² [A/cm²]
ETA_FARADAY = 0.99       # Faraday (current) efficiency [-]

# Reversible cell voltage at T_op: standard linearization around 25 °C,
# E_rev(T) = 1.229 - 0.9e-3 * (T - 298.15)  ->  1.1975 V at 60 °C.
E_REV_V = 1.229 - 0.9e-3 * (T_OP_K - 298.15)

# Stack sizing. n_cells is a chosen integer representative of an MW-class PEM
# stack (lumped single-stack equivalent of the 800 kW system); A_cell is then
# back-solved — NOT a datasheet value — so that rated power is exactly 0.800 MW
# at i_rated: A_cell = P_rated / (n_cells * V_cell(i_rated) * i_rated)
# ≈ 983.3 cm² (plausible MW-class cell area). Stack at rated: ~407 V, ~1967 A.
P_RATED_MW = 0.800       # rated electrical power = ELY rating [MW]
P_MIN_MW = 0.080         # minimum turndown, 10 % of P_RATED_MW [MW]
N_CELLS = 200            # cells in series [-]


def v_cell(i_a_cm2):
    """Cell voltage V_cell(i) = E_rev + eta_act + eta_ohm.

    Tafel activation term (R*T/(alpha*F)) * ln(i/i0) — valid for i >> i0,
    which holds everywhere in the operating window (i >= ~0.26 A/cm²) — plus
    linear ohmic term r_asr * i. Concentration overpotential neglected.

    Args:
        i_a_cm2: current density [A/cm²], must be > 0.

    Returns:
        Cell voltage [V].
    """
    if i_a_cm2 <= 0.0:
        raise ValueError(f"current density must be > 0 A/cm2, got {i_a_cm2}")
    eta_act = (R_GAS * T_OP_K / (ALPHA * F_C_PER_MOL)) * log(i_a_cm2 / I0_A_CM2)
    eta_ohm = R_ASR_OHM_CM2 * i_a_cm2
    return E_REV_V + eta_act + eta_ohm


# Back-solved cell area for an exact 0.800 MW rating at i_rated (see sizing
# comment above). Defined after v_cell() because it evaluates the curve.
A_CELL_CM2 = P_RATED_MW * 1e6 / (N_CELLS * v_cell(I_RATED_A_CM2) * I_RATED_A_CM2)


def stack_power_mw(i_a_cm2):
    """Stack electrical power P(i) = n_cells * V_cell(i) * i * A_cell.

    Args:
        i_a_cm2: current density [A/cm²], must be > 0.

    Returns:
        Stack DC power [MW]. Exactly 0.800 MW at i = I_RATED_A_CM2
        (by construction of A_CELL_CM2).
    """
    return N_CELLS * v_cell(i_a_cm2) * i_a_cm2 * A_CELL_CM2 / 1e6


def _require_in_window(p_mw):
    """Raise ValueError if p_mw is outside the operating window [P_MIN_MW, P_RATED_MW]."""
    if p_mw < P_MIN_MW:
        raise ValueError(
            f"electrolyzer power {p_mw} MW below minimum turndown "
            f"{P_MIN_MW} MW (10 % of rated {P_RATED_MW} MW)")
    if p_mw > P_RATED_MW:
        raise ValueError(
            f"electrolyzer power {p_mw} MW above rated {P_RATED_MW} MW")


def current_density_from_power(p_mw):
    """Inverse of the polarization curve: current density i for stack power P.

    Solved numerically with scipy brentq on [1e-6, i_rated]. P(i) is strictly
    increasing (dV/di = b/i + r > 0 and V > 0 on the bracket), so the root is
    unique; P(1e-6) ≈ 0 < P_MIN_MW and P(i_rated) = P_RATED_MW bracket every
    in-window target.

    Args:
        p_mw: stack electrical power [MW], must lie in
            [P_MIN_MW, P_RATED_MW] = [0.080, 0.800] MW.

    Returns:
        Current density i [A/cm²].

    Raises:
        ValueError: if p_mw is outside the operating window.
    """
    _require_in_window(p_mw)
    return brentq(lambda i: stack_power_mw(i) - p_mw, 1e-6, I_RATED_A_CM2,
                  xtol=1e-12)


def mdot_h2_kg_per_h(p_mw):
    """Hydrogen mass production rate by Faraday's law.

    mdot = eta_F * n_cells * I_cell / (z * F) * M_H2 * 3600, with the cell
    current I_cell = i(P) * A_cell.

    Args:
        p_mw: stack electrical power [MW], in [P_MIN_MW, P_RATED_MW].

    Returns:
        Hydrogen production [kg/h].

    Raises:
        ValueError: if p_mw is outside the operating window.
    """
    i_a_cm2 = current_density_from_power(p_mw)
    i_cell_a = i_a_cm2 * A_CELL_CM2
    mol_per_s = ETA_FARADAY * N_CELLS * i_cell_a / (Z_ELECTRONS * F_C_PER_MOL)
    return mol_per_s * M_H2_KG_PER_MOL * 3600.0


def specific_energy_kwh_per_kg(p_mw):
    """Specific energy consumption: electrical energy per kilogram of hydrogen.

    Decreases at part load (lower V_cell at lower i, while kg/h tracks current);
    equals 26.86 * V_cell numerically for this stack (z*F/(eta_F*M_H2*3.6e6)).

    Args:
        p_mw: stack electrical power [MW], in [P_MIN_MW, P_RATED_MW].

    Returns:
        Specific energy [kWh/kg].

    Raises:
        ValueError: if p_mw is outside the operating window.
    """
    return p_mw * 1000.0 / mdot_h2_kg_per_h(p_mw)


if __name__ == "__main__":
    failures = []

    print(f"stack sizing: {N_CELLS} cells x {A_CELL_CM2:.1f} cm2, "
          f"rated {stack_power_mw(I_RATED_A_CM2):.6f} MW at {I_RATED_A_CM2} A/cm2 "
          f"({N_CELLS * v_cell(I_RATED_A_CM2):.1f} V, "
          f"{I_RATED_A_CM2 * A_CELL_CM2:.0f} A)\n")

    # (a) Cell voltage at rated current density.
    v_rated = v_cell(I_RATED_A_CM2)
    ok_a = 1.9 <= v_rated <= 2.2
    print(f"(a) V_cell({I_RATED_A_CM2} A/cm2) = {v_rated:.4f} V "
          f"(expected 1.9-2.2 V) {'OK' if ok_a else 'OUT OF RANGE'}")
    if not ok_a:
        failures.append("(a) V_cell at i_rated")

    # (b) Hydrogen rate and specific energy at rated power.
    mdot_rated = mdot_h2_kg_per_h(P_RATED_MW)
    se_rated = specific_energy_kwh_per_kg(P_RATED_MW)
    ok_b = 14.0 <= mdot_rated <= 15.0 and 52.0 <= se_rated <= 56.0
    print(f"(b) P = {P_RATED_MW} MW -> {mdot_rated:.3f} kg/h, "
          f"{se_rated:.2f} kWh/kg (expected ~14-15 kg/h, 52-56 kWh/kg) "
          f"{'OK' if ok_b else 'OUT OF RANGE'}")
    if not ok_b:
        failures.append("(b) mdot/specific energy at rated")

    # (c) Half power -> more than half the hydrogen (better specific energy
    # at part load: lower current density -> lower V_cell).
    mdot_half = mdot_h2_kg_per_h(0.400)
    se_half = specific_energy_kwh_per_kg(0.400)
    ok_c = mdot_half > mdot_rated / 2.0
    print(f"(c) P = 0.400 MW -> {mdot_half:.3f} kg/h vs half of (b) = "
          f"{mdot_rated / 2.0:.3f} kg/h ({(mdot_half / (mdot_rated / 2.0) - 1.0) * 100.0:+.1f} %) "
          f"{'OK' if ok_c else 'OUT OF RANGE'}")
    print(f"    specific energy: {se_half:.2f} kWh/kg at 0.400 MW vs "
          f"{se_rated:.2f} kWh/kg at rated")
    if not ok_c:
        failures.append("(c) part-load mdot")

    # (d) Below minimum turndown must raise.
    try:
        mdot_h2_kg_per_h(0.05)
    except ValueError as exc:
        print(f"(d) P = 0.05 MW -> ValueError as expected: {exc}")
    else:
        print("(d) P = 0.05 MW -> NO ERROR RAISED (expected ValueError)")
        failures.append("(d) below-minimum not rejected")

    if failures:
        print(f"\n{len(failures)} HAND CHECK(S) OUT OF RANGE: {failures}")
        raise SystemExit(1)
    print("\nAll electrolyzer hand checks OK.")
