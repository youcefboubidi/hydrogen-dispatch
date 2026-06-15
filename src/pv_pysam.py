"""Real Ghardaïa PV generation from the PySAM run (production PV source).

Loads ghardaia_solar_generation.csv — NREL SAM AC output for the validated
~0.53 MW plant, driven by real CAMS irradiance (15-min, 2023), in UTC — converts
it to MW in LOCAL time (Algeria UTC+1, no DST), and extracts representative-day
15-minute profiles for the dispatch.

This is now the PV source the dispatch consumes. The engineering pv_model.py
stays as the documented, ETAP-anchored model and a full-sun cross-check; it is
no longer in the dispatch loop.

Pure data handling. Run a standalone summary with:  python -m src.pv_pysam
"""

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
GEN_PATH = REPO_ROOT / "ghardaia_solar_generation.csv"

LOCAL_UTC_OFFSET_H = 1   # Algeria (Africa/Algiers) is UTC+1 year-round, no DST
STEPS_PER_DAY = 96       # 15-minute resolution
STEP_H = 0.25            # hours per step


def load_pv_mw(path=GEN_PATH):
    """Load the PySAM AC generation -> pd.Series of PV [MW] in LOCAL time.

    kW -> MW, negatives (inverter standby) clipped to 0, UTC -> local (+1 h) so
    it aligns with the CREG tariff bands used downstream.
    """
    df = pd.read_csv(path)
    t = pd.to_datetime(df.iloc[:, 0]) + pd.Timedelta(hours=LOCAL_UTC_OFFSET_H)
    mw = (df.iloc[:, 1].astype(float) / 1000.0).clip(lower=0.0)
    return pd.Series(mw.to_numpy(), index=t).sort_index()


def representative_days(path=GEN_PATH):
    """Clear-summer / cloudy-summer / clear-winter 15-min PV profiles [MW].

    Returns dict name -> {date, pv_mw (96,), energy_mwh}. Days are selected by
    daily PV energy within season (max summer, min summer, max December/January).
    """
    s = load_pv_mw(path)
    df = pd.DataFrame({"pv": s.to_numpy()}, index=s.index)
    df["date"] = df.index.date

    counts = df.groupby("date")["pv"].count()
    full = set(counts[counts == STEPS_PER_DAY].index)   # whole 96-step local days
    df = df[df["date"].isin(full)]

    daily = df.groupby("date")["pv"].sum()              # proportional to energy
    dates = np.array(list(daily.index))
    totals = daily.to_numpy()
    months = np.array([d.month for d in dates])

    def pick(mask, how):
        idx = np.where(mask)[0]
        sub = totals[idx]
        return dates[idx[np.argmax(sub) if how == "max" else np.argmin(sub)]]

    summer = (months >= 6) & (months <= 8)
    winter = (months == 12) | (months == 1)
    selection = {
        "clear_summer": pick(summer, "max"),
        "cloudy_summer": pick(summer, "min"),
        "clear_winter": pick(winter, "max"),
    }

    out = {}
    for name, date in selection.items():
        day = df[df["date"] == date].sort_index()
        pv = day["pv"].to_numpy(dtype=float)
        out[name] = {"date": str(date), "pv_mw": pv,
                     "energy_mwh": float(pv.sum() * STEP_H)}
    return out


if __name__ == "__main__":
    s = load_pv_mw()
    print(f"PySAM PV (local time): {len(s)} steps, "
          f"{s.index[0]} -> {s.index[-1]}, peak {s.max():.3f} MW")
    print(f"annual energy: {s.sum() * STEP_H:.0f} MWh\n")
    for name, p in representative_days().items():
        pv = p["pv_mw"]
        sun = int((pv > 1e-4).sum())
        print(f"  {name:14s} {p['date']}  energy {p['energy_mwh']:5.2f} MWh  "
              f"peak {pv.max():.3f} MW  {sun:2d}/96 steps with sun")
