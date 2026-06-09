# 🔥 Wildfire Risk Intelligence Engine

A Streamlit analytical platform built on NASA FIRMS satellite fire detection data.

## 📁 Files Required
- `app.py` — main Streamlit app
- `dataset_for_my_project.csv` — your wildfire dataset
- `requirements.txt` — Python dependencies

## 🚀 Deploy on Streamlit Community Cloud (Free)

### Step 1 — Push to GitHub
1. Create a new **public** GitHub repository (e.g. `wildfire-risk-intelligence`)
2. Upload these three files:
   - `app.py`
   - `requirements.txt`
   - `dataset_for_my_project.csv`

### Step 2 — Deploy on Streamlit Cloud
1. Go to **https://share.streamlit.io** and sign in with GitHub
2. Click **"New app"**
3. Select your repository, branch (`main`), and set Main file path to `app.py`
4. Click **Deploy!**
5. Wait ~2–3 minutes — your live URL will be something like:
   `https://wildfire-risk-intelligence-engine-xxxxx.streamlit.app`

## 🖥️ Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 📊 Features
- 🌍 **Global Fire Heatmap** — interactive Folium map with FRP intensity
- 📈 **Temporal Analysis** — daily detection counts and FRP trends
- 📊 **EDA Overview** — distribution plots, day/night breakdown, confidence levels
- 🗺️ **Risk Zone Map** — grid-cell risk scoring (Extreme / High / Moderate / Low)
- 🏆 **Top Risk Regions** — ranked table and bar chart of highest-risk zones
- ⚙️ **Sidebar Filters** — filter by confidence, date range, day/night, FRP threshold

## 📌 Notes
- Dataset: 1M+ records from NASA FIRMS (NOAA-20/VIIRS), May 2026
- Risk scoring uses fire count (40%), total FRP (35%), brightness temperature (25%)
