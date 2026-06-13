"""Fetch real hourly weather (irradiance + air temperature) from PVGIS.

Pulls a Typical Meteorological Year (TMY) for the plant site from the EU JRC
PVGIS service and caches it to data/weather_tmy_<site>.csv, so the rest of the
pipeline runs offline and reproducibly on real measured-climate data instead of
a single invented operating point.

TMY is the standard data product for this kind of study: for each month it
stitches together the most "typical" real month from a multi-year record, giving
one representative 8760-hour year. We keep the raw PVGIS columns; plane-of-array
transposition for the PV model is applied downstream.

PVGIS TMY API (v5.2): https://re.jrc.ec.europa.eu/api/v5_2/tmy
Key fields: T2m (2 m air temperature, degC), G(h) (global horizontal irradiance,
W/m2), Gb(n) (beam normal), Gd(h) (diffuse horizontal).

Usage (from the repo root):
    python data/fetch_weather.py                      # default site (Boumerdes)
    python data/fetch_weather.py 27.88 -0.28 adrar    # lat lon name
"""

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent

# Known Algerian sites (lat, lon). Boumerdes is the institution location; Adrar
# / Ghardaia are high-irradiance southern sites (the national solar program's
# target region) and make the solar-vs-grid trade-off more dramatic.
SITES = {
    "boumerdes": (36.75, 3.47),
    "adrar": (27.88, -0.28),
    "ghardaia": (32.49, 3.67),
}


def fetch_tmy(lat, lon):
    """Return the PVGIS TMY response as a parsed JSON dict (raises on failure)."""
    url = (f"https://re.jrc.ec.europa.eu/api/v5_2/tmy"
           f"?lat={lat}&lon={lon}&outputformat=json")
    req = urllib.request.Request(url, headers={"User-Agent": "hydrogen-dispatch/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_inplane(lat, lon, tilt, azimuth, year):
    """Return PVGIS seriescalc hourly in-plane irradiance for one year (JSON dict).

    seriescalc with a fixed tilt/azimuth makes PVGIS compute the global
    plane-of-array irradiance G(i) with its own validated transposition model —
    so the PV model (anchored at plane-of-array G=1000) is fed the correct
    irradiance without any custom solar geometry on our side.

    Args:
        lat, lon: site coordinates [deg].
        tilt: array tilt from horizontal [deg].
        azimuth: array azimuth, PVGIS convention 0 = south [deg].
        year: single calendar year to pull (keeps it to 8760 rows).
    """
    url = (f"https://re.jrc.ec.europa.eu/api/v5_2/seriescalc"
           f"?lat={lat}&lon={lon}&angle={tilt}&aspect={azimuth}"
           f"&startyear={year}&endyear={year}&outputformat=json")
    req = urllib.request.Request(url, headers={"User-Agent": "hydrogen-dispatch/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


# Fixed-array geometry for the in-plane pull. Tilt ~ latitude is the standard
# rule-of-thumb optimum for a year-round fixed array; south-facing (PVGIS
# aspect 0). Documented so the choice is explicit and reproducible.
INPLANE_TILT_DEG = 30.0
INPLANE_AZIMUTH_DEG = 0.0
INPLANE_YEAR = 2020


def _tmy(argv):
    if len(argv) >= 2:
        lat, lon = float(argv[0]), float(argv[1])
        site = argv[2] if len(argv) >= 3 else f"{lat}_{lon}"
    else:
        site = "boumerdes"
        lat, lon = SITES[site]

    out_csv = DATA_DIR / f"weather_tmy_{site}.csv"
    print(f"PVGIS TMY (global horizontal) for {site} "
          f"(lat={lat}, lon={lon}) ...", flush=True)
    payload = fetch_tmy(lat, lon)
    df = pd.DataFrame(payload["outputs"]["tmy_hourly"])
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")

    cols = list(df.columns)
    ghi = next((c for c in cols if c.startswith("G(")), None)
    print(f"saved: {out_csv}  ({len(df)} rows, columns: {cols})")
    if ghi:
        print(f"  {ghi}: max {df[ghi].max():.0f}, mean {df[ghi].mean():.1f} W/m2")
    if "T2m" in cols:
        print(f"  T2m: min {df['T2m'].min():.1f}, max {df['T2m'].max():.1f}, "
              f"mean {df['T2m'].mean():.1f} degC")


def _inplane(argv):
    # argv: lat lon [name] (after the leading "inplane" token)
    lat, lon = float(argv[0]), float(argv[1])
    site = argv[2] if len(argv) >= 3 else f"{lat}_{lon}"

    out_csv = DATA_DIR / f"weather_inplane_{site}.csv"
    print(f"PVGIS seriescalc (plane-of-array, tilt {INPLANE_TILT_DEG} deg, "
          f"south) for {site} (lat={lat}, lon={lon}), year {INPLANE_YEAR} ...",
          flush=True)
    payload = fetch_inplane(lat, lon, INPLANE_TILT_DEG, INPLANE_AZIMUTH_DEG,
                            INPLANE_YEAR)
    df = pd.DataFrame(payload["outputs"]["hourly"])
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")

    cols = list(df.columns)
    gi = next((c for c in cols if c.startswith("G(i")), None)
    print(f"saved: {out_csv}  ({len(df)} rows, columns: {cols})")
    if gi:
        print(f"  {gi} in-plane irradiance: max {df[gi].max():.0f}, "
              f"mean {df[gi].mean():.1f} W/m2")
    if "T2m" in cols:
        print(f"  T2m: min {df['T2m'].min():.1f}, max {df['T2m'].max():.1f}, "
              f"mean {df['T2m'].mean():.1f} degC")


def main(argv):
    try:
        if argv and argv[0] == "inplane":
            _inplane(argv[1:])
        else:
            _tmy(argv)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"\nFETCH FAILED ({type(exc).__name__}: {exc}).")
        print("If this machine has no outbound network, export the data "
              "manually from the PVGIS portal and drop the CSV in data/:")
        print("  https://re.jrc.ec.europa.eu/pvg_tools/en/")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
