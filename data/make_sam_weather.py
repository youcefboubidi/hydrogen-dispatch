"""Build a SAM-format weather file for PySAM from CAMS irradiance + temp/wind.

Fuses:
  * CAMS Radiation Service all-sky irradiance (real Ghardaia, 15-min, UTC) —
    GHI/DNI/DHI, converted from Wh/m2 per 15-min step to average W/m2 (x4).
  * Temperature + wind: PLACEHOLDER from the PVGIS TMY Ghardaia pull (a typical
    year, mapped by month/day/hour). To be replaced by ERA5 2023 when it lands,
    then just re-run this script.

Output: a single-year (2023), 15-minute SAM CSV that PySAM's
tools.SAM_CSV_to_solar_data() reads directly. 2023 -> 365*96 = 35,040 rows,
a valid 15-min single-year count for SAM.

CAMS timestamps are UTC; we keep them UTC and set the SAM "Time Zone" field to 0
so PySAM computes the solar position correctly. The PySAM AC output is therefore
UTC too — the dispatch layer applies the +1 local shift downstream (as it does
for the tariff), so nothing is double-shifted here.

Run from the repo root:  python data/make_sam_weather.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
CAMS_PATH = REPO_ROOT / "Ghardaia CAMS Radiation Service.csv"
TMY_PATH = REPO_ROOT / "data" / "weather_tmy_ghardaia.csv"
OUT_PATH = REPO_ROOT / "data" / "ghardaia_sam_2023_15min.csv"

YEAR = 2023
LAT, LON, ELEV = 32.5873, 3.7314, 549   # from the CAMS header
WH_TO_W_15MIN = 4.0                      # Wh/m2 per 15-min step -> average W/m2


def load_cams(path):
    """Parse the CAMS SoDa CSV -> DataFrame indexed by interval-start (UTC).

    Irradiance columns converted from Wh/m2 (per 15-min) to average W/m2.
    """
    cols = ["period", "toa", "cs_ghi", "cs_bhi", "cs_dhi", "cs_bni",
            "ghi", "bhi", "dhi", "bni", "reliability"]
    df = pd.read_csv(path, sep=";", comment="#", header=None, names=cols,
                     engine="python")
    start = df["period"].str.split("/").str[0]
    df.index = pd.to_datetime(start, format="%Y-%m-%dT%H:%M:%S.%f")
    for c in ("ghi", "dhi", "bni"):
        df[c] = pd.to_numeric(df[c], errors="coerce") * WH_TO_W_15MIN
    return df[["ghi", "dhi", "bni", "reliability"]]


def tmy_temp_wind_lookup(path):
    """PVGIS TMY -> per (month, day, hour) temperature [C] and wind [m/s]."""
    t = pd.read_csv(path)
    dt = pd.to_datetime(t["time(UTC)"], format="%Y%m%d:%H%M")
    out = pd.DataFrame({
        "Month": dt.dt.month, "Day": dt.dt.day, "Hour": dt.dt.hour,
        "Temperature": t["T2m"].astype(float),
        "Wind Speed": t["WS10m"].astype(float),
    })
    # One row per (month, day, hour); TMY already is hourly-unique.
    return out.drop_duplicates(["Month", "Day", "Hour"])


def main():
    cams = load_cams(CAMS_PATH)

    # Complete 15-min grid for the target year, so SAM gets a clean 35,040 rows.
    grid = pd.date_range(f"{YEAR}-01-01 00:00", f"{YEAR}-12-31 23:45", freq="15min")
    cams = cams.reindex(grid)
    # Irradiance: interpolate tiny gaps, then zero-fill anything still missing.
    for c in ("ghi", "dhi", "bni"):
        cams[c] = cams[c].interpolate(limit=4).fillna(0.0).clip(lower=0.0)

    sam = pd.DataFrame(index=grid)
    sam["Year"] = grid.year
    sam["Month"] = grid.month
    sam["Day"] = grid.day
    sam["Hour"] = grid.hour
    sam["Minute"] = grid.minute
    sam["GHI"] = cams["ghi"].round(1).values
    sam["DNI"] = cams["bni"].round(1).values   # BNI = beam normal = DNI
    sam["DHI"] = cams["dhi"].round(1).values

    # Temperature + wind placeholder from TMY, mapped by (month, day, hour).
    tw = tmy_temp_wind_lookup(TMY_PATH)
    keyed = sam.merge(tw, on=["Month", "Day", "Hour"], how="left")
    keyed["Temperature"] = keyed["Temperature"].ffill().bfill().round(1)
    keyed["Wind Speed"] = keyed["Wind Speed"].ffill().bfill().round(2)

    data = keyed[["Year", "Month", "Day", "Hour", "Minute",
                  "GHI", "DNI", "DHI", "Temperature", "Wind Speed"]]

    # SAM CSV: metadata key row, metadata value row, then the data table.
    meta_keys = ["Source", "Location ID", "City", "State", "Country",
                 "Latitude", "Longitude", "Time Zone", "Elevation"]
    meta_vals = ["CAMS+PVGIS(temp placeholder)", "ghardaia", "Ghardaia", "-",
                 "Algeria", LAT, LON, 0, ELEV]
    with open(OUT_PATH, "w", newline="") as f:
        f.write(",".join(meta_keys) + "\n")
        f.write(",".join(str(v) for v in meta_vals) + "\n")
    data.to_csv(OUT_PATH, mode="a", index=False)

    # --- report ---
    n = len(data)
    day = data[(data["Month"] == 6) & (data["Day"] == 21)]
    print(f"wrote {OUT_PATH}")
    print(f"rows: {n} (expected 35040 for a 15-min non-leap year: "
          f"{'OK' if n == 35040 else 'CHECK'})")
    print(f"GHI  W/m2: max {data['GHI'].max():.0f}, mean {data['GHI'].mean():.1f}")
    print(f"DNI  W/m2: max {data['DNI'].max():.0f}")
    print(f"Temp C   : min {data['Temperature'].min():.1f}, "
          f"max {data['Temperature'].max():.1f}, mean {data['Temperature'].mean():.1f}")
    print(f"Wind m/s : mean {data['Wind Speed'].mean():.2f}")
    annual_kwh_m2 = data["GHI"].sum() * 0.25 / 1000.0
    print(f"annual GHI: {annual_kwh_m2:.0f} kWh/m2 "
          f"(Ghardaia expected ~2000-2200)")
    print("\nsample — June 21 around solar noon (UTC):")
    print(day[(day["Hour"] >= 11) & (day["Hour"] <= 12)].to_string(index=False))


if __name__ == "__main__":
    main()
