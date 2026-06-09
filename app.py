import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import warnings
warnings.filterwarnings('ignore')

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Wildfire Risk Intelligence Engine",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0d0d0d 0%, #1a0a00 50%, #0d0d0d 100%);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a0a00 0%, #2d1200 100%);
    }
    [data-testid="stSidebar"] * { color: #ffcc88 !important; }
    h1, h2, h3 { color: #ff6b35 !important; }
    .stMetric { background: rgba(255,107,53,0.1); border: 1px solid #ff6b35;
                border-radius: 10px; padding: 10px; }
    .stMetric label { color: #ffcc88 !important; }
    .stMetric [data-testid="stMetricValue"] { color: #ff4500 !important; font-size: 2rem !important; }
    .stMetric [data-testid="stMetricDelta"] { color: #ffa07a !important; }
    div[data-testid="stTabs"] button { color: #ffcc88 !important; }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #ff6b35 !important; border-bottom: 2px solid #ff6b35;
    }
    .risk-card {
        background: rgba(255,69,0,0.15);
        border: 1px solid rgba(255,107,53,0.4);
        border-radius: 12px;
        padding: 15px;
        margin: 8px 0;
    }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; padding: 20px 0 10px 0;'>
  <h1 style='font-size:2.8rem; color:#ff6b35; letter-spacing:2px;'>
    🔥 Wildfire Risk Intelligence Engine
  </h1>
  <p style='color:#ffcc88; font-size:1.1rem;'>
    NASA FIRMS Satellite Fire Detection · Real-Time Analytics · Global Risk Assessment
  </p>
</div>
<hr style='border-color:#ff6b3566; margin-bottom:20px;'>
""", unsafe_allow_html=True)

# ── Data loading ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data(file):
    df = pd.read_csv(file)
    df['acq_date'] = pd.to_datetime(df['acq_date'], dayfirst=True)
    conf_map = {'h': 'High', 'n': 'Nominal', 'l': 'Low'}
    df['confidence_label'] = df['confidence'].map(conf_map)
    df['intensity_score'] = (
        (df['brightness'] - df['brightness'].min()) /
        (df['brightness'].max() - df['brightness'].min()) * 0.5 +
        (df['frp'] - df['frp'].min()) /
        (df['frp'].max() - df['frp'].min()) * 0.5
    ).round(4)
    return df

# ── File upload gate ──────────────────────────────────────────────────────────
uploaded_file = st.sidebar.file_uploader(
    "📂 Upload your CSV dataset",
    type=["csv"],
    help="Upload your NASA FIRMS wildfire CSV file (e.g. dataset_for_my_project.csv)"
)

if uploaded_file is None:
    st.markdown("""
    <div style='text-align:center; padding: 60px 20px;'>
      <h2 style='color:#ff6b35;'>📂 Upload Your Dataset to Begin</h2>
      <p style='color:#ffcc88; font-size:1.1rem;'>
        Use the <b>sidebar on the left</b> to upload your NASA FIRMS CSV file<br>
        (e.g. <code>dataset_for_my_project.csv</code>)
      </p>
      <br>
      <p style='color:#aaa;'>Expected columns: latitude, longitude, brightness, acq_date,
      acq_time, satellite, confidence, bright_t31, frp, daynight</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

with st.spinner("🔥 Loading wildfire data..."):
    df = load_data(uploaded_file)

df_filtered = df[df['confidence'].isin(['h', 'n'])].copy()

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown("## ⚙️ Filters & Controls")
st.sidebar.markdown("---")

conf_options = st.sidebar.multiselect(
    "🎯 Confidence Level",
    options=["High", "Nominal", "Low"],
    default=["High", "Nominal"]
)

date_min = df['acq_date'].min().date()
date_max = df['acq_date'].max().date()
date_range = st.sidebar.date_input(
    "📅 Date Range",
    value=(date_min, date_max),
    min_value=date_min,
    max_value=date_max
)

daynight = st.sidebar.radio("🌞 Time of Detection", ["All", "Daytime Only", "Nighttime Only"])

frp_min, frp_max = float(df['frp'].min()), float(df['frp'].quantile(0.99))
frp_threshold = st.sidebar.slider("⚡ Minimum FRP (MW)", 0.0, frp_max, 0.0, step=0.5)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='color:#ffaa66; font-size:0.8rem;'>
📡 <b>Data Source:</b> NASA FIRMS (NOAA-20/VIIRS)<br>
📅 <b>Period:</b> May 2026<br>
🌍 <b>Coverage:</b> Global<br>
🔢 <b>Records:</b> {:,}
</div>
""".format(len(df)), unsafe_allow_html=True)

# ── Apply filters ─────────────────────────────────────────────────────────────
conf_code_map = {"High": "h", "Nominal": "n", "Low": "l"}
selected_conf = [conf_code_map[c] for c in conf_options]

dff = df[df['confidence'].isin(selected_conf)].copy()

if len(date_range) == 2:
    dff = dff[(dff['acq_date'].dt.date >= date_range[0]) &
              (dff['acq_date'].dt.date <= date_range[1])]

if daynight == "Daytime Only":
    dff = dff[dff['daynight'] == 'D']
elif daynight == "Nighttime Only":
    dff = dff[dff['daynight'] == 'N']

dff = dff[dff['frp'] >= frp_threshold]

# ── Risk scoring helper ────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def compute_risk(data_json):
    data = pd.read_json(data_json, orient='split')
    data['lat_bin'] = (data['latitude'] // 2) * 2
    data['lon_bin'] = (data['longitude'] // 2) * 2
    rr = data.groupby(['lat_bin', 'lon_bin']).agg(
        fire_count=('frp', 'count'),
        avg_frp=('frp', 'mean'),
        max_frp=('frp', 'max'),
        total_frp=('frp', 'sum'),
        avg_brightness=('brightness', 'mean'),
    ).reset_index()
    rr['risk_score'] = (
        0.4 * (rr['fire_count'] / rr['fire_count'].max()) +
        0.35 * (rr['total_frp'] / rr['total_frp'].max()) +
        0.25 * (rr['avg_brightness'] / rr['avg_brightness'].max())
    ).round(4)
    def classify(s):
        if s >= 0.6:   return '🔴 Extreme'
        elif s >= 0.3: return '🟠 High'
        elif s >= 0.1: return '🟡 Moderate'
        else:          return '🟢 Low'
    rr['risk_tier'] = rr['risk_score'].apply(classify)
    return rr

if dff.empty:
    st.warning("⚠️ No data matches your current filters. Please adjust the sidebar controls.")
    st.stop()

region_risk = compute_risk(dff[['latitude','longitude','frp','brightness']].to_json(orient='split'))

# ── KPI Metrics ────────────────────────────────────────────────────────────────
st.markdown("### 📊 Key Intelligence Metrics")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("🔥 Total Detections", f"{len(dff):,}")
c2.metric("⚡ Mean FRP", f"{dff['frp'].mean():.1f} MW")
c3.metric("🌡️ Peak FRP", f"{dff['frp'].max():.0f} MW")
c4.metric("🗺️ Risk Zones", f"{len(region_risk):,}")
extreme = (region_risk['risk_tier'] == '🔴 Extreme').sum()
c5.metric("🚨 Extreme Zones", f"{extreme:,}")

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ────────────────────────────────────────────────────────────────────────
# ── Global tier colours (used in Tab 4 & 5) ──────────────────────────────────
tier_colors_map = {
    '🔴 Extreme': '#bd0026',
    '🟠 High':    '#f03b20',
    '🟡 Moderate':'#fd8d3c',
    '🟢 Low':     '#fecc5c'
}

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌍 Global Fire Map",
    "📈 Temporal Analysis",
    "📊 EDA Overview",
    "🗺️ Risk Zone Map",
    "🏆 Top Risk Regions"
])

# ── TAB 1: Global Fire Map ─────────────────────────────────────────────────────
with tab1:
    st.markdown("#### 🌍 Live Wildfire Heatmap (Satellite Detections)")

    sample_size = min(60000, len(dff))
    sample = dff.sample(n=sample_size, random_state=42) if len(dff) > sample_size else dff

    heat_data = list(zip(
        sample['latitude'],
        sample['longitude'],
        sample['frp'].clip(upper=sample['frp'].quantile(0.95))
    ))

    m = folium.Map(location=[20, 0], zoom_start=2, tiles='CartoDB dark_matter')
    HeatMap(
        heat_data,
        min_opacity=0.3,
        radius=6, blur=4,
        gradient={0.2: '#ffffb2', 0.5: '#fd8d3c', 0.8: '#f03b20', 1.0: '#bd0026'}
    ).add_to(m)

    top10 = region_risk.sort_values('risk_score', ascending=False).head(10)
    for _, row in top10.iterrows():
        tier_color = {'🔴 Extreme': 'red', '🟠 High': 'orange',
                      '🟡 Moderate': 'yellow', '🟢 Low': 'green'}.get(row['risk_tier'], 'cyan')
        folium.CircleMarker(
            location=[row['lat_bin'] + 1, row['lon_bin'] + 1],
            radius=9, color=tier_color, fill=True,
            fill_color=tier_color, fill_opacity=0.75,
            popup=folium.Popup(
                f"<b>Risk Score: {row['risk_score']:.3f}</b><br>"
                f"Fire Count: {row['fire_count']:,}<br>"
                f"Avg FRP: {row['avg_frp']:.1f} MW<br>"
                f"Max FRP: {row['max_frp']:.1f} MW<br>"
                f"Tier: {row['risk_tier']}",
                max_width=220
            )
        ).add_to(m)

    st_folium(m, width="100%", height=500)
    st.caption(f"📍 Showing {sample_size:,} sampled detections · Top-10 extreme zones marked")

# ── TAB 2: Temporal Analysis ───────────────────────────────────────────────────
with tab2:
    st.markdown("#### 📈 Daily Wildfire Activity Timeline")

    daily = dff.groupby('acq_date').agg(
        fire_count=('frp', 'count'),
        total_frp=('frp', 'sum'),
        mean_frp=('frp', 'mean')
    ).reset_index()

    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    fig.patch.set_facecolor('#0d0d0d')
    for ax in axes:
        ax.set_facecolor('#111111')
        ax.tick_params(colors='#ffcc88')
        ax.spines[:].set_color('#333333')

    axes[0].fill_between(daily['acq_date'], daily['fire_count'], color='orangered', alpha=0.7)
    axes[0].plot(daily['acq_date'], daily['fire_count'], color='#ff4500', lw=1.5)
    axes[0].set_ylabel('Detection Count', color='#ffcc88')
    axes[0].set_title('Daily Fire Detections', color='#ff9955', fontsize=12)

    axes[1].fill_between(daily['acq_date'], daily['total_frp'], color='#FFD700', alpha=0.65)
    axes[1].plot(daily['acq_date'], daily['total_frp'], color='darkorange', lw=1.5)
    axes[1].set_ylabel('Total FRP (MW)', color='#ffcc88')
    axes[1].set_title('Daily Total Fire Radiative Power', color='#ff9955', fontsize=12)

    axes[2].fill_between(daily['acq_date'], daily['mean_frp'], color='#ff6b6b', alpha=0.65)
    axes[2].plot(daily['acq_date'], daily['mean_frp'], color='#ff0000', lw=1.5)
    axes[2].set_ylabel('Mean FRP (MW)', color='#ffcc88')
    axes[2].set_xlabel('Date', color='#ffcc88')
    axes[2].set_title('Daily Average Fire Intensity', color='#ff9955', fontsize=12)

    fig.suptitle('Temporal Wildfire Analysis', color='#ff6b35', fontsize=15, fontweight='bold')
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    # Peak day callout
    peak = daily.loc[daily['fire_count'].idxmax()]
    st.info(f"📌 **Peak detection day:** {peak['acq_date'].date()} — "
            f"{peak['fire_count']:,} fires detected, {peak['total_frp']:,.0f} MW total FRP")

# ── TAB 3: EDA Overview ────────────────────────────────────────────────────────
with tab3:
    st.markdown("#### 📊 Exploratory Data Analysis")

    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.patch.set_facecolor('#0d0d0d')
    for ax in axes.flat:
        ax.set_facecolor('#111111')
        ax.tick_params(colors='#ffcc88')
        ax.spines[:].set_color('#333333')
        ax.xaxis.label.set_color('#ffcc88')
        ax.yaxis.label.set_color('#ffcc88')
        ax.title.set_color('#ff9955')

    # FRP Distribution
    axes[0,0].hist(np.log1p(dff['frp']), bins=60, color='orangered', edgecolor='black', alpha=0.85)
    axes[0,0].set_title('FRP Distribution (log scale)')
    axes[0,0].set_xlabel('log(FRP + 1)')

    # Brightness
    axes[0,1].hist(dff['brightness'], bins=60, color='#FF8C00', edgecolor='black', alpha=0.85)
    axes[0,1].set_title('Brightness Temperature')
    axes[0,1].set_xlabel('Brightness (K)')

    # Confidence
    conf_counts = dff['confidence_label'].value_counts()
    colors_conf = ['#d62728', '#ff7f0e', '#aec7e8'][:len(conf_counts)]
    axes[0,2].bar(conf_counts.index, conf_counts.values, color=colors_conf, edgecolor='black')
    axes[0,2].set_title('Detections by Confidence')
    for i, v in enumerate(conf_counts.values):
        axes[0,2].text(i, v + len(dff)*0.002, f'{v:,}', ha='center', fontsize=8, color='#ffcc88')

    # Day/Night pie
    dn_counts = dff['daynight'].value_counts()
    dn_labels = ['Daytime' if x == 'D' else 'Nighttime' for x in dn_counts.index]
    axes[1,0].pie(dn_counts.values, labels=dn_labels, autopct='%1.1f%%',
                  colors=['#FFD700', '#1a1a2e'], startangle=140,
                  textprops={'color': '#ffcc88'})
    axes[1,0].set_title('Day vs Night Detections')

    # Risk tier distribution
    tier_order = ['🔴 Extreme', '🟠 High', '🟡 Moderate', '🟢 Low']
    tier_colors_map = {'🔴 Extreme': '#bd0026', '🟠 High': '#f03b20',
                       '🟡 Moderate': '#fd8d3c', '🟢 Low': '#fecc5c'}
    tier_vals = [region_risk[region_risk['risk_tier'] == t].shape[0] for t in tier_order]
    axes[1,1].barh(tier_order, tier_vals,
                   color=[tier_colors_map[t] for t in tier_order], edgecolor='black')
    axes[1,1].set_title('Grid Cells by Risk Tier')
    axes[1,1].set_xlabel('Count')

    # FRP vs Brightness scatter (sampled)
    sc_sample = dff.sample(n=min(5000, len(dff)), random_state=0)
    sc = axes[1,2].scatter(sc_sample['brightness'], sc_sample['frp'],
                           c=sc_sample['frp'], cmap='hot', s=3, alpha=0.6,
                           vmin=0, vmax=dff['frp'].quantile(0.95))
    axes[1,2].set_title('Brightness vs FRP')
    axes[1,2].set_xlabel('Brightness (K)')
    axes[1,2].set_ylabel('FRP (MW)')
    fig.colorbar(sc, ax=axes[1,2]).ax.tick_params(colors='#ffcc88')

    fig.suptitle('Wildfire Detection — EDA Overview', color='#ff6b35',
                 fontsize=15, fontweight='bold')
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

# ── TAB 4: Risk Zone Map ─────────────────────────────────────────────────────
with tab4:
    st.markdown("#### 🗺️ Wildfire Risk Tier Map — Grid Cell Assessment")

    fig, ax = plt.subplots(figsize=(18, 9))
    ax.set_facecolor('#0d0d0d')
    fig.patch.set_facecolor('#1a1a2e')

    tier_order = ['🟢 Low', '🟡 Moderate', '🟠 High', '🔴 Extreme']
    for tier in tier_order:
        subset = region_risk[region_risk['risk_tier'] == tier]
        if len(subset) == 0:
            continue
        ax.scatter(
            subset['lon_bin'] + 1, subset['lat_bin'] + 1,
            c=tier_colors_map[tier],
            s=subset['fire_count'] / subset['fire_count'].max() * 30 + 2,
            alpha=0.75,
            label=f'{tier} ({len(subset):,} cells)',
            edgecolors='none'
        )

    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_xlabel('Longitude', color='#ffcc88')
    ax.set_ylabel('Latitude', color='#ffcc88')
    ax.set_title('🔥 Wildfire Risk Tier Map — Global Grid Assessment',
                 color='#ff6b35', fontsize=14, fontweight='bold')
    ax.tick_params(colors='#ffcc88')
    ax.spines[:].set_color('#333333')
    ax.grid(alpha=0.1, color='#555555')
    legend = ax.legend(loc='lower left', framealpha=0.3,
                       labelcolor='white', facecolor='black',
                       edgecolor='#ff6b35', fontsize=9)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    col1, col2, col3, col4 = st.columns(4)
    for col, tier, color in zip(
        [col1, col2, col3, col4],
        ['🔴 Extreme', '🟠 High', '🟡 Moderate', '🟢 Low'],
        ['#bd0026', '#f03b20', '#fd8d3c', '#fecc5c']
    ):
        count = (region_risk['risk_tier'] == tier).sum()
        col.markdown(f"""
        <div class='risk-card' style='border-color:{color}66; background:rgba(255,255,255,0.05);'>
          <h4 style='color:{color}; margin:0;'>{tier}</h4>
          <p style='color:#ffcc88; font-size:1.6rem; margin:5px 0;'><b>{count:,}</b></p>
          <p style='color:#999; margin:0; font-size:0.8rem;'>grid cells</p>
        </div>
        """, unsafe_allow_html=True)

# ── TAB 5: Top Risk Regions ───────────────────────────────────────────────────
with tab5:
    st.markdown("#### 🏆 Top Wildfire-Prone Regions by Risk Score")

    col_n, col_t = st.columns([1, 3])
    with col_n:
        top_n = st.slider("Show top N regions", 5, 50, 20)
    with col_t:
        show_tier = st.selectbox("Filter by tier", ["All", "🔴 Extreme", "🟠 High", "🟡 Moderate", "🟢 Low"])

    display_df = region_risk.copy()
    if show_tier != "All":
        display_df = display_df[display_df['risk_tier'] == show_tier]

    top_regions = display_df.sort_values('risk_score', ascending=False).head(top_n)

    # Bar chart
    fig, ax = plt.subplots(figsize=(14, max(5, top_n * 0.35)))
    fig.patch.set_facecolor('#0d0d0d')
    ax.set_facecolor('#111111')
    ax.tick_params(colors='#ffcc88')
    ax.spines[:].set_color('#333333')

    colors = [tier_colors_map.get(t, '#ff6b35') for t in top_regions['risk_tier']]
    bars = ax.barh(
        [f"({r['lat_bin']:.0f}°, {r['lon_bin']:.0f}°)" for _, r in top_regions.iterrows()],
        top_regions['risk_score'],
        color=colors, edgecolor='black', alpha=0.9
    )
    ax.set_xlabel('Risk Score (0–1)', color='#ffcc88')
    ax.set_title(f'Top {top_n} Wildfire Risk Zones', color='#ff6b35', fontsize=13, fontweight='bold')
    ax.set_xlim(0, 1)
    for bar, val in zip(bars, top_regions['risk_score']):
        ax.text(val + 0.01, bar.get_y() + bar.get_height()/2,
                f'{val:.3f}', va='center', color='#ffcc88', fontsize=8)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    # Table
    st.markdown("##### 📋 Detailed Region Data")
    table_df = top_regions[['lat_bin','lon_bin','fire_count','avg_frp','max_frp','total_frp','risk_score','risk_tier']].copy()
    table_df.columns = ['Lat°', 'Lon°', 'Fire Count', 'Avg FRP (MW)', 'Max FRP (MW)',
                         'Total FRP (MW)', 'Risk Score', 'Risk Tier']
    table_df = table_df.round(2)
    st.dataframe(table_df, use_container_width=True, hide_index=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#ff9933; font-size:0.9rem; padding:10px 0;'>
  🔥 <b>Wildfire Risk Intelligence Engine</b> · Powered by NASA FIRMS Satellite Data ·
  Built with Streamlit & Python
</div>
""", unsafe_allow_html=True)
