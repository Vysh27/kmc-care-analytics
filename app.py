"""
app.py — KMC Care Analytics dashboard
-------------------------------------
A Streamlit dashboard over synthetic Kangaroo Mother Care (KMC) program data.
Turns raw field-app exports into decision-ready views for program and M&E teams:
coverage KPIs, adherence trends, hospital comparison, and a data-quality worklist.

Data is SYNTHETIC and for demonstration only — see README.

Run locally:  streamlit run app.py
"""

from __future__ import annotations
import pandas as pd
import plotly.express as px
import streamlit as st

from pipeline import build

st.set_page_config(page_title="KMC Care Analytics", page_icon="👶", layout="wide")

PRIMARY = "#0F766E"   # teal
ACCENT = "#B45309"    # amber
GREY = "#64748B"


@st.cache_data(show_spinner="Building models from raw data…")
def load_data() -> dict[str, pd.DataFrame]:
    return build()


tables = load_data()
adm = tables["admissions"].copy()
adm["admit_date"] = pd.to_datetime(adm["admit_date"])
adm["admit_month"] = pd.to_datetime(adm["admit_month"])
dq = tables["dq"]

# ---------------------------------------------------------------- sidebar filters
st.sidebar.title("👶 KMC Care Analytics")
st.sidebar.caption("Synthetic demo data · portfolio project")

states = st.sidebar.multiselect(
    "State", sorted(adm["state"].unique()), default=sorted(adm["state"].unique())
)
adm_s = adm[adm["state"].isin(states)] if states else adm

hosp_opts = sorted(adm_s["hospital_name"].unique())
hosps = st.sidebar.multiselect("Hospital", hosp_opts, default=hosp_opts)
adm_s = adm_s[adm_s["hospital_name"].isin(hosps)] if hosps else adm_s

dmin, dmax = adm["admit_date"].min(), adm["admit_date"].max()
dr = st.sidebar.date_input("Admission date range", (dmin, dmax), min_value=dmin, max_value=dmax)
if isinstance(dr, tuple) and len(dr) == 2:
    lo, hi = pd.to_datetime(dr[0]), pd.to_datetime(dr[1])
    adm_s = adm_s[(adm_s["admit_date"] >= lo) & (adm_s["admit_date"] <= hi)]

st.sidebar.markdown("---")
st.sidebar.markdown(
    "Built with **Python · SQL · DuckDB · Streamlit**. "
    "SQL models run live on each load. Code on GitHub."
)

# ------------------------------------------------------------------------- header
st.title("Kangaroo Mother Care — Program Dashboard")
st.caption(
    "Synthetic data demonstrating an end-to-end analytics pipeline: raw app exports → "
    "SQL modeling layer → decision-ready views. Not real patient data."
)

if adm_s.empty:
    st.warning("No records match the current filters.")
    st.stop()

# ------------------------------------------------------------------------- KPIs
n_adm = len(adm_s)
lbw_pct = adm_s["is_lbw"].mean() * 100
avg_kmc = adm_s["avg_kmc_hours_day"].mean()
mortality = adm_s["is_death"].mean() * 100
ebf = adm_s["exclusive_breastfeeding"].mean() * 100

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Admissions", f"{n_adm:,}")
k2.metric("Low birth weight", f"{lbw_pct:.0f}%")
k3.metric("Avg KMC hrs/day", f"{avg_kmc:.1f}")
k4.metric("Mortality", f"{mortality:.1f}%")
k5.metric("Exclusive breastfeeding", f"{ebf:.0f}%")

st.markdown("---")

# --------------------------------------------------------------- trend + mix row
c1, c2 = st.columns([3, 2])

with c1:
    st.subheader("KMC adherence over time")
    monthly = (
        adm_s.groupby("admit_month")
        .agg(avg_kmc=("avg_kmc_hours_day", "mean"), admissions=("admission_id", "count"))
        .reset_index()
    )
    fig = px.line(monthly, x="admit_month", y="avg_kmc", markers=True)
    fig.update_traces(line_color=PRIMARY)
    fig.add_hline(y=8, line_dash="dot", line_color=ACCENT,
                  annotation_text="8h adequacy target", annotation_position="bottom right")
    fig.update_layout(height=330, margin=dict(t=10, b=0, l=0, r=0),
                      yaxis_title="Avg KMC hours / day", xaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Admissions by birth-weight band")
    bands = pd.cut(
        adm_s["birth_weight_g"],
        bins=[0, 1000, 1500, 2000, 2500, 10000],
        labels=["<1000 (ELBW)", "1000–1499 (VLBW)", "1500–1999", "2000–2499 (LBW)", "≥2500"],
    )
    band_df = bands.value_counts().sort_index().reset_index()
    band_df.columns = ["band", "count"]
    fig2 = px.bar(band_df, x="count", y="band", orientation="h")
    fig2.update_traces(marker_color=PRIMARY)
    fig2.update_layout(height=330, margin=dict(t=10, b=0, l=0, r=0),
                       xaxis_title="Admissions", yaxis_title=None)
    st.plotly_chart(fig2, use_container_width=True)

# ----------------------------------------------------------- hospital comparison
st.subheader("Hospital comparison")
by_hosp = (
    adm_s.groupby(["hospital_name", "state"])
    .agg(
        admissions=("admission_id", "count"),
        avg_kmc=("avg_kmc_hours_day", "mean"),
        mortality=("is_death", "mean"),
        lbw=("is_lbw", "mean"),
    )
    .reset_index()
    .sort_values("avg_kmc", ascending=False)
)
by_hosp["mortality"] = (by_hosp["mortality"] * 100).round(1)
by_hosp["lbw"] = (by_hosp["lbw"] * 100).round(0)
by_hosp["avg_kmc"] = by_hosp["avg_kmc"].round(1)

cc1, cc2 = st.columns([2, 3])
with cc1:
    st.dataframe(
        by_hosp.rename(columns={
            "hospital_name": "Hospital", "state": "State", "admissions": "Admissions",
            "avg_kmc": "Avg KMC hrs/day", "mortality": "Mortality %", "lbw": "LBW %",
        }),
        hide_index=True, use_container_width=True, height=380,
    )
with cc2:
    st.caption("Does more KMC track with lower mortality? (each point = one hospital)")
    fig3 = px.scatter(
        by_hosp, x="avg_kmc", y="mortality", size="admissions", color="state",
        hover_name="hospital_name", color_discrete_sequence=[PRIMARY, ACCENT],
        trendline="ols" if len(by_hosp) > 2 else None,
    )
    fig3.update_layout(height=380, margin=dict(t=10, b=0, l=0, r=0),
                       xaxis_title="Avg KMC hours / day", yaxis_title="Mortality %",
                       legend_title=None)
    st.plotly_chart(fig3, use_container_width=True)

# --------------------------------------------------------------- data quality
st.markdown("---")
st.subheader("🩺 Data quality worklist")
st.caption(
    "Issues caught by the pipeline before numbers reach leadership or partners. "
    "Filtered to the hospitals selected in the sidebar."
)
sel_hosp_ids = set(adm_s["hospital_id"].unique())
dq_f = dq[dq["hospital_id"].isin(sel_hosp_ids)]

q1, q2, q3 = st.columns(3)
q1.metric("Flagged records", f"{len(dq_f):,}")
q2.metric("Issue types", dq_f["issue"].nunique() if len(dq_f) else 0)
q3.metric("Hospitals affected", dq_f["hospital_id"].nunique() if len(dq_f) else 0)

if len(dq_f):
    summary = dq_f["issue"].value_counts().reset_index()
    summary.columns = ["Issue", "Count"]
    left, right = st.columns([1, 2])
    with left:
        st.dataframe(summary, hide_index=True, use_container_width=True)
    with right:
        st.dataframe(dq_f.head(200), hide_index=True, use_container_width=True, height=260)
else:
    st.success("No data-quality issues for the current selection.")

st.markdown("---")
st.caption(
    "Portfolio project · synthetic data · Python + SQL (BigQuery-portable) + DuckDB + Streamlit"
)
