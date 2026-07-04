"""Electricity tariff economics (Stage 1) — the real Algerian time-of-use price.

Encodes the official Algerian medium-voltage time-of-use tariff that applies to
the 11 kV reference network, so the optimizer can decide *when* to run the
electrolyzer, not just how hard. Replacing the single flat 4.68 DA/kWh with a
clock-dependent price is what turns "least-cost dispatch" into a real decision:
running during the 17:00-21:00 peak costs 6.7x the overnight rate.

All rates are the official CREG schedule for non-household medium-voltage
customers (tariff code 51NM); see SOURCES. Pure module: no I/O, no pandapower.
Prices are in Algerian dinar (DA). 1 DA = 100 cDA (centimes).

The electrolyzer hardware/CAPEX side of the cost (for levelized cost of
hydrogen) is deliberately NOT here yet — it is added next, sourced from IRENA,
so every number in this file traces to one regulator document.

SOURCES
-------
CREG (Commission de Regulation de l'Electricite et du Gaz), "Comment lire votre
facture" — medium-voltage triple time-of-use tariff, code 51NM:
    Pointe  (peak)   17:00-21:00              811.47 cDA/kWh = 8.1147 DA/kWh
    Pleines (full)   06:00-17:00, 21:00-22:30 216.45 cDA/kWh = 2.1645 DA/kWh
    Creuses (night)  22:30-06:00              120.50 cDA/kWh = 1.2050 DA/kWh
    Demand charge (prime de puissance)        4.37 DA/kW/month (subscribed power)
    https://creg.gov.dz/fr/consommateurs/comment-lire-votre-facture/
"""

# CREG medium-voltage time-of-use energy rates [DA/kWh] (tariff code 51NM).
PRICE_POINTE_DA_PER_KWH = 8.1147    # peak,  17:00-21:00
PRICE_PLEINES_DA_PER_KWH = 2.1645   # full,  06:00-17:00 and 21:00-22:30
PRICE_CREUSES_DA_PER_KWH = 1.2050   # night, 22:30-06:00

# Demand charge on subscribed power (prime de puissance) [DA/kW/month].
DEMAND_CHARGE_DA_PER_KW_MONTH = 4.37

# The flat tariff used in Phases 4-6, kept for before/after comparison [DA/kWh].
FLAT_TARIFF_DA_PER_KWH = 4.68

# Time-of-use band boundaries [hour of day]. The 22:30 night boundary is the
# one sub-hourly edge; the price function takes a fractional hour so an hourly
# schedule can sample it at whatever convention (hour start / midpoint) it uses.
_POINTE_START, _POINTE_END = 17.0, 21.0
_CREUSES_START, _CREUSES_END = 22.5, 6.0


def grid_price_da_per_kwh(hour):
    """Time-of-use energy price [DA/kWh] at a given hour of day.

    Args:
        hour: hour of day in [0, 24); fractional values allowed (e.g. 22.5).
            Values outside the range are wrapped modulo 24.

    Returns:
        Energy price [DA/kWh] for that instant (CREG code 51NM bands).
    """
    h = hour % 24.0
    if _POINTE_START <= h < _POINTE_END:
        return PRICE_POINTE_DA_PER_KWH
    if h >= _CREUSES_START or h < _CREUSES_END:
        return PRICE_CREUSES_DA_PER_KWH
    return PRICE_PLEINES_DA_PER_KWH


def band_name(hour):
    """Name of the tariff band at a given hour ('pointe' / 'pleines' / 'creuses')."""
    h = hour % 24.0
    if _POINTE_START <= h < _POINTE_END:
        return "pointe"
    if h >= _CREUSES_START or h < _CREUSES_END:
        return "creuses"
    return "pleines"


def energy_cost_da(power_mw, hour, duration_h=1.0):
    """Grid energy cost [DA] for drawing power over a time step at the hour's rate.

    Only positive (import) power is billed; export is not remunerated, matching
    the convention in src.pipeline (max(grid_p, 0)).

    Args:
        power_mw: grid power drawn [MW]; <= 0 (export) costs nothing.
        hour: hour of day for the tariff lookup.
        duration_h: length of the time step [h] (1.0 for an hourly schedule).

    Returns:
        Energy cost [DA] over the step.
    """
    import_mw = max(power_mw, 0.0)
    return grid_price_da_per_kwh(hour) * import_mw * 1000.0 * duration_h


if __name__ == "__main__":
    print("CREG medium-voltage time-of-use tariff (code 51NM), DA/kWh:\n")
    print(f"  {'hour':>5}  {'band':<8} {'price':>8}")
    for h in range(24):
        bar = "#" * round(grid_price_da_per_kwh(h) * 3)
        print(f"  {h:02d}:00  {band_name(h):<8} {grid_price_da_per_kwh(h):>7.4f}  {bar}")

    day_avg = sum(grid_price_da_per_kwh(h) for h in range(24)) / 24.0
    ratio = PRICE_POINTE_DA_PER_KWH / PRICE_CREUSES_DA_PER_KWH
    print(f"\n  flat tariff (old):      {FLAT_TARIFF_DA_PER_KWH:.4f} DA/kWh")
    print(f"  simple 24h average:     {day_avg:.4f} DA/kWh")
    print(f"  peak / off-peak ratio:  {ratio:.2f}x  "
          f"({PRICE_POINTE_DA_PER_KWH} vs {PRICE_CREUSES_DA_PER_KWH} DA/kWh)")
    print(f"  demand charge:          {DEMAND_CHARGE_DA_PER_KW_MONTH} DA/kW/month")
