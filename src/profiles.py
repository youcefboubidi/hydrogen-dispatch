"""Representative-day extraction from the cached PVGIS in-plane weather (Stage 1).

Loads data/weather_inplane_<site>.csv (PVGIS seriescalc — plane-of-array
irradiance G(i) and air temperature T2m for one year) and pulls a few
contrasting 24-hour profiles for the dispatch optimizer to run on:

    clear_summer  - clearest, highest-energy summer day (max free solar)
    cloudy_summer - lowest-energy summer day (clouds/dust; same season, so it
                    isolates the cloud effect from day length)
    clear_winter  - clearest December/January day (short day, low sun angle)

Each profile is the hourly (in-plane irradiance [W/m2], ambient temperature
[degC]) that the existing PV model consumes unchanged. Pure data handling:
no optimization, no pandapower.

Run a standalone summary with:  python -m src.profiles
"""

from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# PVGIS seriescalc column names (see data/fetch_weather.py).
COL_IRRAD = "G(i)"   # global plane-of-array irradiance [W/m2]
COL_TEMP = "T2m"     # 2 m air temperature [degC]

# PVGIS timestamps are UTC; Algeria (Africa/Algiers) is UTC+1 year-round with no
# DST. We shift to local time so the hour index aligns with the CREG tariff
# bands, which are defined in local time (peak 17:00-21:00 local). Without this,
# the solar profile and the tariff would be one hour out of phase.
LOCAL_UTC_OFFSET_H = 1


def load_inplane(site="ghardaia"):
    """Load the cached in-plane weather CSV and add parsed date/hour columns."""
    csv = DATA_DIR / f"weather_inplane_{site}.csv"
    df = pd.read_csv(csv)
    # PVGIS seriescalc timestamps look like '20200101:0010' (YYYYMMDD:HHMM,
    # centred at HH:10), in UTC. Shift to local time (UTC+1) so the hour index
    # lines up with the CREG tariff bands; then derive calendar date + hour.
    dt = pd.to_datetime(df["time"], format="%Y%m%d:%H%M") \
        + pd.Timedelta(hours=LOCAL_UTC_OFFSET_H)
    df["date"] = dt.dt.date
    df["hour"] = dt.dt.hour
    df["month"] = dt.dt.month
    return df


def _day_arrays(df, date):
    """24-element (irradiance, temperature) arrays for one calendar date."""
    day = df[df["date"] == date].sort_values("hour")
    return (day[COL_IRRAD].to_numpy(dtype=float),
            day[COL_TEMP].to_numpy(dtype=float))


def representative_days(site="ghardaia"):
    """Return the named 24-hour profiles described in the module docstring.

    Returns:
        dict name -> {date, g_wm2 (24,), t_amb_c (24,), daily_kwh_m2}.
    """
    df = load_inplane(site)

    # Use only full 24-hour days so every profile is a clean day.
    counts = df.groupby("date")["hour"].count()
    full = set(counts[counts == 24].index)
    df = df[df["date"].isin(full)]

    daily = df.groupby("date")[COL_IRRAD].sum().sort_index()
    dates = np.array(list(daily.index))
    totals = daily.to_numpy()
    months = np.array([d.month for d in dates])

    def pick(mask, how):
        idx = np.where(mask)[0]
        sub = totals[idx]
        chosen = idx[np.argmax(sub) if how == "max" else np.argmin(sub)]
        return dates[chosen], totals[chosen]

    summer = (months >= 6) & (months <= 8)
    winter = (months == 12) | (months == 1)
    selection = {
        "clear_summer": pick(summer, "max"),
        "cloudy_summer": pick(summer, "min"),
        "clear_winter": pick(winter, "max"),
    }

    out = {}
    for name, (date, total) in selection.items():
        g, ta = _day_arrays(df, date)
        out[name] = {"date": str(date), "g_wm2": g, "t_amb_c": ta,
                     "daily_kwh_m2": float(total) / 1000.0}
    return out


if __name__ == "__main__":
    days = representative_days("ghardaia")
    print("Representative days for Ghardaïa (PVGIS in-plane, 2020):\n")
    for name, p in days.items():
        g = p["g_wm2"]
        sun_hours = int((g > 1.0).sum())
        print(f"  {name:14s} {p['date']}  "
              f"daily {p['daily_kwh_m2']:5.2f} kWh/m2  "
              f"peak {g.max():4.0f} W/m2  "
              f"{sun_hours:2d} h of sun  "
              f"Ta {p['t_amb_c'].min():.0f}-{p['t_amb_c'].max():.0f} degC")
