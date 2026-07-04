"""Tab 3 — Annual Performance (precomputed full-year 2023).

Reads results/tables/annual_2023.csv (the 364-day least-cost run at the fixed
daily demand) and shows year KPIs, a calendar heatmap of cost/kg, and the monthly
cost / solar-fraction pattern. No live compute — instant and demo-safe.
"""

import calendar

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app._shared import AXIS_TITLE_FONT, BLACK, FONT, LEGEND_STYLE, read_table
from app._theme import section


def render():
    section("Annual Performance",
            "Full-year 2023 least-cost dispatch on real PV at a fixed daily demand — "
            "the seasonal cost and solar-fraction pattern across all 364 days.")

    df = read_table("results/tables/annual_2023.csv")
    if df is None:
        st.error("results/tables/annual_2023.csv not found — run "
                 "`python -m scripts.run_annual` to generate it.")
        return

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    daily_demand = float(df["h2_kg"].median())   # fixed demand the run used
    st.caption(f"Full-year least-cost dispatch at a fixed **{daily_demand:.0f} kg/day** "
               f"H₂ demand · real Ghardaïa 2023 PV · CREG time-of-use tariff.")

    # ── year KPIs (computed from the CSV) ───────────────────────────────────────
    total_h2_t   = df["h2_kg"].sum() / 1000.0
    total_cost_m = df["cost_da"].sum() / 1e6
    avg_cost_kg  = df["cost_da"].sum() / max(df["h2_kg"].sum(), 1e-9)
    solar_frac   = 100.0 * df["solar_to_elz_mwh"].sum() / max(
        (df["solar_to_elz_mwh"] + df["grid_import_mwh"]).sum(), 1e-9)
    days_met     = int(df["demand_met"].sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("H₂ produced", f"{total_h2_t:.1f} t/yr")
    c2.metric("Total grid cost", f"{total_cost_m:.2f} M DA")
    c3.metric("Avg cost/kg", f"{avg_cost_kg:.1f} DA/kg")
    c4.metric("Solar fraction", f"{solar_frac:.0f} %")
    c5.metric("Demand met", f"{days_met}/{len(df)} days")

    # ── calendar heatmap of cost/kg ─────────────────────────────────────────────
    df["month"] = df["date"].dt.month
    df["dom"]   = df["date"].dt.day
    grid = np.full((12, 31), np.nan)
    for _, r in df.iterrows():
        grid[int(r["month"]) - 1, int(r["dom"]) - 1] = r["cost_per_kg_da"]

    heat = go.Figure(go.Heatmap(
        z=grid, x=list(range(1, 32)),
        y=[calendar.month_abbr[m] for m in range(1, 13)],
        colorscale="RdYlGn_r",
        colorbar=dict(title=dict(text="DA/kg", font=dict(color=BLACK)),
                      tickfont=dict(color=BLACK)),
        hovertemplate="%{y} %{x}: %{z:.1f} DA/kg<extra></extra>"))
    heat.update_layout(
        font=FONT,
        title=dict(text="Daily least-cost hydrogen [DA/kg] — cheap green summers, "
                        "dear winters", font=dict(size=13, color=BLACK)),
        xaxis=dict(title=dict(text="Day of month", font=AXIS_TITLE_FONT), dtick=2,
                   tickfont=dict(color=BLACK)),
        yaxis=dict(autorange="reversed", tickfont=dict(color=BLACK)),
        height=360, margin=dict(t=60, b=40), paper_bgcolor="#ffffff")
    st.plotly_chart(heat, use_container_width=True)

    # ── monthly cost / solar fraction ───────────────────────────────────────────
    g = df.groupby("month")
    m_cost = g.apply(lambda x: x["cost_da"].sum() / max(x["h2_kg"].sum(), 1e-9),
                     include_groups=False)
    m_solar = g.apply(lambda x: 100.0 * x["solar_to_elz_mwh"].sum() / max(
        (x["solar_to_elz_mwh"] + x["grid_import_mwh"]).sum(), 1e-9),
        include_groups=False)
    months = [calendar.month_abbr[m] for m in m_cost.index]

    bars = go.Figure()
    bars.add_trace(go.Bar(x=months, y=m_cost.to_numpy(),
                          name="Average cost [DA/kg]  (left axis)",
                          marker_color="#1d4ed8",
                          hovertemplate="%{y:.1f} DA/kg<extra></extra>"))
    bars.add_trace(go.Scatter(x=months, y=m_solar.to_numpy(),
                              name="Solar fraction [%]  (right axis)",
                              yaxis="y2", mode="lines+markers",
                              line=dict(color="#15803d", width=3),
                              marker=dict(size=8),
                              hovertemplate="%{y:.0f}%<extra></extra>"))
    bars.update_layout(
        font=FONT,
        title=dict(text="Monthly cost and solar fraction",
                   font=dict(size=13, color=BLACK)),
        xaxis=dict(title=dict(text="Month", font=AXIS_TITLE_FONT),
                   tickfont=dict(color=BLACK)),
        yaxis=dict(title=dict(text="Average cost [DA/kg]", font=AXIS_TITLE_FONT),
                   gridcolor="#e5e7eb", tickfont=dict(color=BLACK)),
        yaxis2=dict(title=dict(text="Solar fraction [%]", font=AXIS_TITLE_FONT),
                    overlaying="y", side="right", range=[0, 100], showgrid=False,
                    tickfont=dict(color=BLACK)),
        legend=LEGEND_STYLE,
        hovermode="x unified", plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        height=380, margin=dict(t=80, b=40))
    st.plotly_chart(bars, use_container_width=True)
