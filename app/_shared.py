"""Shared building blocks for the Streamlit dashboard tabs.

Cached data loaders, the colour palette / tariff bands, x-axis helpers, the
dispatch-chart builder, and the cached optimizer runners. Every tab imports from
here so there is one PV loader, one palette, and one chart definition.

Import side effects (sys.path + pymoo warning config) are applied on import so a
tab module can `from app._shared import ...` without repeating the boilerplate.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pymoo.config import Config

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

Config.warnings["not_compiled"] = False

from src.battery_dispatch import Battery, optimize_day_battery
from src.day_dispatch import (
    HOURS, STEP_H, STEPS, STEPS_PER_HOUR,
    _PRICE_BY_HOUR,
    optimize_day,
    verify_day_feasibility,
)
from src.economics import band_name
from src.pv_data import STEPS_PER_DAY, load_pv_mw, representative_days

# ── representative-day labels ──────────────────────────────────────────────────
DAY_KEYS = ["clear_summer", "cloudy_summer", "clear_winter"]
DAY_LABELS = {
    "clear_summer":  "Clear Summer",
    "cloudy_summer": "Cloudy Summer",
    "clear_winter":  "Clear Winter",
}

# ── palette (shared across every chart) ────────────────────────────────────────
# High-contrast, colourblind-aware set tuned for visibility on a white background.
COLOR_PV       = "#15803d"   # strong green
COLOR_SETPOINT = "#1d4ed8"   # strong blue
COLOR_GRID     = "#ea580c"   # strong orange
COLOR_TARIFF   = "#7c3aed"   # strong violet
COLOR_BATTERY  = "#0d9488"   # teal
COLOR_SOC      = "#dc2626"   # red

# CREG tariff band shading
_BAND_CREUSES_COLOR = "rgba(191, 219, 254, 0.60)"   # light blue (cheap night)
_BAND_POINTE_COLOR  = "rgba(254, 202, 202, 0.70)"   # light red  (peak)

# Shared legend + layout styling so every chart reads the same way.
# All chart text is black for maximum legibility / print contrast.
BLACK = "#000000"
FONT = dict(color=BLACK, size=12)
LEGEND_STYLE = dict(
    orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
    bgcolor="rgba(255,255,255,0.92)", bordercolor="#94a3b8", borderwidth=1,
    font=dict(size=12.5, color=BLACK), itemsizing="constant",
)
AXIS_TITLE_FONT = dict(size=13, color=BLACK)

# ── x-axis helpers ─────────────────────────────────────────────────────────────
X_STEPS = np.arange(STEPS) * STEP_H              # 0.00, 0.25, …, 23.75
PRICE_STEPS = np.array([_PRICE_BY_HOUR[h] for h in range(HOURS)
                        for _ in range(STEPS_PER_HOUR)])


# ── cached loaders / runners ───────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_days():
    """Representative-day PV profiles {key: {date, pv_mw(96), energy_mwh}}."""
    return representative_days()


@st.cache_data(show_spinner=False)
def all_days():
    """Every full 96-step real day in the dataset, keyed by ISO date string.

    {YYYY-MM-DD: {date, pv_mw(96), energy_mwh}} — the real Ghardaïa 2023
    CAMS→PySAM PV in local time. Partial days (incomplete 96 steps) are dropped.
    """
    s = load_pv_mw()
    df = pd.DataFrame({"pv": s.to_numpy()}, index=s.index)
    df["date"] = df.index.date
    counts = df.groupby("date")["pv"].count()
    out = {}
    for d, c in counts.items():
        if c != STEPS_PER_DAY:
            continue
        pv = df[df["date"] == d].sort_index()["pv"].to_numpy(dtype=float)
        out[str(d)] = {"date": str(d), "pv_mw": pv,
                       "energy_mwh": float(pv.sum() * STEP_H)}
    return out


@st.cache_data(show_spinner=False)
def run_optimization_date(date_str, demand_kg, seed=0):
    """PSO least-cost dispatch for a specific real dataset day (cached by inputs)."""
    pv = all_days()[date_str]["pv_mw"]
    return optimize_day(pv, demand_kg, seed=seed)


@st.cache_data(show_spinner=False)
def run_optimization_battery_date(date_str, demand_kg, capacity_mwh, hours=4.0, seed=0):
    """PSO setpoints + LP-optimal storage for a specific real dataset day."""
    pv = all_days()[date_str]["pv_mw"]
    battery = Battery.from_hours(capacity_mwh, hours=hours)
    return optimize_day_battery(pv, demand_kg, battery, seeds=(seed,))


@st.cache_data(show_spinner=False)
def run_feasibility_date(date_str, hourly_setpoints):
    """Pandapower feasibility for a 24-h schedule on a specific real dataset day."""
    pv = all_days()[date_str]["pv_mw"]
    return verify_day_feasibility(np.asarray(hourly_setpoints), pv)


@st.cache_data(show_spinner=False)
def run_optimization(day_name, demand_kg, seed=0):
    """PSO least-cost dispatch (no battery), cached by inputs."""
    pv = load_days()[day_name]["pv_mw"]
    return optimize_day(pv, demand_kg, seed=seed)


@st.cache_data(show_spinner=False)
def run_optimization_battery(day_name, demand_kg, capacity_mwh, hours=4.0, seed=0):
    """PSO setpoints + LP-optimal storage, cached by inputs."""
    pv = load_days()[day_name]["pv_mw"]
    battery = Battery.from_hours(capacity_mwh, hours=hours)
    return optimize_day_battery(pv, demand_kg, battery, seeds=(seed,))


@st.cache_data(show_spinner=False)
def run_feasibility(day_name, hourly_setpoints):
    """Pandapower feasibility on a 24-hour setpoint schedule (electrolyzer + PV)."""
    pv = load_days()[day_name]["pv_mw"]
    return verify_day_feasibility(np.asarray(hourly_setpoints), pv)


@st.cache_data(show_spinner=False)
def read_table(rel_path):
    """Read a results CSV (UTF-8-BOM tolerant). Returns None if missing."""
    path = REPO_ROOT / rel_path
    if not path.exists():
        return None
    return pd.read_csv(path, encoding="utf-8-sig")


# ── derived metrics ────────────────────────────────────────────────────────────
def solar_metrics(result):
    """Solar-to-electrolyzer fraction [%] and grid import [MWh] from a result dict."""
    sp = np.asarray(result["setpoints"])
    pv = np.asarray(result["pv_mw"])
    grid = np.asarray(result["grid_p_mw"])
    solar_to_elz = float(np.minimum(pv, sp).sum() * STEP_H)
    total_elz = float(sp.sum() * STEP_H)
    frac = 100.0 * solar_to_elz / max(total_elz, 1e-9)
    grid_import = float(np.clip(grid, 0.0, None).sum() * STEP_H)
    return frac, grid_import


def hourly_setpoints_of(result):
    """24 hourly setpoints from a result dict (battery results omit the key)."""
    if "hourly_setpoints" in result:
        return np.asarray(result["hourly_setpoints"])
    return np.asarray(result["setpoints"])[::STEPS_PER_HOUR]


# ── the shared dispatch chart ──────────────────────────────────────────────────
def dispatch_figure(result, *, title, y_max=0.92, show_battery=False):
    """Build the dispatch Plotly figure used by Daily Dispatch (and others).

    Traces: tariff bands, available PV, electrolyzer setpoint (step + fill),
    grid (+import/−export), tariff on yaxis2. With show_battery, adds the SOC
    line (yaxis2, scaled) and the battery charge/discharge.
    """
    sp   = np.asarray(result["setpoints"])
    pv   = np.asarray(result["pv_mw"])
    grid = np.asarray(result["grid_p_mw"])

    fig = go.Figure()

    # tariff band shading (behind the traces)
    for x0, x1, color, label in [
        (0.0,  6.0,  _BAND_CREUSES_COLOR, "Creuses (cheap)"),
        (17.0, 21.0, _BAND_POINTE_COLOR,  "Pointe (peak)"),
        (22.5, 24.0, _BAND_CREUSES_COLOR, None),
    ]:
        fig.add_vrect(x0=x0, x1=x1, fillcolor=color, layer="below", line_width=0,
                      annotation_text=label or "", annotation_position="top left",
                      annotation_font_size=10)

    fig.add_trace(go.Scatter(
        x=X_STEPS, y=pv, mode="lines", name="Available solar PV [MW]",
        line=dict(color=COLOR_PV, width=3),
        hovertemplate="%{y:.3f} MW<extra>PV</extra>"))

    fig.add_trace(go.Scatter(
        x=X_STEPS, y=sp, mode="lines", name="Electrolyzer setpoint [MW]",
        line=dict(color=COLOR_SETPOINT, width=3, shape="hv"),
        fill="tozeroy", fillcolor="rgba(29, 78, 216, 0.18)",
        hovertemplate="%{y:.3f} MW<extra>Setpoint</extra>"))

    fig.add_trace(go.Scatter(
        x=X_STEPS, y=grid, mode="lines", name="Grid power [MW]  (+import / −export)",
        line=dict(color=COLOR_GRID, width=2.5, dash="dash"),
        hovertemplate="%{y:.3f} MW<extra>Grid</extra>"))

    if show_battery and "batt_mw" in result:
        batt = np.asarray(result["batt_mw"])      # + discharge / − charge
        soc  = np.asarray(result["soc_mwh"])
        fig.add_trace(go.Scatter(
            x=X_STEPS, y=batt, mode="lines",
            name="Battery power [MW]  (+discharge / −charge)",
            line=dict(color=COLOR_BATTERY, width=2.5),
            hovertemplate="%{y:.3f} MW<extra>Battery</extra>"))
        # SOC scaled onto the (price) right axis range for context
        soc_scaled = soc / max(soc.max(), 1e-9) * 10.0
        fig.add_trace(go.Scatter(
            x=X_STEPS, y=soc_scaled, mode="lines", name="Battery SOC [MWh] (scaled)",
            line=dict(color=COLOR_SOC, width=2, dash="dashdot"), yaxis="y2",
            customdata=soc,
            hovertemplate="%{customdata:.2f} MWh<extra>SOC</extra>"))

    fig.add_trace(go.Scatter(
        x=X_STEPS, y=PRICE_STEPS, mode="lines", name="CREG tariff [DA/kWh]",
        line=dict(color=COLOR_TARIFF, width=2.5, dash="dot"), yaxis="y2",
        hovertemplate="%{y:.4f} DA/kWh<extra>Tariff</extra>"))

    fig.update_layout(
        font=FONT,
        title=dict(text=title, font=dict(size=13, color=BLACK)),
        xaxis=dict(title=dict(text="Hour of day (local time)", font=AXIS_TITLE_FONT),
                   range=[0, 24], tickvals=list(range(0, 25, 2)),
                   tickfont=dict(color=BLACK)),
        yaxis=dict(title=dict(text="Power [MW]", font=AXIS_TITLE_FONT),
                   range=[None, y_max], gridcolor="#e5e7eb",
                   tickfont=dict(color=BLACK)),
        yaxis2=dict(title=dict(text="Tariff [DA/kWh] · SOC (scaled)",
                               font=AXIS_TITLE_FONT),
                    overlaying="y", side="right", range=[0, 10], showgrid=False,
                    tickformat=".2f", tickfont=dict(color=BLACK)),
        legend=LEGEND_STYLE,
        hovermode="x unified", plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        height=460, margin=dict(t=96, b=50))
    return fig
