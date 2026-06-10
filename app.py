import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

# ─── Page Setup ───────────────────────────
st.set_page_config(
    page_title="Fire Detection Intelligence Engine",
    page_icon="🔥",
    layout="wide"
)

st.title("🔥 Fire Detection Intelligence Engine")
st.markdown("**Dataset:** NASA VIIRS SNPP Fire Archive | **Stack:** Pandas · NumPy · Matplotlib")
st.markdown("---")


# ─── Load Data ────────────────────────────
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    df["acq_date"] = pd.to_datetime(df["acq_date"], format="%Y-%m-%d", errors="coerce")
    return df


# ─── Sidebar: Upload ──────────────────────
st.sidebar.header("📁 Upload Fire CSV")
uploaded_file = st.sidebar.file_uploader("Choose a VIIRS/MODIS fire CSV", type=["csv"])

if uploaded_file is None:
    default_path = "fire_archive_SV-C2_761163.csv"
    if os.path.exists(default_path):
        df = load_data(default_path)
        st.info(f"Loaded default file: `{default_path}`")
    else:
        st.markdown("""
        ## 👋 Welcome!

        This dashboard analyses **NASA VIIRS SNPP fire detection data**.

        ### To get started:
        1. **Upload a fire archive CSV** using the sidebar on the left ←
        2. The CSV should be a VIIRS or MODIS fire archive from [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/download/)

        ### Expected columns:
        `latitude`, `longitude`, `brightness`, `frp`, `acq_date`, `confidence`, `daynight`

        ---
        Once you upload a file, all charts and filters will appear automatically.
        """)
        st.stop()
else:
    df = load_data(uploaded_file)
    st.success(f"Loaded: `{uploaded_file.name}` — {df.shape[0]:,} fire detections")

pdf = df.copy()

# ─── Sidebar Filters ──────────────────────
st.sidebar.markdown("---")
st.sidebar.header("🔧 Filters")

conf_options = sorted(pdf["confidence"].dropna().unique().tolist())
conf_map = {"n": "Nominal", "l": "Low", "h": "High"}
selected_conf = st.sidebar.multiselect(
    "Confidence Level",
    options=conf_options,
    default=conf_options,
    format_func=lambda x: conf_map.get(str(x), str(x))
)

daynight_options = pdf["daynight"].dropna().unique().tolist()
selected_dn = st.sidebar.multiselect(
    "Day / Night",
    options=daynight_options,
    default=daynight_options,
    format_func=lambda x: "☀️ Day" if x == "D" else "🌙 Night"
)

min_frp = float(pdf["frp"].min())
max_frp = float(pdf["frp"].max())
frp_range = st.sidebar.slider(
    "Fire Radiative Power (FRP) Range (MW)",
    min_value=min_frp,
    max_value=min(500.0, max_frp),
    value=(min_frp, min(500.0, max_frp))
)

filtered = pdf[
    (pdf["confidence"].isin(selected_conf)) &
    (pdf["daynight"].isin(selected_dn)) &
    (pdf["frp"] >= frp_range[0]) &
    (pdf["frp"] <= frp_range[1])
].copy()

if len(filtered) == 0:
    st.warning("No data matches the current filters. Please adjust your selections.")
    st.stop()

# ─── Metric Cards ─────────────────────────
st.subheader("📊 Dataset Overview")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Detections", f"{len(filtered):,}")
col2.metric("Date Range", f"{pdf['acq_date'].dt.year.min()} – {pdf['acq_date'].dt.year.max()}")
col3.metric("Avg Brightness (K)", f"{filtered['brightness'].mean():.1f}")
col4.metric("Avg FRP (MW)", f"{filtered['frp'].mean():.2f}")
col5.metric("Max FRP (MW)", f"{filtered['frp'].max():.1f}")
st.markdown("---")

# ─── Charts Row 1 ─────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("📅 Fire Detections Over Time")
    monthly = filtered.set_index("acq_date").resample("M").size().reset_index()
    monthly.columns = ["month", "count"]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(monthly["month"], monthly["count"], color="orangered", width=20)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45, ha="right")
    ax.set_ylabel("Number of Detections")
    ax.set_title("Monthly Fire Detection Count")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

with col2:
    st.subheader("🌡️ Brightness Temperature Distribution")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(filtered["brightness"], bins=60, color="firebrick", edgecolor="white", alpha=0.85)
    ax.axvline(filtered["brightness"].mean(), color="gold", linestyle="--", linewidth=2,
               label=f"Mean: {filtered['brightness'].mean():.1f} K")
    ax.set_xlabel("Brightness Temperature (K)")
    ax.set_ylabel("Frequency")
    ax.set_title("Brightness Temperature Distribution")
    ax.legend()
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

st.markdown("---")

# ─── Charts Row 2 ─────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("☀️🌙 Day vs Night Fire Detections")
    dn_counts = filtered["daynight"].value_counts()
    labels = ["☀️ Day" if x == "D" else "🌙 Night" for x in dn_counts.index]
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.pie(dn_counts.values, labels=labels, autopct="%1.1f%%",
           colors=["#FFB347", "#4169E1"], startangle=90, pctdistance=0.75)
    ax.set_title("Day vs Night Detections")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

with col2:
    st.subheader("📶 Confidence Level Breakdown")
    conf_counts = filtered["confidence"].map(conf_map).value_counts()
    colors = {"High": "#2ecc71", "Nominal": "#f39c12", "Low": "#e74c3c"}
    bar_colors = [colors.get(c, "steelblue") for c in conf_counts.index]
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.bar(conf_counts.index, conf_counts.values, color=bar_colors, edgecolor="white")
    ax.set_ylabel("Count")
    ax.set_title("Fire Detection Confidence Levels")
    for i, v in enumerate(conf_counts.values):
        ax.text(i, v + max(conf_counts.values) * 0.01, f"{v:,}", ha="center", fontsize=9)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

st.markdown("---")

# ─── Charts Row 3 ─────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("⚡ Fire Radiative Power (FRP) Distribution")
    fig, ax = plt.subplots(figsize=(8, 5))
    data = filtered[filtered["frp"] <= 100]["frp"]
    ax.hist(data, bins=60, color="darkorange", edgecolor="white", alpha=0.85)
    ax.set_xlabel("FRP (MW) — clipped at 100 MW for clarity")
    ax.set_ylabel("Frequency")
    ax.set_title("Fire Radiative Power Distribution")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

with col2:
    st.subheader("🗺️ Geographic Spread (Lat vs Lon)")
    sample = filtered.sample(min(10000, len(filtered)), random_state=42)
    fig, ax = plt.subplots(figsize=(8, 5))
    sc = ax.scatter(
        sample["longitude"], sample["latitude"],
        c=sample["brightness"], cmap="hot", s=2, alpha=0.5
    )
    plt.colorbar(sc, ax=ax, label="Brightness (K)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Fire Hotspot Map (colored by Brightness)")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

st.markdown("---")

# ─── Top Hotspot Regions ──────────────────
st.subheader("🏆 Top Hotspot Grid Cells (Binned by 1° Grid)")
heatmap_df = filtered.copy()
heatmap_df["lat_bin"] = heatmap_df["latitude"].round(0)
heatmap_df["lon_bin"] = heatmap_df["longitude"].round(0)
top_cells = (
    heatmap_df.groupby(["lat_bin", "lon_bin"])
    .agg(detections=("frp", "count"), avg_frp=("frp", "mean"), max_frp=("frp", "max"))
    .reset_index()
    .sort_values("detections", ascending=False)
    .head(20)
    .reset_index(drop=True)
)
top_cells.index += 1
top_cells.columns = ["Lat (°)", "Lon (°)", "Detections", "Avg FRP (MW)", "Max FRP (MW)"]
top_cells["Avg FRP (MW)"] = top_cells["Avg FRP (MW)"].round(2)
top_cells["Max FRP (MW)"] = top_cells["Max FRP (MW)"].round(2)
st.dataframe(top_cells, use_container_width=True)

st.markdown("---")

# ─── Raw Data Preview ─────────────────────
with st.expander("🔍 Raw Data Preview"):
    n = st.slider("Rows to preview", 10, 200, 50)
    st.dataframe(filtered.head(n), use_container_width=True)

st.markdown("---")

# ─── Download ─────────────────────────────
st.subheader("⬇️ Download Filtered Data")
csv_out = filtered.to_csv(index=False)
st.download_button(
    label="Download filtered_fire_data.csv",
    data=csv_out,
    file_name="filtered_fire_data.csv",
    mime="text/csv"
)

st.markdown("---")
st.markdown("**Project:** Fire Detection Intelligence Engine | **Dataset:** NASA VIIRS SNPP | **Stack:** Pandas · NumPy · Matplotlib")
