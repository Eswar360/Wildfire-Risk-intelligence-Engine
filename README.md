# 🔥 Wildfire Risk Intelligence Engine

A Streamlit dashboard for analyzing NASA VIIRS satellite fire detection data. Upload any VIIRS/MODIS fire archive CSV and get instant visual intelligence on fire hotspots, brightness temperatures, radiative power, and temporal trends.

---

## 📸 Dashboard Features

| Feature | Description |
|---|---|
| 📊 Overview Metrics | Total detections, date range, avg & max brightness, avg & max FRP |
| 📅 Monthly Trend | Bar chart of fire detections aggregated by month |
| 🌡️ Brightness Distribution | Histogram of brightness temperatures with mean marker |
| ☀️🌙 Day vs Night | Pie chart of daytime vs nighttime detections |
| 📶 Confidence Levels | Bar chart of High / Nominal / Low confidence fire detections |
| ⚡ FRP Distribution | Histogram of Fire Radiative Power (MW) |
| 🗺️ Hotspot Map | Geographic scatter plot colored by brightness temperature |
| 🏆 Top Hotspot Cells | Table of top 20 most active 1° grid cells |
| 🔍 Raw Data Preview | Paginated preview with adjustable row count |
| ⬇️ Download | Export the filtered dataset as CSV |

---

## 🗂️ Dataset

This project is built for the **NASA VIIRS SNPP Fire Archive** (SV-C2 product).

**Columns used:**

| Column | Description |
|---|---|
| `latitude` / `longitude` | Fire detection location |
| `brightness` | Brightness temperature (Kelvin) at band I-4 |
| `frp` | Fire Radiative Power (Megawatts) |
| `acq_date` | Acquisition date |
| `acq_time` | Acquisition time (UTC HHMM) |
| `satellite` | Satellite name (e.g., SNPP) |
| `confidence` | Detection confidence: `h` = High, `n` = Nominal, `l` = Low |
| `daynight` | `D` = Daytime, `N` = Nighttime overpass |
| `bright_t31` | Brightness temperature at band I-5 (Kelvin) |

Download fire archive data from: https://firms.modaps.eosdis.nasa.gov/download/

---

## 🚀 Getting Started

### 1. Clone / download the project

```bash
git clone https://github.com/your-username/fire-detection-intelligence-engine.git
cd fire-detection-intelligence-engine
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501` in your browser.

### 4. Load your data

- Upload a VIIRS/MODIS fire CSV using the **sidebar uploader**, OR
- Place your CSV in the project folder named `fire_archive_SV-C2_761163.csv` and it loads automatically.

---

## 📦 Project Structure

```
fire-detection-intelligence-engine/
│
├── app.py                        # Main Streamlit application
├── requirements.txt              # Python dependencies
├── README.md                     # This file
└── fire_archive_SV-C2_761163.csv # (Optional) default data file
```

---

## 🛠️ Tech Stack

| Library | Purpose |
|---|---|
| [Streamlit](https://streamlit.io) | Web dashboard framework |
| [Polars](https://pola.rs) | Fast CSV loading & lazy computation |
| [Pandas](https://pandas.pydata.org) | Data wrangling, resampling, filtering |
| [NumPy](https://numpy.org) | Numerical operations |
| [Matplotlib](https://matplotlib.org) | Charts and geographic scatter plots |

---

## 🔧 Sidebar Filters

The dashboard includes interactive sidebar filters to slice the data:

- **Confidence Level** — filter by High / Nominal / Low detection confidence
- **Day / Night** — show only daytime or nighttime fire detections
- **FRP Range** — slider to focus on fires within a specific power range (MW)

All charts and metrics update dynamically based on your filter selections.

---

## 📊 Sample Insights (2024 Dataset)

- **552,312** total fire detections recorded in 2024
- **71.6%** daytime detections vs **28.4%** nighttime
- Average brightness temperature: **331.5 K**
- Average FRP: **6.1 MW** | Max FRP: **1,552.8 MW**
- Satellite: SNPP (Suomi National Polar-orbiting Partnership)

---

## 🤝 Acknowledgements

- Fire data sourced from [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/) (Fire Information for Resource Management System)
- VIIRS instrument operated by NASA / NOAA

---

## 📄 License

MIT License — free to use, modify, and distribute.
