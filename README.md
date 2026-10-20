# 🚀 StarbaseV — Spaceport Site Selector for Malaysia

<div align="center">

**Interactive spaceport site analysis for Borneo & West Malaysia**  
Powered by real-time OSM data, live weather, and orbital physics.

[![Streamlit App](https://img.shields.io/badge/🚀%20LIVE%20APP-starbasev.streamlit.app-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://starbasev.streamlit.app)
[![GitHub](https://img.shields.io/badge/GitHub-Source%20Code-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/YOUR_USERNAME/starbasev)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-39ff14?style=for-the-badge)](LICENSE)
[![Made in Malaysia](https://img.shields.io/badge/Made%20in-🇲🇾%20Malaysia-CC0001?style=for-the-badge)](https://malaysia.gov.my)

[![Buy Me A Coffee](https://img.shields.io/badge/☕%20Buy%20Me%20A%20Coffee-stargazex-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/stargazex)


</div>

---
<a href="https://buymeacoffee.com/stargazex" target="_blank"> <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" > </a>

## 🌏 What is StarbaseV?

**StarbaseV** is a free, open-source web application that evaluates potential **spaceport launch sites** across **Malaysia** — both **Borneo** (Sabah & Sarawak) and **West Malaysia** (Peninsular).

It scores **450+ locations** using a weighted multi-criteria model that combines:

| Icon | Data Source | What It Provides |
|------|-------------|------------------|
| 🗺️ | **Geographic rules** | Elevation, coastal proximity, land use |
| 🌐 | **OpenStreetMap (live)** | Airports, settlements, roads, coastlines |
| 🌤️ | **Open-Meteo (live)** | Wind speed, gusts, temperature, humidity |
| 📡 | **Open-Elevation (live)** | Real elevation at the exact coordinate |

Every analysis completes in **seconds** — with a full reasoning log, downloadable report, and detailed recommendation strategy.

**No API keys. No sign-up. No ads. Just open the link and use it.**
<a href="https://buymeacoffee.com/stargazex" target="_blank"> <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" > </a>

---

## ✨ Features

| Icon | Feature |
|------|---------|
| 🚀 | **Spaceport suitability scoring** — weighted 8-criteria model |
| 🌊 | **Launch corridor overlay** — azimuth, direction, safety notes on the map |
| 🔥 | **Heatmap layer** — visualize candidate scores across the region |
| ⭐ | **Save favorites** — persist your best sites |
| 📤 | **Download reports** — TXT / CSV / JSON formats |
| 🚀 | **Payload / Delta-V calculator** — physics-based LEO & GTO estimates |
| 📅 | **30-day wind history** — from Open-Meteo Archive API |
| 🔍 | **Search any location** — by address or `lat,lon` coordinates |
| 🛰️ | **Satellite / OSM basemap toggle** |
| 🧠 | **Chain-of-thought reasoning** — see how the agent reached its conclusion |
| 💾 | **Memory system** — agent learns from past analyses |
| 🔄 | **Compare all sites** — leaderboard across 120+ candidate sites |
| 🎯 | **Detailed recommendation strategy** — immediate / short / long-term actions with cost estimates |

---

## 🎯 How the scoring works

Each site is scored across **8 weighted criteria**:

| Criterion | Weight | What it measures |
|-----------|--------|------------------|
| **Elevation** | 15% | Higher = better (up to ~500m), live API data |
| **Population Density** | 18% | Lower = safer (fewer evacuation concerns) |
| **Coastal Proximity** | 13% | Closer to coast = easier heavy equipment transport |
| **Infrastructure Access** | 13% | Airports, roads, ports, power |
| **Land Availability** | 13% | Forest vs. developed area balance |
| **Flood Risk** | 10% | Derived from elevation |
| **Latitudinal Advantage** | 8% | Lower latitude = more Earth-rotation boost |
| **Wind Conditions** | 10% | Calmer = better for launches |

**Final score** = weighted sum, minus penalties for critical issues (low elevation, high flood risk, dense population, etc.).
 ☕ If StarbaseV helped you, consider [buying me a coffee](https://buymeacoffee.com/stargazex) — it keeps the app free and ad-free.
 <a href="https://www.buymeacoffee.com/stargazex" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" 
       alt="Buy Me A Coffee" 
       height="41" 
       width="174">
### Rating bands

- 🚀 **Excellent** (80–100%) — Highly recommended
- 👍 **Good** (65–79%) — Suitable with minor prep
- 👌 **Moderate** (50–64%) — Significant investment required
- ⚠️ **Limited** (35–49%) — Marginal, major investment
- ❌ **Poor** (0–34%) — Not recommended
 ☕ If StarbaseV helped you, consider [buying me a coffee](https://buymeacoffee.com/stargazex) — it keeps the app free and ad-free.
 <a href="https://www.buymeacoffee.com/stargazex" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" 
       alt="Buy Me A Coffee" 
       height="41" 
       width="174">
