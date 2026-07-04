"""Tab 5 — Validation & Plant.

The credibility gate: pandapower reproduces the ETAP base case within tolerance
(every downstream result rests on this). Renders the 24-check validation table,
previews the network load-flow figures, and links out to the standalone three.js
3D digital twin (kept separate so its relative asset paths keep working).
"""

from pathlib import Path

import streamlit as st

from app._shared import REPO_ROOT, read_table
from app._theme import section


def render():
    section("Validation & Plant",
            "The credibility gate: pandapower reproduces the ETAP base case within "
            "tolerance, so every dispatch result is trustworthy — plus the 3D twin.")

    # ── ETAP ↔ pandapower validation ────────────────────────────────────────────
    st.markdown("**ETAP ↔ pandapower base-case validation**")
    df = read_table("results/tables/validation_pandapower_vs_etap.csv")
    if df is None:
        st.error("results/tables/validation_pandapower_vs_etap.csv not found.")
    else:
        n_pass = int((df["status"] == "PASS").sum())
        n_total = len(df)
        if n_pass == n_total:
            st.success(f"{n_pass}/{n_total} checks PASS — pandapower reproduces the "
                       "ETAP base case within ±0.01 pu (voltage) / 2 % (loading, "
                       "flows). Every dispatch result rests on this gate.")
        else:
            st.warning(f"{n_pass}/{n_total} checks PASS — review the failures below.")
        st.dataframe(df, use_container_width=True, height=320)

    st.divider()

    # ── network load-flow figures ───────────────────────────────────────────────
    st.markdown("**Network load-flow cases (pandapower)**")
    figs = [("results/figures/net_sunny.png",     "Sunny"),
            ("results/figures/net_night.png",     "Night"),
            ("results/figures/net_pv_export.png", "PV export (reverse flow)")]
    cols = st.columns(3)
    for col, (rel, caption) in zip(cols, figs):
        path = REPO_ROOT / rel
        if path.exists():
            col.image(str(path), caption=caption, use_container_width=True)
        else:
            col.caption(f"_(missing: {rel})_")

    st.divider()

    # ── 3D digital twin (link out) ──────────────────────────────────────────────
    st.markdown("**3D digital twin**")
    twin = REPO_ROOT / "app" / "plant_3d" / "index.html"
    if twin.exists():
        st.write("An ETAP-style interactive 3D view of the plant driven by the real "
                 "per-timestep load-flow state. Served separately to keep its "
                 "three.js asset paths intact:")
        st.code("cd app/plant_3d && python -m http.server 8001\n"
                "# then open http://localhost:8001", language="bash")
        st.link_button("Open 3D twin (if already served) ↗",
                       "http://localhost:8001")
    else:
        st.caption("_(app/plant_3d/index.html not found)_")
