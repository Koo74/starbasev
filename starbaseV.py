"""
StarbaseV - Complete Combined Single-Page Website
=====================================================
Combines Borneo (Sabah & Sarawak) + West Malaysia (Peninsular) site selection.
All features preserved:
  - 🏝️ Launch Corridor Overlay
  - 🗺️ Heatmap Layer on Comparison Map
  - ⭐ Save / Favorite Sites
  - 📤 Download Report (JSON / CSV / TXT)
  - 🚀 Payload / Delta-V Calculator
  - 📅 30-Day Historical Wind Chart
  - 🔍 Search Bar (address or coordinates)
"""

from __future__ import annotations

import streamlit as st
import folium
from folium.plugins import Fullscreen, MiniMap, MousePosition, Draw, HeatMap
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
from functools import wraps
import requests
from pathlib import Path
import sqlite3
import pickle
import math
import threading
import queue
from io import StringIO, BytesIO

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="StarbaseV",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# SESSION STATE - REGION ROUTING
# ============================================================================

if 'active_region' not in st.session_state:
    st.session_state.active_region = "borneo"

# ============================================================================
# CYBERPUNK STYLING
# ============================================================================

CYBERPUNK_CSS = """
<style>
    :root {
        --neon-cyan: #00f0ff;
        --neon-pink: #ff2d95;
        --neon-purple: #b026ff;
        --neon-green: #39ff14;
        --neon-yellow: #ffe84d;
        --dark-bg: #0a0a0f;
        --card-bg: rgba(15, 15, 35, 0.92);
        --text-white: #ffffff;
    }
    .stApp {
        background: linear-gradient(135deg, #0a0a0f 0%, #1a0a2e 50%, #0a0a1f 100%);
    }
    .main-title {
        font-family: 'Courier New', monospace;
        font-size: 3.5rem;
        font-weight: 900;
        background: linear-gradient(90deg, #00f0ff, #b026ff, #ff2d95);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 40px rgba(0, 240, 255, 0.3);
        letter-spacing: 4px;
        animation: glowPulse 3s ease-in-out infinite;
    }
    @keyframes glowPulse {
        0%, 100% { text-shadow: 0 0 40px rgba(0, 240, 255, 0.3); }
        50% { text-shadow: 0 0 60px rgba(0, 240, 255, 0.6), 0 0 80px rgba(176, 38, 255, 0.3); }
    }
    .subtitle {
        font-family: 'Courier New', monospace;
        color: #00f0ff;
        font-size: 1.2rem;
        letter-spacing: 8px;
        text-shadow: 0 0 20px rgba(0, 240, 255, 0.3);
        border-bottom: 1px solid rgba(0, 240, 255, 0.2);
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .css-1d391kg, .css-1633s9g {
        background: rgba(10, 10, 20, 0.95) !important;
        border-right: 1px solid rgba(0, 240, 255, 0.2) !important;
        backdrop-filter: blur(10px);
    }
    .css-1d391kg p, .css-1633s9g p,
    .css-1d391kg label, .css-1633s9g label,
    .css-1d391kg div, .css-1633s9g div,
    .css-1d391kg span, .css-1633s9g span {
        color: #ffffff !important;
        font-weight: 400 !important;
    }
    .recommendation-container {
        background: rgba(15, 15, 35, 0.85);
        border: 1px solid rgba(0, 240, 255, 0.2);
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 0 30px rgba(0, 240, 255, 0.05);
        transition: all 0.3s ease;
    }
    .recommendation-container:hover {
        border-color: #00f0ff;
        box-shadow: 0 0 40px rgba(0, 240, 255, 0.15);
        transform: translateY(-2px);
    }
    .recommendation-title {
        color: #00f0ff;
        font-family: 'Courier New', monospace;
        font-size: 1.2rem;
        font-weight: bold;
        letter-spacing: 2px;
        margin-bottom: 10px;
        text-shadow: 0 0 20px rgba(0, 240, 255, 0.3);
    }
    .recommendation-item {
        color: #ffffff;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        padding: 6px 0;
        border-bottom: 1px solid rgba(0, 240, 255, 0.05);
        line-height: 1.6;
    }
    .recommendation-item:last-child { border-bottom: none; }
    .recommendation-item .icon { margin-right: 8px; }
    .stButton > button {
        background: linear-gradient(135deg, rgba(0, 240, 255, 0.15), rgba(176, 38, 255, 0.15)) !important;
        border: 1px solid rgba(0, 240, 255, 0.4) !important;
        color: #00f0ff !important;
        font-family: 'Courier New', monospace !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(5px);
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.2);
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(0, 240, 255, 0.3), rgba(176, 38, 255, 0.3)) !important;
        border-color: #00f0ff !important;
        box-shadow: 0 0 30px rgba(0, 240, 255, 0.3) !important;
        transform: scale(1.02);
        color: #ffffff !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, rgba(0, 240, 255, 0.25), rgba(176, 38, 255, 0.25)) !important;
        border: 1px solid #00f0ff !important;
        box-shadow: 0 0 30px rgba(0, 240, 255, 0.2) !important;
        color: #ffffff !important;
        text-shadow: 0 0 20px rgba(0, 240, 255, 0.4);
    }
    [data-testid="metric-container"] {
        background: rgba(15, 15, 35, 0.8);
        border: 1px solid rgba(0, 240, 255, 0.15);
        border-radius: 10px;
        padding: 15px;
        backdrop-filter: blur(5px);
    }
    [data-testid="metric-container"] label {
        color: #00f0ff !important;
        font-family: 'Courier New', monospace !important;
        letter-spacing: 2px;
        font-size: 0.8rem !important;
    }
    [data-testid="metric-container"] div {
        color: #ffffff !important;
        font-family: 'Courier New', monospace !important;
        font-weight: bold !important;
    }
    .dataframe {
        background: rgba(15, 15, 35, 0.8) !important;
        border: 1px solid rgba(0, 240, 255, 0.15) !important;
        border-radius: 10px !important;
        font-family: 'Courier New', monospace !important;
    }
    .dataframe th {
        color: #00f0ff !important;
        background: rgba(0, 240, 255, 0.1) !important;
        font-family: 'Courier New', monospace !important;
        letter-spacing: 1px;
        font-weight: bold !important;
        font-size: 0.9rem !important;
    }
    .dataframe td {
        color: #ffffff !important;
        font-family: 'Courier New', monospace !important;
        font-size: 0.85rem !important;
    }
    .streamlit-expanderHeader {
        background: rgba(15, 15, 35, 0.8) !important;
        border: 1px solid rgba(0, 240, 255, 0.15) !important;
        border-radius: 8px !important;
        color: #00f0ff !important;
        font-family: 'Courier New', monospace !important;
        letter-spacing: 1px;
        font-weight: bold !important;
    }
    .streamlit-expanderContent {
        background: rgba(15, 15, 35, 0.8) !important;
        border: 1px solid rgba(0, 240, 255, 0.1) !important;
        border-top: none !important;
    }
    .streamlit-expanderContent p, .streamlit-expanderContent div,
    .streamlit-expanderContent li, .streamlit-expanderContent span {
        color: #ffffff !important;
    }
    .stSelectbox [data-baseweb="select"] {
        background: rgba(15, 15, 35, 0.8) !important;
        border: 1px solid rgba(0, 240, 255, 0.2) !important;
        color: #00f0ff !important;
    }
    .stTextInput input, .stTextArea textarea {
        background: rgba(15, 15, 35, 0.8) !important;
        border: 1px solid rgba(0, 240, 255, 0.2) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
        font-family: 'Courier New', monospace !important;
    }
    .stAlert {
        background: rgba(15, 15, 35, 0.9) !important;
        border: 1px solid rgba(0, 240, 255, 0.2) !important;
        border-radius: 8px !important;
    }
    .stAlert p, .stAlert div, .stAlert li, .stAlert span { color: #ffffff !important; }
    .stProgress > div > div {
        background: linear-gradient(90deg, #00f0ff, #b026ff, #ff2d95) !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(15, 15, 35, 0.8) !important;
        border: 1px solid rgba(0, 240, 255, 0.15) !important;
        border-radius: 8px !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #a0a0c0 !important;
        font-family: 'Courier New', monospace !important;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #00f0ff !important;
        border-bottom: 2px solid #00f0ff !important;
        text-shadow: 0 0 20px rgba(0, 240, 255, 0.3);
        font-weight: bold !important;
    }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: rgba(10, 10, 20, 0.5); }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #00f0ff, #b026ff);
        border-radius: 3px;
    }
    .folium-map {
        border: 1px solid rgba(0, 240, 255, 0.2);
        border-radius: 12px;
        box-shadow: 0 0 40px rgba(0, 240, 255, 0.05);
    }
    .cyber-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #00f0ff, #b026ff, #ff2d95, transparent);
        margin: 20px 0;
        opacity: 0.5;
    }
    .stMarkdown p, .stMarkdown li {
        color: #ffffff !important;
        font-family: 'Courier New', monospace !important;
        line-height: 1.6 !important;
    }
    .stMarkdown h1 { color: #00f0ff !important; }
    .stMarkdown h2 { color: #b026ff !important; }
    .stMarkdown h3 { color: #ff2d95 !important; }
    .stMarkdown h4 { color: #39ff14 !important; }
    .stCaption {
        color: #a0a0c0 !important;
        font-family: 'Courier New', monospace !important;
        font-size: 0.8rem !important;
    }
    .stRadio label {
        color: #ffffff !important;
        font-family: 'Courier New', monospace !important;
        font-size: 0.9rem !important;
    }
    .stRadio [role="radiogroup"] {
        gap: 8px;
    }
    .payload-box {
        background: linear-gradient(135deg, rgba(0, 240, 255, 0.08), rgba(176, 38, 255, 0.08));
        border: 1px solid rgba(0, 240, 255, 0.3);
        border-radius: 12px;
        padding: 18px;
        margin: 12px 0;
    }
    .corridor-box {
        background: linear-gradient(135deg, rgba(57, 255, 20, 0.08), rgba(0, 240, 255, 0.08));
        border: 1px solid rgba(57, 255, 20, 0.3);
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
"""

BMC_BUTTON_HTML = """
<div style="text-align: center; padding: 30px 0 20px 0; margin-top: 20px;">
    <a href="https://buymeacoffee.com/stargazex" target="_blank">
        <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png"
             alt="Buy Me A Coffee"
             style="height: 60px !important;width: 217px !important;">
    </a>
</div>
"""

# ============================================================================
# SHARED RECOMMENDATION ENGINE
# ============================================================================

def generate_recommendation_strategy(result_data: Dict) -> Dict:
    score = result_data.get('suitability_percentage', 0)
    details = result_data.get('details', {})
    elevation_m = result_data.get('elevation_m', 0)
    flood_risk = result_data.get('flood_risk', 'Unknown')
    population_density = result_data.get('population_density', 0)
    coastal_distance = result_data.get('coastal_distance_km', 0)
    wind_speed = result_data.get('wind_speed_ms', None)
    wind_gust = result_data.get('wind_gust_ms', None)

    recommendations = {
        'immediate_actions': [],
        'short_term_actions': [],
        'long_term_actions': [],
        'investment_required': 'Low',
        'overall_feasibility': 'High',
        'risk_level': 'Low',
    }

    def add_action(bucket, text, priority, cost):
        recommendations[bucket].append({
            'text': text, 'priority': priority, 'cost': cost
        })

    # 1. ELEVATION
    if elevation_m < 20:
        add_action('immediate_actions',
            '🚨 CRITICAL: Elevation is very low (<20m). Build massive flood defenses and elevated launch pads immediately.',
            'Critical', '💸💸💸💸💸')
        recommendations['investment_required'] = 'Very High'
    elif elevation_m < 50:
        add_action('short_term_actions',
            '🌊 Build flood defenses and drainage systems. Elevation is moderate.',
            'High', '💸💸💸')
        if recommendations['investment_required'] != 'Very High':
            recommendations['investment_required'] = 'Moderate'
    elif elevation_m < 200:
        add_action('immediate_actions',
            '✅ Excellent elevation (50-200m). No flood defenses needed. Proceed with standard launch pad design.',
            'Low', '💸')
    elif elevation_m < 500:
        add_action('short_term_actions',
            '⛰️ Good elevation (200-500m). Plan for stable foundations and wind protection.',
            'Medium', '💸💸')
    else:
        add_action('short_term_actions',
            '🏔️ Very high elevation (500m+). Consider construction challenges and weather protection.',
            'Medium', '💸💸💸')

    # 2. POPULATION
    if population_density > 5:
        add_action('immediate_actions',
            '🏙️ HIGH POPULATION DENSITY. Need extensive evacuation plans and safety buffer zones.',
            'Critical', '💸💸💸💸')
    elif population_density > 2:
        add_action('short_term_actions',
            '🏘️ MODERATE POPULATION. Develop evacuation procedures and community engagement.',
            'High', '💸💸💸')
    else:
        add_action('immediate_actions',
            '✅ VERY LOW POPULATION. Ideal for spaceport - minimal evacuation required.',
            'Low', '💸')

    # 3. COASTAL
    if coastal_distance < 5:
        add_action('immediate_actions',
            '🌊 PERFECT COASTAL ACCESS. Leverage sea transport for heavy equipment.',
            'Low', '💸')
    elif coastal_distance < 30:
        add_action('short_term_actions',
            '🚢 GOOD COASTAL ACCESS. Build access roads to the coast. Consider sea transport hub.',
            'Medium', '💸💸')
    else:
        add_action('long_term_actions',
            '🚛 INLAND LOCATION. Significant transport infrastructure needed.',
            'High', '💸💸💸💸')

    # 4. INFRASTRUCTURE
    infra_details = details.get('infrastructure_access', {}).get('value', {})
    if isinstance(infra_details, dict):
        if infra_details.get('airports', 0) == 0:
            add_action('short_term_actions',
                '✈️ No airport nearby. Build airstrip for personnel transport.',
                'High', '💸💸💸')
        if infra_details.get('major_roads', 0) == 0:
            add_action('short_term_actions',
                '🛣️ No major roads. Build access roads for equipment transport.',
                'High', '💸💸💸')
        if infra_details.get('ports', 0) == 0:
            add_action('long_term_actions',
                '🚢 No port. Consider building a small port for heavy equipment delivery.',
                'Medium', '💸💸💸💸')
        if infra_details.get('power_facilities', 0) == 0:
            add_action('long_term_actions',
                '⚡ No power infrastructure. Build power plant or connect to grid.',
                'High', '💸💸💸💸')

    # 5. LAND
    land_details = details.get('land_availability', {}).get('value', {})
    if isinstance(land_details, dict):
        forest = land_details.get('forest_areas', 0)
        developed = land_details.get('developed_areas', 0)
        if forest > 20 and developed < 5:
            add_action('immediate_actions',
                '🌳 ABUNDANT LAND. Excellent for expansion. Ready for development.',
                'Low', '💸')
        elif forest > 10 and developed < 10:
            add_action('short_term_actions',
                '🌿 GOOD LAND AVAILABILITY. Plan for expansion and buffer zones.',
                'Medium', '💸💸')
        else:
            add_action('immediate_actions',
                '🏗️ LIMITED LAND. Need to acquire additional land for launch pads and safety zones.',
                'Critical', '💸💸💸💸')

    # 6. FLOOD
    if flood_risk == 'High':
        add_action('immediate_actions',
            '🌊 HIGH FLOOD RISK! Emergency flood defenses needed. Consider elevating all structures.',
            'Critical', '💸💸💸💸💸')
        recommendations['investment_required'] = 'Very High'
    elif flood_risk == 'Moderate':
        add_action('short_term_actions',
            '🌊 MODERATE FLOOD RISK. Build standard flood defenses and drainage systems.',
            'High', '💸💸💸')
        if recommendations['investment_required'] != 'Very High':
            recommendations['investment_required'] = 'Moderate'

    # 7. LATITUDE
    lat_deg = result_data.get('lat_deg', 0)
    if lat_deg < 3:
        add_action('immediate_actions',
            f'🌐 EXCELLENT LATITUDE ({lat_deg:.1f}°). Near equator - maximum fuel efficiency! ✅',
            'Low', '💸')
    elif lat_deg < 5:
        add_action('immediate_actions',
            f'🌐 GOOD LATITUDE ({lat_deg:.1f}°). Good launch efficiency.',
            'Low', '💸')
    else:
        add_action('short_term_actions',
            f'🌐 MODERATE LATITUDE ({lat_deg:.1f}°). Optimize launch trajectories for fuel efficiency.',
            'Medium', '💸💸')

    # 8. WIND / WEATHER
    if wind_speed is not None:
        if wind_speed > 12:
            add_action('immediate_actions',
                f'🌬️ HIGH WIND SPEED ({wind_speed:.1f} m/s). Need robust wind shear protection and launch-window scheduling. High operational cost.',
                'Critical', '💸💸💸💸')
        elif wind_speed > 8:
            add_action('short_term_actions',
                f'🌬️ MODERATE WIND ({wind_speed:.1f} m/s). Plan wind-monitoring systems and flexible launch windows.',
                'High', '💸💸💸')
        elif wind_speed < 4:
            add_action('immediate_actions',
                f'✅ EXCELLENT WIND CONDITIONS ({wind_speed:.1f} m/s). Calm, stable air — ideal for launches.',
                'Low', '💸')
        else:
            add_action('short_term_actions',
                f'🌬️ GOOD WIND ({wind_speed:.1f} m/s). Normal launch conditions. Standard weather monitoring recommended.',
                'Low', '💸')

        if wind_gust is not None and wind_gust > 15:
            add_action('short_term_actions',
                f'💨 STRONG GUSTS ({wind_gust:.1f} m/s). Design structures for high wind-load. Consider reinforced launch pad and hangar.',
                'High', '💸💸💸')

    critical_count = sum(
        1 for a in recommendations['immediate_actions']
        if a['priority'] == 'Critical'
    )
    high_count = sum(
        1 for a in recommendations['short_term_actions']
        if a['priority'] == 'High'
    )
    total_actions = (
        len(recommendations['immediate_actions'])
        + len(recommendations['short_term_actions'])
        + len(recommendations['long_term_actions'])
    )

    if score >= 80:
        score_band, score_emoji = 'Excellent', '✅'
    elif score >= 65:
        score_band, score_emoji = 'Good', '👍'
    elif score >= 50:
        score_band, score_emoji = 'Moderate', '👌'
    elif score >= 35:
        score_band, score_emoji = 'Limited', '⚠️'
    else:
        score_band, score_emoji = 'Poor', '❌'

    if critical_count >= 3:
        feasibility = '❌ Poor - Major critical issues must be resolved before development'
        risk_level = 'Very High'
    elif critical_count == 2:
        feasibility = '⚠️ Limited - Multiple critical issues require resolution'
        risk_level = 'High'
    elif critical_count == 1:
        feasibility = '👌 Moderate - One critical issue requires resolution'
        risk_level = 'High'
    elif high_count >= 2:
        feasibility = '👌 Moderate - Several high-priority preparations required'
        risk_level = 'Medium'
    else:
        feasibility = f'{score_emoji} {score_band} - ' + {
            'Excellent': 'High potential for immediate development',
            'Good': 'Suitable with minor site preparation',
            'Moderate': 'Significant investment required',
            'Limited': 'Major investment required',
            'Poor': 'Not recommended for spaceport development',
        }[score_band]
        risk_level = {
            'Excellent': 'Low', 'Good': 'Low',
            'Moderate': 'Medium', 'Limited': 'High', 'Poor': 'Very High',
        }[score_band]

    recommendations['overall_feasibility'] = feasibility
    recommendations['risk_level'] = risk_level
    recommendations['critical_action_count'] = critical_count
    recommendations['high_action_count'] = high_count
    recommendations['total_action_count'] = total_actions

    recommendations['timeline_summary'] = {
        'immediate': f"{len(recommendations['immediate_actions'])} actions (0-6 months)",
        'short_term': f"{len(recommendations['short_term_actions'])} actions (6-18 months)",
        'long_term': f"{len(recommendations['long_term_actions'])} actions (18-36 months)"
    }
    return recommendations

# ============================================================================
# CACHE MANAGER
# ============================================================================

class APICache:
    def __init__(self, cache_dir: str = "spaceportvbase_cache", ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)

    def _get_cache_key(self, url: str, params: Dict) -> str:
        key_str = url + json.dumps(params, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, url: str, params: Dict) -> Optional[Dict]:
        cache_key = self._get_cache_key(url, params)
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            modified_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - modified_time < self.ttl:
                try:
                    with open(cache_file, 'r') as f:
                        return json.load(f)
                except Exception:
                    return None
        return None

    def set(self, url: str, params: Dict, data: Dict) -> None:
        cache_key = self._get_cache_key(url, params)
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass

    def clear(self):
        for f in self.cache_dir.glob("*.json"):
            f.unlink()

    def get_stats(self) -> Dict:
        files = list(self.cache_dir.glob("*.json"))
        return {'total_cached': len(files), 'cache_dir': str(self.cache_dir)}

api_cache = APICache()

# ============================================================================
# NEW FEATURE HELPERS
# ============================================================================

def compute_launch_azimuth(lat: float, lon: float) -> Dict:
    if lon > 116.0 or (lon > 102.0 and lat > 2.0 and lat < 7.5):
        azimuth = 90.0
        direction = 'E → South China Sea / Sulu Sea'
        length_km = 300
        note = 'Open ocean — safe corridor'
    elif lon < 101.0:
        azimuth = 270.0
        direction = 'W → Strait of Malacca / Andaman Sea'
        length_km = 250
        note = 'International waters — coordinate with neighbours'
    else:
        azimuth = 90.0
        direction = 'E → South China Sea'
        length_km = 350
        note = 'Passes over interior — restrict to polar/inclined orbits'
    return {
        'azimuth_deg': azimuth,
        'direction_label': direction,
        'corridor_length_km': length_km,
        'safety_note': note,
    }


def compute_corridor_polygon(lat: float, lon: float, azimuth_deg: float,
                              length_km: float, width_km: float = 20.0) -> List[tuple]:
    lat_deg = length_km / 111.0
    lon_deg = length_km / (111.0 * max(math.cos(math.radians(lat)), 0.1))
    width_lat = width_km / 111.0
    width_lon = width_km / (111.0 * max(math.cos(math.radians(lat)), 0.1))

    az_rad = math.radians(azimuth_deg)
    end_lat = lat + lat_deg * math.cos(az_rad)
    end_lon = lon + lon_deg * math.sin(az_rad)

    perp_lat = width_lat * math.cos(az_rad + math.pi / 2)
    perp_lon = width_lon * math.sin(az_rad + math.pi / 2)

    return [
        (lat - perp_lat, lon - perp_lon),
        (lat + perp_lat, lon + perp_lon),
        (end_lat + perp_lat, end_lon + perp_lon),
        (end_lat - perp_lat, end_lon - perp_lon),
    ]


def compute_payload_delta_v(lat_deg: float, elevation_m: float) -> Dict:
    lat_abs = abs(lat_deg)
    cape_lat = 28.5

    v_rot_site = 465.0 * math.cos(math.radians(lat_abs))
    v_rot_cape = 465.0 * math.cos(math.radians(cape_lat))
    dv_bonus_ms = v_rot_site - v_rot_cape
    elev_bonus_ms = elevation_m * 0.01
    total_bonus_ms = dv_bonus_ms + elev_bonus_ms

    baseline_leo_t = 22.8
    pct_improvement = total_bonus_ms / 100.0
    leo_payload_t = baseline_leo_t * (1 + pct_improvement / 100.0)
    gto_payload_t = leo_payload_t * 0.42

    return {
        'dv_bonus_ms': round(total_bonus_ms, 1),
        'leo_payload_t': round(leo_payload_t, 2),
        'gto_payload_t': round(gto_payload_t, 2),
        'pct_improvement': round(pct_improvement, 2),
        'rotation_speed_ms': round(v_rot_site, 1),
        'baseline_leo_t': baseline_leo_t,
    }


def fetch_wind_history(lat: float, lon: float, days: int = 30) -> Optional[Dict]:
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily": "wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant",
            "wind_speed_unit": "ms",
            "timezone": "auto",
        }
        r = requests.get(url, params=params, timeout=8)
        if r.status_code != 200:
            return None
        data = r.json()
        daily = data.get('daily', {})
        if not daily.get('time'):
            return None
        df = pd.DataFrame({
            'date': daily['time'],
            'wind_max': daily.get('wind_speed_10m_max', []),
            'gust_max': daily.get('wind_gusts_10m_max', []),
            'direction': daily.get('wind_direction_10m_dominant', []),
        })
        return {
            'df': df,
            'mean_wind': float(df['wind_max'].mean()) if len(df) else 0,
            'max_wind': float(df['wind_max'].max()) if len(df) else 0,
            'min_wind': float(df['wind_max'].min()) if len(df) else 0,
            'calm_days': int((df['wind_max'] < 6).sum()),
            'total_days': len(df),
        }
    except Exception:
        return None


def geocode_query(query: str) -> Optional[Dict]:
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': query,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'my',
        }
        headers = {'User-Agent': 'StarbaseV/1.0 (spaceport site selection)'}
        r = requests.get(url, params=params, headers=headers, timeout=8)
        if r.status_code != 200:
            return None
        data = r.json()
        if not data:
            params.pop('countrycodes', None)
            r = requests.get(url, params=params, headers=headers, timeout=8)
            data = r.json()
            if not data:
                return None
        result = data[0]
        return {
            'lat': float(result['lat']),
            'lon': float(result['lon']),
            'display_name': result.get('display_name', query),
        }
    except Exception:
        return None


def parse_coordinates(text: str) -> Optional[Dict]:
    try:
        parts = text.replace(' ', '').split(',')
        if len(parts) == 2:
            lat = float(parts[0])
            lon = float(parts[1])
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return {'lat': lat, 'lon': lon,
                        'display_name': f'Custom coordinates ({lat:.4f}, {lon:.4f})'}
    except Exception:
        pass
    return None


def generate_report_text(result_data: Dict) -> str:
    lines = []
    lines.append("=" * 70)
    lines.append("STARBASEV - SPACEPORT SITE ANALYSIS REPORT")
    lines.append("=" * 70)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append(f"LOCATION: {result_data.get('location', 'Unknown')}")
    lines.append(f"LATITUDE: {result_data.get('lat_deg', 0):.4f}°")
    lines.append(f"ELEVATION: {result_data.get('elevation_m', 0):.0f} m")
    lines.append("")
    lines.append("-" * 70)
    lines.append("SUITABILITY SCORE")
    lines.append("-" * 70)
    lines.append(f"Score: {result_data.get('suitability_percentage', 0)}%")
    lines.append(f"Rating: {result_data.get('rating', 'Unknown')} {result_data.get('rating_emoji', '')}")
    lines.append(f"Recommendation: {result_data.get('recommendation', '')}")
    lines.append("")
    lines.append("-" * 70)
    lines.append("SCORING BREAKDOWN")
    lines.append("-" * 70)
    details = result_data.get('details', {})
    scores = result_data.get('scores', {})
    for key, detail in details.items():
        label = key.replace('_', ' ').title()
        score = scores.get(key, 0)
        value = detail.get('value', 'N/A')
        weight = detail.get('weight', 0)
        lines.append(f"{label}: {score:.1f}/5  (value: {value}, weight: {weight*100:.0f}%)")
    lines.append("")
    lines.append("-" * 70)
    lines.append("RECOMMENDATION STRATEGY")
    lines.append("-" * 70)
    recs = generate_recommendation_strategy(result_data)
    lines.append(f"Overall Feasibility: {recs.get('overall_feasibility', '')}")
    lines.append(f"Risk Level: {recs.get('risk_level', '')}")
    lines.append(f"Investment Required: {recs.get('investment_required', '')}")
    lines.append("")
    for bucket_name, bucket_title in [
        ('immediate_actions', 'IMMEDIATE ACTIONS (0-6 months)'),
        ('short_term_actions', 'SHORT-TERM ACTIONS (6-18 months)'),
        ('long_term_actions', 'LONG-TERM ACTIONS (18-36 months)'),
    ]:
        if recs.get(bucket_name):
            lines.append(f"{bucket_title}:")
            for a in recs[bucket_name]:
                lines.append(f"  - [{a.get('priority', '')}] {a.get('text', '')}  (cost: {a.get('cost', '')})")
            lines.append("")
    lines.append("=" * 70)
    lines.append("End of report · StarbaseV")
    lines.append("=" * 70)
    return "\n".join(lines)


# ============================================================================
# FAVORITES MANAGEMENT
# ============================================================================

FAVORITES_DB = "spaceportvbase_favorites.db"

def init_favorites_db():
    conn = sqlite3.connect(FAVORITES_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            region TEXT DEFAULT 'unknown',
            score REAL DEFAULT 0,
            rating TEXT DEFAULT '',
            added_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_favorite(name: str, lat: float, lon: float, region: str, score: float, rating: str):
    init_favorites_db()
    conn = sqlite3.connect(FAVORITES_DB)
    c = conn.cursor()
    c.execute("SELECT id FROM favorites WHERE name = ? AND lat = ? AND lon = ?",
              (name, lat, lon))
    if c.fetchone():
        conn.close()
        return False
    c.execute("""
        INSERT INTO favorites (name, lat, lon, region, score, rating, added_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, lat, lon, region, score, rating, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return True

def get_favorites() -> List[Dict]:
    init_favorites_db()
    conn = sqlite3.connect(FAVORITES_DB)
    c = conn.cursor()
    c.execute("SELECT id, name, lat, lon, region, score, rating, added_at FROM favorites ORDER BY added_at DESC")
    rows = c.fetchall()
    conn.close()
    return [
        {'id': r[0], 'name': r[1], 'lat': r[2], 'lon': r[3],
         'region': r[4], 'score': r[5], 'rating': r[6], 'added_at': r[7]}
        for r in rows
    ]

def remove_favorite(fid: int):
    conn = sqlite3.connect(FAVORITES_DB)
    c = conn.cursor()
    c.execute("DELETE FROM favorites WHERE id = ?", (fid,))
    conn.commit()
    conn.close()

def is_favorite(name: str, lat: float, lon: float) -> bool:
    init_favorites_db()
    conn = sqlite3.connect(FAVORITES_DB)
    c = conn.cursor()
    c.execute("SELECT id FROM favorites WHERE name = ? AND lat = ? AND lon = ?",
              (name, lat, lon))
    row = c.fetchone()
    conn.close()
    return row is not None


# ============================================================================
# BORNEO DATA
# ============================================================================

SABAH_LOCATIONS = {
    'Kota Kinabalu City Center': (5.9804, 116.0735),
    'KK Waterfront': (5.9850, 116.0750),
    'Tanjung Aru Beach': (5.9400, 116.0500),
    'Likas Bay': (5.9500, 116.0200),
    'Signal Hill': (5.9750, 116.0700),
    'Atkinson Clock Tower': (5.9800, 116.0710),
    'Sabah State Mosque': (5.9600, 116.0800),
    'Tun Mustapha Tower': (5.9900, 116.0700),
    'Sabah Museum': (5.9600, 116.0650),
    'Jesselton Point': (5.9850, 116.0750),
    '1Borneo Mall': (6.0200, 116.1100),
    'Imago Mall': (5.9800, 116.0700),
    'Suria Sabah': (5.9800, 116.0700),
    'Sutera Harbour': (5.9600, 116.0600),
    'Queen Elizabeth Hospital': (5.9680, 116.0680),
    'KPJ Sabah Hospital': (5.9800, 116.0730),
    'Universiti Malaysia Sabah': (6.0300, 116.1200),
    'Penampang': (5.9000, 116.0800),
    'Putatan': (5.8800, 116.0600),
    'Tuaran': (6.1800, 116.2400),
    'Papar': (5.7300, 115.9300),
    'Kinarut': (5.8200, 116.0500),
    'Lok Kawi': (5.8500, 116.0300),
    'Kota Kinabalu Industrial Park': (5.9200, 116.0400),
    'Menggatal': (6.0200, 116.1400),
    'Sepanggar': (6.0400, 116.0900),
    'Inanam': (6.0000, 116.1200),
    'Telipok': (6.0800, 116.1900),
    'Likas': (5.9600, 116.0300),
    'Luyang': (5.9300, 116.0700),
    'Donggongon': (5.9000, 116.0900),
    'Keningau': (5.3300, 116.1600),
    'Tenom': (5.1300, 115.9500),
    'Beaufort': (5.3500, 115.7500),
    'Sipitang': (5.0800, 115.5500),
    'Nabawan': (5.0800, 116.4300),
    'Tambunan': (5.6700, 116.3600),
    'Kuala Penyu': (5.5700, 115.5800),
    'Membakut': (5.4700, 115.7800),
    'Weston': (5.2700, 115.4800),
    'Kemabong': (5.0800, 116.0800),
    'Sook': (5.1300, 116.2200),
    'Melalap': (5.0800, 115.9000),
    'Bongawan': (5.5300, 115.8300),
    'Klias': (5.4300, 115.6800),
    'Limbawang': (5.1700, 115.5800),
    'Gana': (5.0300, 115.4800),
    'Kudat': (6.8860, 116.8430),
    'Kota Marudu': (6.5000, 116.7400),
    'Pitas': (6.7200, 117.0700),
    'Banggi Island': (7.2300, 117.1700),
    'Malawali Island': (7.1500, 117.1300),
    'Tanjung Simpang Mengayau': (7.0900, 116.9100),
    'Bakapit': (6.8000, 116.8000),
    'Matunggong': (6.7700, 116.7900),
    'Tindakon': (6.8700, 116.8500),
    'Pinangsoo': (6.9200, 116.8800),
    'Perancangan': (6.9500, 116.9000),
    'Sandakan City Center': (5.8400, 118.1200),
    'Sandakan Waterfront': (5.8420, 118.1220),
    'Sandakan Hospital': (5.8480, 118.1250),
    'Sandakan Airport': (5.9010, 118.0580),
    'Sandakan Harbour': (5.8400, 118.1300),
    'Sepilok Orangutan Centre': (5.8650, 117.9420),
    'Sandakan Rainforest Discovery Centre': (5.8700, 117.9450),
    'Gomantong Caves': (5.5300, 118.0700),
    'Sukau': (5.5000, 118.2500),
    'Kinabatangan River': (5.4000, 117.8000),
    'Telupid': (5.6300, 117.1300),
    'Beluran': (5.8800, 117.5600),
    'Pamol': (5.4800, 118.0800),
    'Batu Putih': (5.3800, 117.9200),
    'Muanad': (5.4800, 118.1800),
    'Bilit': (5.4200, 117.8200),
    'Abai': (5.3500, 117.6800),
    'Batu Bulan': (5.2800, 117.5800),
    'Tawau City Center': (4.2435, 117.8853),
    'Tawau Waterfront': (4.2450, 117.8870),
    'Tawau Hospital': (4.2520, 117.8970),
    'Tawau Airport': (4.3133, 117.9183),
    'Tawau Hills Park': (4.3500, 117.9000),
    'Tawau Sports Complex': (4.2400, 117.8800),
    'Lahad Datu': (5.0300, 118.3300),
    'Felda Sahabat': (5.0620, 119.0810),
    'Dent Haven': (5.2680, 119.2620),
    'Semporna': (4.4800, 118.6100),
    'Kunak': (4.6800, 118.2500),
    'Silam': (4.8700, 118.2300),
    'Kalabakan': (4.2200, 117.4800),
    'Maliau Basin': (4.7200, 117.5200),
    'Danum Valley': (4.9500, 117.7800),
    'Tabin Wildlife Reserve': (5.2000, 118.6500),
    'Tungku': (4.7000, 118.2000),
    'Merotai': (4.3000, 117.8500),
    'Apas': (4.2800, 117.8800),
    'Balung': (4.1800, 117.6800),
    'Umas Umas': (4.1500, 117.5800),
    'Bombalai': (4.1200, 117.4800),
    'Tanjung Batu': (4.0500, 117.3800),
    'Mount Kinabalu': (6.0750, 116.5583),
    'Kinabalu National Park': (6.0100, 116.5400),
    'Kundasang': (5.9800, 116.5700),
    'Ranau': (5.9500, 116.6700),
    'Mesilau': (6.0400, 116.5900),
    'Poring Hot Springs': (6.0500, 116.7000),
    'Crocker Range': (5.8000, 116.3000),
    'Trus Madi': (5.5000, 116.4000),
    'Maliau Basin Conservation': (4.7200, 117.5200),
    'Long Pasia': (4.4000, 115.7500),
    'Kipungit': (6.0200, 116.6200),
    'Eastern Sabah Hills': (5.0000, 117.8500),
    'Pulau Gaya': (5.9800, 116.0200),
    'Pulau Manukan': (5.9700, 116.0000),
    'Pulau Mamutik': (5.9600, 115.9900),
    'Pulau Sapi': (5.9500, 115.9900),
    'Pulau Sulug': (5.9400, 115.9800),
    'Pulau Sipadan': (4.1140, 118.6250),
    'Pulau Mabul': (4.2400, 118.6200),
    'Pulau Kapalai': (4.2100, 118.6600),
    'Pulau Ligitan': (4.1500, 118.8800),
    'Pulau Bohey Dulang': (4.5800, 118.7800),
    'Pulau Bum Bum': (4.5000, 118.7100),
    'Pulau Sebatik': (4.1300, 117.7800),
    'Pulau Tiga': (5.7200, 115.6300),
    'Pulau Dinawan': (5.7000, 115.5800),
}

SARAWAK_LOCATIONS = {
    'Kuching City Center': (1.5497, 110.3633),
    'Kuching Waterfront': (1.5597, 110.3433),
    'Kuching Hospital': (1.5697, 110.3533),
    'Kuching Airport': (1.4843, 110.3469),
    'Sarawak Museum': (1.5547, 110.3633),
    'Sarawak State Mosque': (1.5547, 110.3533),
    'Kuching Civic Centre': (1.5597, 110.3633),
    'Borneo Convention Centre': (1.5647, 110.3833),
    'Satok Bridge': (1.5497, 110.3433),
    'Stutong Park': (1.5347, 110.3833),
    'Damai Beach': (1.7000, 110.3800),
    'Santubong': (1.7000, 110.3800),
    'Bako National Park': (1.7400, 110.4800),
    'Semenggoh Wildlife Centre': (1.4000, 110.3300),
    'Bau': (1.4100, 110.1500),
    'Lundu': (1.6700, 109.8500),
    'Puncak Borneo': (1.2500, 110.1000),
    'Padawan': (1.3500, 110.2000),
    'Serian': (1.1700, 110.5700),
    'Siburan': (1.3000, 110.3500),
    'Tebedu': (1.1200, 110.5300),
    'Bengkoh': (1.4500, 110.2500),
    'Kota Sentosa': (1.4800, 110.3300),
    'Jalan Batu Kawa': (1.5000, 110.3000),
    'Matang': (1.6200, 110.1800),
    'Kuching Wetlands': (1.5800, 110.3200),
    'Kota Samarahan': (1.4500, 110.5000),
    'Asajaya': (1.6000, 110.6200),
    'Simunjan': (1.3800, 110.7500),
    'Sebuyau': (1.5200, 110.9300),
    'Sadong Jaya': (1.4700, 110.7300),
    'Muaras': (1.5300, 110.5800),
    'Semera': (1.4200, 110.4800),
    'Sri Aman': (1.2000, 111.5000),
    'Lubok Antu': (1.0500, 111.8300),
    'Engkilili': (1.1300, 111.6700),
    'Pantu': (1.0800, 111.4200),
    'Lingga': (1.3300, 111.1500),
    'Balai Ringin': (1.0300, 111.1500),
    'Rimbang': (1.1000, 111.3000),
    'Betong': (1.4100, 111.5300),
    'Debak': (1.5600, 111.4200),
    'Pusa': (1.4800, 111.3000),
    'Saratok': (1.7400, 111.3200),
    'Spaoh': (1.4500, 111.4500),
    'Maludam': (1.6500, 111.2500),
    'Roban': (1.6800, 111.3800),
    'Sarikei': (2.1000, 111.8000),
    'Bintangor': (2.1500, 111.9000),
    'Julau': (2.0200, 111.9100),
    'Pakan': (1.8800, 111.7800),
    'Matu': (2.1000, 111.5300),
    'Daro': (2.0500, 111.4800),
    'Jakar': (2.0800, 111.6500),
    'Sibu City Center': (2.2871, 111.8301),
    'Sibu Waterfront': (2.2971, 111.8201),
    'Sibu Hospital': (2.2971, 111.8401),
    'Sibu Airport': (2.2586, 111.9661),
    'Sibu Central Market': (2.2871, 111.8301),
    'Tua Pek Kong Temple': (2.2871, 111.8301),
    'Kanowit': (2.1000, 112.1500),
    'Selangau': (2.5200, 112.3200),
    'Tatau': (2.8800, 112.8500),
    'Nanga Dap': (2.3200, 112.1000),
    'Durin': (2.2000, 111.9000),
    'Sungei Bidut': (2.2500, 111.7500),
    'Mukah': (2.9064, 112.0800),
    'Dalat': (2.7500, 111.9700),
    'Oya': (2.8500, 111.8500),
    'Balingian': (2.9200, 112.5300),
    'Tanjung Manis': (2.7100, 111.6200),
    'Igan': (2.8200, 111.7500),
    'Ladang': (2.7800, 112.0500),
    'Kapit': (2.0000, 112.5000),
    'Song': (2.0100, 112.5400),
    'Belaga': (2.7000, 113.7800),
    'Bakun Dam': (2.7600, 113.9300),
    'Murum Dam': (2.9400, 114.1700),
    'Baleh': (2.3000, 113.2000),
    'Nanga Merit': (1.8000, 112.8000),
    'Rumah Siga': (2.2000, 113.0000),
    'Bintulu City Center': (3.1746, 113.0316),
    'Bintulu Waterfront': (3.1846, 113.0216),
    'Bintulu Hospital': (3.1846, 113.0416),
    'Bintulu Airport': (3.1232, 113.0195),
    'Tanjung Batu Beach': (3.1946, 113.0116),
    'Bintulu Port': (3.1746, 113.0316),
    'Sebauh': (3.1000, 112.9800),
    'Samalaju': (3.4500, 113.1200),
    'Tubau': (3.1800, 113.1300),
    'Jepak': (3.1500, 112.9800),
    'Kemena': (3.2000, 113.0000),
    'Miri City Center': (4.3995, 113.9918),
    'Miri Waterfront': (4.4095, 113.9818),
    'Miri Hospital': (4.4095, 113.9918),
    'Miri Airport': (4.3223, 113.9868),
    'Miri Marina': (4.4195, 113.9718),
    'Tanjung Lobang': (4.4295, 113.9618),
    'Grand Old Lady': (4.3995, 113.9918),
    'Marudi': (4.1800, 114.3200),
    'Lutong': (4.4700, 114.0200),
    'Bekenu': (4.0600, 113.7700),
    'Niah National Park': (3.8100, 113.7700),
    'Lambir Hills': (4.2200, 114.0300),
    'Sibuti': (3.8000, 113.6300),
    'Kuala Baram': (4.5800, 114.0000),
    'Sungai Tujoh': (4.5000, 113.9500),
    'Piasau': (4.4200, 113.9800),
    'Permyjaya': (4.4500, 114.0000),
    'Limbang': (4.7500, 115.0000),
    'Lawas': (4.8500, 115.4000),
    'Sundar': (4.7200, 115.5800),
    'Trusan': (4.8700, 115.2000),
    'Long Semadoh': (4.0500, 115.5000),
    'Ba Kelalan': (3.9700, 115.6200),
    'Bario': (3.7300, 115.4700),
    'Mulu National Park': (4.0450, 114.9380),
    'Gunung Mulu': (4.0500, 114.9300),
    'Deer Cave': (4.0300, 114.9100),
    'Clearwater Cave': (4.0200, 114.9200),
    'Wind Cave': (4.0400, 114.9000),
    'Tebangan': (4.8000, 115.1000),
    'Merapok': (4.8300, 115.3500),
    'Bario Highlands': (3.7300, 115.4700),
    'Ba Kelalan Highlands': (3.9700, 115.6200),
    'Long Pasia': (4.4000, 115.7500),
    'Kelabit Highlands': (3.8000, 115.5000),
    'Long Banga': (3.6000, 115.4000),
    'Long Lellang': (3.7000, 115.3500),
    'Pa Dalih': (3.8500, 115.5200),
    'Pa Ramapuh': (3.9000, 115.5500),
}

BORNEO_LOCATIONS = {**SABAH_LOCATIONS, **SARAWAK_LOCATIONS}

BORNEO_SPACEPORT_CANDIDATES = {
    'Kudat Peninsula, Sabah': (6.8860, 116.8430),
    'Sandakan Coast, Sabah': (5.8400, 118.1200),
    'Tawau Hills, Sabah': (4.2435, 117.8853),
    'Felda Sahabat, Sabah': (5.0620, 119.0810),
    'Dent Haven, Sabah': (5.2680, 119.2620),
    'Lahad Datu, Sabah': (5.0300, 118.3300),
    'Semporna, Sabah': (4.4800, 118.6100),
    'Kinabatangan, Sabah': (5.4000, 117.8000),
    'Ranau, Sabah': (5.9500, 116.6700),
    'Kota Belud, Sabah': (6.3500, 116.4300),
    'Tambunan, Sabah': (5.6700, 116.3600),
    'Keningau, Sabah': (5.3300, 116.1600),
    'Beaufort, Sabah': (5.3500, 115.7500),
    'Kota Marudu, Sabah': (6.5000, 116.7400),
    'Telupid, Sabah': (5.6300, 117.1300),
    'Pamol, Sabah': (5.4800, 118.0800),
    'Silam, Sabah': (4.8700, 118.2300),
    'Kalabakan, Sabah': (4.2200, 117.4800),
    'Maliau Basin, Sabah': (4.7200, 117.5200),
    'Danum Valley, Sabah': (4.9500, 117.7800),
    'Tabin, Sabah': (5.2000, 118.6500),
    'Banggi Island, Sabah': (7.2300, 117.1700),
    'Eastern Sabah Hills, Sabah': (5.0000, 117.8500),
    'Miri Coast, Sarawak': (4.3995, 113.9918),
    'Bintulu Coast, Sarawak': (3.1746, 113.0316),
    'Lawas Coast, Sarawak': (4.8500, 115.4000),
    'Limbang, Sarawak': (4.7500, 115.0000),
    'Mulu Highlands, Sarawak': (4.0450, 114.9380),
    'Marudi, Sarawak': (4.1800, 114.3200),
    'Baram River, Sarawak': (4.3000, 114.2000),
    'Bario Highlands, Sarawak': (3.7300, 115.4700),
    'Ba Kelalan, Sarawak': (3.9700, 115.6200),
    'Samalaju, Sarawak': (3.4500, 113.1200),
    'Tanjung Manis, Sarawak': (2.7100, 111.6200),
    'Mukah, Sarawak': (2.9064, 112.0800),
    'Balingian, Sarawak': (2.9200, 112.5300),
    'Sebauh, Sarawak': (3.1000, 112.9800),
    'Dalat, Sarawak': (2.7500, 111.9700),
    'Kuala Baram, Sarawak': (4.5800, 114.0000),
    'Tanjung Lobang, Sarawak': (4.4295, 113.9618),
}

BORNEO_STATIC_AIRPORTS = {
    'Kota Kinabalu International': (5.9375, 116.0490),
    'Sandakan Airport': (5.9010, 118.0580),
    'Tawau Airport': (4.3133, 117.9183),
    'Kudat Airport': (6.9180, 116.8280),
    'Lahad Datu Airport': (5.0310, 118.3200),
    'Semporna Airport': (4.4800, 118.6100),
    'Keningau Airport': (5.3300, 116.1600),
    'Ranau Airport': (5.9500, 116.6700),
    'Kota Marudu Airport': (6.5000, 116.7400),
    'Pitas Airport': (6.7200, 117.0700),
    'Telupid Airport': (5.6300, 117.1300),
    'Beluran Airport': (5.8800, 117.5600),
    'Kunak Airport': (4.6800, 118.2500),
    'Sipitang Airport': (5.0800, 115.5500),
    'Beaufort Airport': (5.3500, 115.7500),
    'Tenom Airport': (5.1300, 115.9500),
    'Tambunan Airport': (5.6700, 116.3600),
    'Papar Airport': (5.7300, 115.9300),
    'Tuaran Airport': (6.1800, 116.2400),
    'Pulau Sipadan Airport': (4.1140, 118.6250),
    'Kuching International': (1.4843, 110.3469),
    'Miri Airport': (4.3223, 113.9868),
    'Sibu Airport': (2.2586, 111.9661),
    'Bintulu Airport': (3.1232, 113.0195),
    'Limbang Airport': (4.7560, 115.0100),
    'Lawas Airport': (4.8500, 115.4000),
    'Mukah Airport': (2.9064, 112.0800),
    'Sarikei Airport': (2.1160, 111.5360),
    'Kapit Airport': (2.0000, 112.5000),
    'Betong Airport': (1.4100, 111.5300),
    'Sri Aman Airport': (1.2000, 111.5000),
    'Marudi Airport': (4.1800, 114.3200),
    'Bario Airport': (3.7300, 115.4700),
    'Ba Kelalan Airport': (3.9700, 115.6200),
    'Mulu Airport': (4.0450, 114.9380),
    'Long Semadoh Airport': (4.0500, 115.5000),
    'Sundar Airport': (4.7200, 115.5800),
    'Lutong Airport': (4.4700, 114.0200),
    'Tatau Airport': (2.8800, 112.8500),
    'Selangau Airport': (2.5200, 112.3200),
    'Kanowit Airport': (2.1000, 112.1500),
    'Daro Airport': (2.0500, 111.4800),
    'Matu Airport': (2.1000, 111.5300),
    'Dalat Airport': (2.7500, 111.9700),
    'Oya Airport': (2.8500, 111.8500),
    'Lubok Antu Airport': (1.0500, 111.8300),
    'Engkilili Airport': (1.1300, 111.6700),
    'Pusa Airport': (1.4800, 111.3000),
    'Saratok Airport': (1.7400, 111.3200),
    'Sebauh Airport': (3.1000, 112.9800),
    'Balingian Airport': (2.9200, 112.5300),
}

BORNEO_STATIC_SETTLEMENTS = {
    'Kota Kinabalu': {'coords': (5.9804, 116.0735), 'population': 500000},
    'Sandakan': {'coords': (5.8400, 118.1200), 'population': 150000},
    'Tawau': {'coords': (4.2435, 117.8853), 'population': 120000},
    'Lahad Datu': {'coords': (5.0300, 118.3300), 'population': 30000},
    'Kudat': {'coords': (6.8860, 116.8430), 'population': 20000},
    'Semporna': {'coords': (4.4800, 118.6100), 'population': 25000},
    'Keningau': {'coords': (5.3300, 116.1600), 'population': 20000},
    'Ranau': {'coords': (5.9500, 116.6700), 'population': 15000},
    'Kota Marudu': {'coords': (6.5000, 116.7400), 'population': 12000},
    'Beaufort': {'coords': (5.3500, 115.7500), 'population': 10000},
    'Tenom': {'coords': (5.1300, 115.9500), 'population': 8000},
    'Tambunan': {'coords': (5.6700, 116.3600), 'population': 7000},
    'Pitas': {'coords': (6.7200, 117.0700), 'population': 6000},
    'Kunak': {'coords': (4.6800, 118.2500), 'population': 8000},
    'Sipitang': {'coords': (5.0800, 115.5500), 'population': 5000},
    'Papar': {'coords': (5.7300, 115.9300), 'population': 7000},
    'Tuaran': {'coords': (6.1800, 116.2400), 'population': 10000},
    'Penampang': {'coords': (5.9000, 116.0800), 'population': 45000},
    'Putatan': {'coords': (5.8800, 116.0600), 'population': 30000},
    'Telupid': {'coords': (5.6300, 117.1300), 'population': 4000},
    'Beluran': {'coords': (5.8800, 117.5600), 'population': 5000},
    'Kinabatangan': {'coords': (5.4000, 117.8000), 'population': 3000},
    'Kuching': {'coords': (1.5497, 110.3633), 'population': 600000},
    'Miri': {'coords': (4.3995, 113.9918), 'population': 300000},
    'Sibu': {'coords': (2.2871, 111.8301), 'population': 200000},
    'Bintulu': {'coords': (3.1746, 113.0316), 'population': 150000},
    'Limbang': {'coords': (4.7500, 115.0000), 'population': 20000},
    'Lawas': {'coords': (4.8500, 115.4000), 'population': 15000},
    'Mukah': {'coords': (2.9064, 112.0800), 'population': 18000},
    'Sarikei': {'coords': (2.1160, 111.5360), 'population': 25000},
    'Kapit': {'coords': (2.0000, 112.5000), 'population': 15000},
    'Betong': {'coords': (1.4100, 111.5300), 'population': 12000},
    'Sri Aman': {'coords': (1.2000, 111.5000), 'population': 15000},
    'Marudi': {'coords': (4.1800, 114.3200), 'population': 10000},
    'Bario': {'coords': (3.7300, 115.4700), 'population': 1000},
    'Ba Kelalan': {'coords': (3.9700, 115.6200), 'population': 2000},
    'Lutong': {'coords': (4.4700, 114.0200), 'population': 15000},
    'Samalaju': {'coords': (3.4500, 113.1200), 'population': 5000},
    'Sebauh': {'coords': (3.1000, 112.9800), 'population': 8000},
    'Balingian': {'coords': (2.9200, 112.5300), 'population': 5000},
    'Dalat': {'coords': (2.7500, 111.9700), 'population': 8000},
    'Oya': {'coords': (2.8500, 111.8500), 'population': 6000},
    'Tanjung Manis': {'coords': (2.7100, 111.6200), 'population': 7000},
    'Kanowit': {'coords': (2.1000, 112.1500), 'population': 5000},
    'Selangau': {'coords': (2.5200, 112.3200), 'population': 4000},
    'Tatau': {'coords': (2.8800, 112.8500), 'population': 3000},
    'Song': {'coords': (2.0100, 112.5400), 'population': 3000},
    'Belaga': {'coords': (2.7000, 113.7800), 'population': 2000},
}

BORNEO_SPACEPORT_FACILITY_TAGS = {
    'hospital': [('amenity', 'hospital'), ('amenity', 'clinic')],
    'airport': [('aeroway', 'aerodrome'), ('aeroway', 'airport'), ('aeroway', 'heliport')],
    'port': [('harbour', 'yes'), ('amenity', 'ferry_terminal'), ('waterway', 'port')],
    'power_plant': [('power', 'plant'), ('power', 'substation'), ('power', 'generator')],
    'road': [('highway', 'motorway'), ('highway', 'trunk'), ('highway', 'primary')],
    'railway': [('railway', 'rail'), ('railway', 'station')],
    'telecom': [('telecom', 'tower'), ('telecom', 'exchange'), ('man_made', 'tower')],
    'population_center': [('place', 'city'), ('place', 'town'), ('place', 'village')],
}

# ============================================================================
# WEST MALAYSIA DATA
# ============================================================================

WEST_MALAYSIA_LOCATIONS = {
    'Kangar (Perlis)': (6.4414, 100.1986),
    'Arau (Perlis)': (6.4297, 100.2703),
    'Padang Besar (Perlis)': (6.6601, 100.3244),
    'Kuala Perlis': (6.4000, 100.1300),
    'Chuping (Perlis)': (6.5000, 100.2600),
    'Wang Kelian (Perlis)': (6.6800, 100.1700),
    'Alor Setar (Kedah)': (6.1248, 100.3678),
    'Sungai Petani (Kedah)': (5.6470, 100.4877),
    'Kulim (Kedah)': (5.3649, 100.5600),
    'Langkawi (Kedah)': (6.3500, 99.8000),
    'Kuah (Langkawi)': (6.3265, 99.8430),
    'Pantai Cenang (Langkawi)': (6.2930, 99.7250),
    'Padang Matsirat (Langkawi)': (6.3400, 99.7600),
    'Tanjung Rhu (Langkawi)': (6.4400, 99.8500),
    'Teluk Ewa (Langkawi)': (6.4000, 99.9000),
    'Datai Bay (Langkawi)': (6.4700, 99.6800),
    'Baling (Kedah)': (5.6800, 100.9200),
    'Sik (Kedah)': (5.8200, 100.7400),
    'Pendang (Kedah)': (6.0000, 100.4700),
    'Jitra (Kedah)': (6.2683, 100.4225),
    'Yan (Kedah)': (5.8000, 100.3700),
    'Gurun (Kedah)': (5.8200, 100.4700),
    'George Town (Penang)': (5.4141, 100.3288),
    'Bayan Lepas (Penang)': (5.2950, 100.2700),
    'Batu Ferringhi (Penang)': (5.4750, 100.2400),
    'Balik Pulau (Penang)': (5.3500, 100.2300),
    'Butterworth (Penang)': (5.3990, 100.3630),
    'Bukit Mertajam (Penang)': (5.3630, 100.4670),
    'Nibong Tebal (Penang)': (5.1700, 100.4800),
    'Teluk Bahang (Penang)': (5.4600, 100.2100),
    'Gertak Sanggul (Penang)': (5.2700, 100.2000),
    'Batu Maung (Penang)': (5.2800, 100.2900),
    'Ipoh (Perak)': (4.5975, 101.0901),
    'Taiping (Perak)': (4.8500, 100.7333),
    'Teluk Intan (Perak)': (4.0259, 101.0214),
    'Kuala Kangsar (Perak)': (4.7700, 100.9400),
    'Lumut (Perak)': (4.2300, 100.6300),
    'Pangkor Island (Perak)': (4.2200, 100.5600),
    'Sitiawan (Perak)': (4.2200, 100.7000),
    'Batu Gajah (Perak)': (4.4700, 101.0400),
    'Kampar (Perak)': (4.3100, 101.1500),
    'Tapah (Perak)': (4.2000, 101.2600),
    'Tanjung Malim (Perak)': (3.6800, 101.5200),
    'Gerik (Perak)': (5.4300, 101.1300),
    'Segari (Perak)': (4.2800, 100.6000),
    'Pantai Remis (Perak)': (4.4500, 100.6300),
    'Shah Alam (Selangor)': (3.0733, 101.5185),
    'Petaling Jaya (Selangor)': (3.1073, 101.6067),
    'Subang Jaya (Selangor)': (3.0567, 101.5850),
    'Klang (Selangor)': (3.0333, 101.4500),
    'Port Klang (Selangor)': (3.0000, 101.4000),
    'Kuala Selangor (Selangor)': (3.3500, 101.2500),
    'Kuala Kubu Bharu (Selangor)': (3.5600, 101.6400),
    'Rawang (Selangor)': (3.3200, 101.5800),
    'Sepang (Selangor)': (2.7000, 101.7500),
    'Banting (Selangor)': (2.8100, 101.5000),
    'Morib (Selangor)': (2.7500, 101.4400),
    'Tanjung Sepat (Selangor)': (2.6600, 101.5600),
    'Sekinchan (Selangor)': (3.5100, 101.1000),
    'Sabak Bernam (Selangor)': (3.7700, 100.9800),
    'Kajang (Selangor)': (2.9900, 101.7900),
    'Bangi (Selangor)': (2.9500, 101.7800),
    'Putrajaya (FT)': (2.9264, 101.6964),
    'Cyberjaya (Selangor)': (2.9200, 101.6500),
    'Puchong (Selangor)': (3.0000, 101.6200),
    'Batang Kali (Selangor)': (3.4700, 101.6500),
    'Carey Island (Selangor)': (2.8700, 101.3800),
    'Pulau Ketam (Selangor)': (3.0200, 101.2500),
    'Pulau Carey (Selangor)': (2.8800, 101.3500),
    'Pulau Indah (Selangor)': (2.9800, 101.3200),
    'Kuala Langat (Selangor)': (2.8500, 101.4500),
    'Kuala Lumpur City Centre': (3.1390, 101.6869),
    'KLCC (KL)': (3.1578, 101.7120),
    'Bukit Bintang (KL)': (3.1450, 101.7100),
    'Cheras (KL)': (3.0800, 101.7300),
    'Kepong (KL)': (3.2100, 101.6400),
    'Sungai Besi (KL)': (3.0600, 101.7000),
    'Batu Caves (Selangor)': (3.2379, 101.6840),
    'Seremban (N. Sembilan)': (2.7297, 101.9381),
    'Port Dickson (N. Sembilan)': (2.5228, 101.7967),
    'Nilai (N. Sembilan)': (2.8200, 101.8000),
    'Bahau (N. Sembilan)': (2.8000, 102.4000),
    'Tampin (N. Sembilan)': (2.4700, 102.2300),
    'Kuala Pilah (N. Sembilan)': (2.7400, 102.2500),
    'Rembau (N. Sembilan)': (2.5900, 102.0900),
    'Gemas (N. Sembilan)': (2.5800, 102.6100),
    'Lukut (N. Sembilan)': (2.5800, 101.8300),
    'Tanjung Tuan (N. Sembilan)': (2.4000, 101.8500),
    'Blue Lagoon (N. Sembilan)': (2.4800, 101.8300),
    'Linggi (N. Sembilan)': (2.4800, 102.0000),
    'Melaka City (Melaka)': (2.1896, 102.2501),
    'Ayer Keroh (Melaka)': (2.2700, 102.2900),
    'Alor Gajah (Melaka)': (2.3800, 102.2100),
    'Jasin (Melaka)': (2.3100, 102.4300),
    'Masjid Tanah (Melaka)': (2.3500, 102.1100),
    'Merlimau (Melaka)': (2.1400, 102.4300),
    'Tanjung Kling (Melaka)': (2.2200, 102.1600),
    'Tanjung Bidara (Melaka)': (2.2800, 102.0900),
    'Pengkalan Balak (Melaka)': (2.3200, 102.0800),
    'Kuala Sungai Baru (Melaka)': (2.3500, 102.0400),
    'Johor Bahru (Johor)': (1.4927, 103.7414),
    'Iskandar Puteri (Johor)': (1.4300, 103.6300),
    'Kulai (Johor)': (1.6600, 103.6000),
    'Skudai (Johor)': (1.5400, 103.6700),
    'Senai (Johor)': (1.6200, 103.6600),
    'Pasir Gudang (Johor)': (1.4700, 103.9000),
    'Pengerang (Johor)': (1.3600, 104.1700),
    'Kota Tinggi (Johor)': (1.7300, 103.9000),
    'Mersing (Johor)': (2.4300, 103.8300),
    'Batu Pahat (Johor)': (1.8500, 102.9300),
    'Muar (Johor)': (2.0500, 102.5700),
    'Segamat (Johor)': (2.5100, 102.8100),
    'Kluang (Johor)': (2.0300, 103.3200),
    'Pontian (Johor)': (1.4800, 103.3800),
    'Desaru (Johor)': (1.5500, 104.2600),
    'Endau (Johor)': (2.6500, 103.6200),
    'Pulau Aur (Johor)': (2.4500, 104.5200),
    'Pulau Pemanggil (Johor)': (2.5800, 104.3300),
    'Pulau Sibu (Johor)': (2.2000, 104.1000),
    'Pulau Tinggi (Johor)': (2.3000, 104.1200),
    'Pulau Rawa (Johor)': (2.5300, 103.9700),
    'Pulau Kukup (Johor)': (1.3100, 103.4200),
    'Tanjung Piai (Johor)': (1.2700, 103.5100),
    'Gelang Patah (Johor)': (1.4500, 103.5900),
    'Kukup (Johor)': (1.3200, 103.4300),
    'Labis (Johor)': (2.3800, 103.0200),
    'Yong Peng (Johor)': (2.0100, 103.0600),
    'Ayer Hitam (Johor)': (1.9200, 103.1800),
    'Kota Bharu (Kelantan)': (6.1256, 102.2386),
    'Kubang Kerian (Kelantan)': (6.1000, 102.2800),
    'Pasir Puteh (Kelantan)': (5.8300, 102.4000),
    'Pasir Mas (Kelantan)': (6.0500, 102.1400),
    'Tumpat (Kelantan)': (6.2000, 102.1700),
    'Bachok (Kelantan)': (6.0700, 102.4000),
    'Tanah Merah (Kelantan)': (5.8000, 102.1500),
    'Machang (Kelantan)': (5.7700, 102.2100),
    'Kuala Krai (Kelantan)': (5.5300, 102.2000),
    'Gua Musang (Kelantan)': (4.8800, 101.9600),
    'Jeli (Kelantan)': (5.7000, 101.8400),
    'Tok Bali (Kelantan)': (5.8200, 102.4500),
    'Pantai Cahaya Bulan (Kelantan)': (6.1300, 102.2900),
    'Kuala Terengganu (Terengganu)': (5.3303, 103.1408),
    'Kuala Nerus (Terengganu)': (5.3800, 103.0800),
    'Kemaman (Terengganu)': (4.2300, 103.4200),
    'Chukai (Terengganu)': (4.2200, 103.4200),
    'Kerteh (Terengganu)': (4.5200, 103.4500),
    'Paka (Terengganu)': (4.6400, 103.4400),
    'Dungun (Terengganu)': (4.7700, 103.4200),
    'Marang (Terengganu)': (5.2000, 103.2100),
    'Kuala Berang (Terengganu)': (5.0700, 102.9500),
    'Jerteh (Terengganu)': (5.7400, 102.5100),
    'Besut (Terengganu)': (5.7300, 102.5600),
    'Setiu (Terengganu)': (5.5800, 102.8000),
    'Kuala Besut (Terengganu)': (5.8300, 102.5600),
    'Pulau Perhentian (Terengganu)': (5.9100, 102.7400),
    'Pulau Redang (Terengganu)': (5.7800, 103.0000),
    'Pulau Kapas (Terengganu)': (5.2200, 103.2600),
    'Pulau Tenggol (Terengganu)': (4.8000, 103.6800),
    'Pulau Lang Tengah (Terengganu)': (5.7800, 102.8900),
    'Kijal (Terengganu)': (4.3600, 103.5000),
    'Kuantan (Pahang)': (3.8077, 103.3260),
    'Pekan (Pahang)': (3.4900, 103.3900),
    'Temerloh (Pahang)': (3.4500, 102.4200),
    'Bentong (Pahang)': (3.5200, 101.9100),
    'Raub (Pahang)': (3.7900, 101.8600),
    'Kuala Lipis (Pahang)': (4.1800, 102.0500),
    'Jerantut (Pahang)': (3.9400, 102.3600),
    'Mentakab (Pahang)': (3.4900, 102.3500),
    'Cameron Highlands (Pahang)': (4.4700, 101.3800),
    'Genting Highlands (Pahang)': (3.4200, 101.7900),
    "Fraser's Hill (Pahang)": (3.7100, 101.7400),
    'Tioman Island (Pahang)': (2.7900, 104.1700),
    'Cherating (Pahang)': (4.1300, 103.3900),
    'Balok (Pahang)': (3.9500, 103.3700),
    'Beserah (Pahang)': (3.8800, 103.3600),
    'Sungai Lembing (Pahang)': (3.9200, 103.0300),
    'Gambang (Pahang)': (3.7100, 103.0900),
    'Maran (Pahang)': (3.5800, 102.7700),
    'Kuala Rompin (Pahang)': (2.8200, 103.4800),
    'Nenasi (Pahang)': (2.9900, 103.4900),
    'Gebeng (Pahang)': (3.9600, 103.3700),
    'Bukit Ibam (Pahang)': (3.3000, 102.8500),
    'Lanchang (Pahang)': (3.5000, 102.2000),
    'Janda Baik (Pahang)': (3.3200, 101.8800),
}

WEST_MALAYSIA_SPACEPORT_CANDIDATES = {
    'Pengerang, Johor': (1.3600, 104.1700),
    'Desaru Coast, Johor': (1.5500, 104.2600),
    'Kota Tinggi, Johor': (1.7300, 103.9000),
    'Mersing, Johor': (2.4300, 103.8300),
    'Endau, Johor': (2.6500, 103.6200),
    'Pulau Aur, Johor': (2.4500, 104.5200),
    'Pulau Pemanggil, Johor': (2.5800, 104.3300),
    'Pulau Sibu, Johor': (2.2000, 104.1000),
    'Pulau Tinggi, Johor': (2.3000, 104.1200),
    'Pulau Rawa, Johor': (2.5300, 103.9700),
    'Tanjung Piai, Johor': (1.2700, 103.5100),
    'Pulau Kukup, Johor': (1.3100, 103.4200),
    'Kukup, Johor': (1.3200, 103.4300),
    'Pontian Coast, Johor': (1.4800, 103.3800),
    'Labis, Johor': (2.3800, 103.0200),
    'Ayer Hitam, Johor': (1.9200, 103.1800),
    'Pulau Tioman, Pahang': (2.7900, 104.1700),
    'Kuala Rompin, Pahang': (2.8200, 103.4800),
    'Nenasi, Pahang': (2.9900, 103.4900),
    'Pekan, Pahang': (3.4900, 103.3900),
    'Cherating, Pahang': (4.1300, 103.3900),
    'Balok, Pahang': (3.9500, 103.3700),
    'Beserah, Pahang': (3.8800, 103.3600),
    'Gebeng, Pahang': (3.9600, 103.3700),
    'Bukit Ibam, Pahang': (3.3000, 102.8500),
    'Lanchang, Pahang': (3.5000, 102.2000),
    'Kerteh, Terengganu': (4.5200, 103.4500),
    'Paka, Terengganu': (4.6400, 103.4400),
    'Kijal, Terengganu': (4.3600, 103.5000),
    'Kuala Kemaman, Terengganu': (4.2300, 103.4200),
    'Pulau Tenggol, Terengganu': (4.8000, 103.6800),
    'Pulau Redang, Terengganu': (5.7800, 103.0000),
    'Pulau Perhentian, Terengganu': (5.9100, 102.7400),
    'Pulau Kapas, Terengganu': (5.2200, 103.2600),
    'Pulau Lang Tengah, Terengganu': (5.7800, 102.8900),
    'Setiu, Terengganu': (5.5800, 102.8000),
    'Kuala Besut, Terengganu': (5.8300, 102.5600),
    'Besut, Terengganu': (5.7300, 102.5600),
    'Kuala Berang, Terengganu': (5.0700, 102.9500),
    'Dungun, Terengganu': (4.7700, 103.4200),
    'Marang, Terengganu': (5.2000, 103.2100),
    'Tok Bali, Kelantan': (5.8200, 102.4500),
    'Bachok, Kelantan': (6.0700, 102.4000),
    'Pasir Puteh, Kelantan': (5.8300, 102.4000),
    'Gua Musang, Kelantan': (4.8800, 101.9600),
    'Dabong, Kelantan': (5.3800, 102.0100),
    'Kuala Krai, Kelantan': (5.5300, 102.2000),
    'Langkawi (Kedah)': (6.3500, 99.8000),
    'Teluk Ewa, Langkawi': (6.4000, 99.9000),
    'Pantai Cenang, Langkawi': (6.2930, 99.7250),
    'Padang Matsirat, Langkawi': (6.3400, 99.7600),
    'Datai Bay, Langkawi': (6.4700, 99.6800),
    'Kuala Perlis': (6.4000, 100.1300),
    'Padang Besar (Perlis)': (6.6601, 100.3244),
    'Chuping (Perlis)': (6.5000, 100.2600),
    'Pangkor Island (Perak)': (4.2200, 100.5600),
    'Pulau Pangkor (Perak)': (4.2200, 100.5600),
    'Pulau Sembilan (Perak)': (4.0800, 100.5300),
    'Pulau Jarak (Perak)': (4.0800, 100.2800),
    'Segari (Perak)': (4.2800, 100.6000),
    'Pantai Remis (Perak)': (4.4500, 100.6300),
    'Pulau Ketam (Selangor)': (3.0200, 101.2500),
    'Pulau Carey (Selangor)': (2.8800, 101.3500),
    'Pulau Indah (Selangor)': (2.9800, 101.3200),
    'Morib (Selangor)': (2.7500, 101.4400),
    'Tanjung Sepat (Selangor)': (2.6600, 101.5600),
    'Sekinchan Coast (Selangor)': (3.5000, 101.0800),
    'Sungai Besar (Selangor)': (3.6700, 100.9800),
    'Sabak Bernam (Selangor)': (3.7700, 100.9800),
    'Banting (Selangor)': (2.8100, 101.5000),
    'Kuala Langat (Selangor)': (2.8500, 101.4500),
    'Carey Island (Selangor)': (2.8700, 101.3800),
    'Tanjung Bidara (Melaka)': (2.2800, 102.0900),
    'Pengkalan Balak (Melaka)': (2.3200, 102.0800),
    'Kuala Sungai Baru (Melaka)': (2.3500, 102.0400),
    'Port Dickson (N. Sembilan)': (2.5228, 101.7967),
    'Tanjung Tuan (N. Sembilan)': (2.4000, 101.8500),
    'Blue Lagoon (N. Sembilan)': (2.4800, 101.8300),
    'Linggi (N. Sembilan)': (2.4800, 102.0000),
    'Gemas (N. Sembilan)': (2.5800, 102.6100),
    'Teluk Bahang (Penang)': (5.4600, 100.2100),
    'Gertak Sanggul (Penang)': (5.2700, 100.2000),
    'Batu Maung (Penang)': (5.2800, 100.2900),
    'Balik Pulau (Penang)': (5.3500, 100.2300),
    'Pulau Betong (Penang)': (5.3300, 100.2000),
}

WEST_STATIC_AIRPORTS = {
    'Langkawi International': (6.3297, 99.7287),
    'Sultan Abdul Halim (Alor Setar)': (6.1897, 100.3982),
    'Kangar Airport': (6.4500, 100.2000),
    'Penang International': (5.2972, 100.2768),
    'Butterworth Air Base': (5.4000, 100.3700),
    'Sultan Azlan Shah (Ipoh)': (4.5679, 101.0920),
    'Taiping Airport': (4.8667, 100.7167),
    'Pulau Pangkor Airstrip': (4.2200, 100.5500),
    'Lumut RMAF Base': (4.2300, 100.6200),
    'Sultan Abdul Aziz Shah (Subang)': (3.1306, 101.5493),
    'KLIA (Sepang)': (2.7456, 101.7099),
    'KLIA2 (Sepang)': (2.7430, 101.6860),
    'Melaka International': (2.2633, 102.2517),
    'Senai International (JB)': (1.6411, 103.6696),
    'Batu Pahat Airport': (1.8500, 102.9300),
    'Mersing Airport': (2.4300, 103.8300),
    'Sultan Ahmad Shah (Kuantan)': (3.7753, 103.2090),
    'Tioman Airport': (2.8183, 104.1600),
    'Sultan Mahmud (K. Terengganu)': (5.3825, 103.1033),
    'Kerteh Airport': (4.5200, 103.4500),
    'Sultan Ismail Petra (Kota Bharu)': (6.1664, 102.2924),
    'Tok Bali Airstrip': (5.8200, 102.4500),
    'Gua Musang Airstrip': (4.8800, 101.9600),
}

WEST_STATIC_SETTLEMENTS = {
    'Kangar': {'coords': (6.4414, 100.1986), 'population': 50000},
    'Arau': {'coords': (6.4297, 100.2703), 'population': 30000},
    'Alor Setar': {'coords': (6.1248, 100.3678), 'population': 400000},
    'Sungai Petani': {'coords': (5.6470, 100.4877), 'population': 300000},
    'Kulim': {'coords': (5.3649, 100.5600), 'population': 150000},
    'Langkawi': {'coords': (6.3500, 99.8000), 'population': 90000},
    'Baling': {'coords': (5.6800, 100.9200), 'population': 30000},
    'George Town': {'coords': (5.4141, 100.3288), 'population': 700000},
    'Butterworth': {'coords': (5.3990, 100.3630), 'population': 200000},
    'Bukit Mertajam': {'coords': (5.3630, 100.4670), 'population': 200000},
    'Bayan Lepas': {'coords': (5.2950, 100.2700), 'population': 150000},
    'Ipoh': {'coords': (4.5975, 101.0901), 'population': 750000},
    'Taiping': {'coords': (4.8500, 100.7333), 'population': 200000},
    'Teluk Intan': {'coords': (4.0259, 101.0214), 'population': 100000},
    'Kuala Kangsar': {'coords': (4.7700, 100.9400), 'population': 50000},
    'Lumut': {'coords': (4.2300, 100.6300), 'population': 40000},
    'Sitiawan': {'coords': (4.2200, 100.7000), 'population': 150000},
    'Shah Alam': {'coords': (3.0733, 101.5185), 'population': 700000},
    'Petaling Jaya': {'coords': (3.1073, 101.6067), 'population': 800000},
    'Subang Jaya': {'coords': (3.0567, 101.5850), 'population': 700000},
    'Klang': {'coords': (3.0333, 101.4500), 'population': 900000},
    'Kuala Lumpur': {'coords': (3.1390, 101.6869), 'population': 1800000},
    'Putrajaya': {'coords': (2.9264, 101.6964), 'population': 100000},
    'Cyberjaya': {'coords': (2.9200, 101.6500), 'population': 100000},
    'Sepang': {'coords': (2.7000, 101.7500), 'population': 90000},
    'Kajang': {'coords': (2.9900, 101.7900), 'population': 300000},
    'Bangi': {'coords': (2.9500, 101.7800), 'population': 200000},
    'Kuala Selangor': {'coords': (3.3500, 101.2500), 'population': 40000},
    'Kuala Kubu Bharu': {'coords': (3.5600, 101.6400), 'population': 30000},
    'Rawang': {'coords': (3.3200, 101.5800), 'population': 200000},
    'Banting': {'coords': (2.8100, 101.5000), 'population': 40000},
    'Sekinchan': {'coords': (3.5100, 101.1000), 'population': 15000},
    'Sabak Bernam': {'coords': (3.7700, 100.9800), 'population': 30000},
    'Seremban': {'coords': (2.7297, 101.9381), 'population': 500000},
    'Port Dickson': {'coords': (2.5228, 101.7967), 'population': 100000},
    'Nilai': {'coords': (2.8200, 101.8000), 'population': 100000},
    'Bahau': {'coords': (2.8000, 102.4000), 'population': 30000},
    'Tampin': {'coords': (2.4700, 102.2300), 'population': 30000},
    'Kuala Pilah': {'coords': (2.7400, 102.2500), 'population': 20000},
    'Melaka City': {'coords': (2.1896, 102.2501), 'population': 500000},
    'Ayer Keroh': {'coords': (2.2700, 102.2900), 'population': 60000},
    'Alor Gajah': {'coords': (2.3800, 102.2100), 'population': 40000},
    'Jasin': {'coords': (2.3100, 102.4300), 'population': 30000},
    'Johor Bahru': {'coords': (1.4927, 103.7414), 'population': 1500000},
    'Iskandar Puteri': {'coords': (1.4300, 103.6300), 'population': 500000},
    'Kulai': {'coords': (1.6600, 103.6000), 'population': 200000},
    'Pasir Gudang': {'coords': (1.4700, 103.9000), 'population': 200000},
    'Pengerang': {'coords': (1.3600, 104.1700), 'population': 30000},
    'Kota Tinggi': {'coords': (1.7300, 103.9000), 'population': 50000},
    'Mersing': {'coords': (2.4300, 103.8300), 'population': 30000},
    'Batu Pahat': {'coords': (1.8500, 102.9300), 'population': 300000},
    'Muar': {'coords': (2.0500, 102.5700), 'population': 200000},
    'Segamat': {'coords': (2.5100, 102.8100), 'population': 80000},
    'Kluang': {'coords': (2.0300, 103.3200), 'population': 150000},
    'Pontian': {'coords': (1.4800, 103.3800), 'population': 50000},
    'Desaru': {'coords': (1.5500, 104.2600), 'population': 15000},
    'Kota Bharu': {'coords': (6.1256, 102.2386), 'population': 500000},
    'Kubang Kerian': {'coords': (6.1000, 102.2800), 'population': 50000},
    'Pasir Puteh': {'coords': (5.8300, 102.4000), 'population': 30000},
    'Pasir Mas': {'coords': (6.0500, 102.1400), 'population': 40000},
    'Tumpat': {'coords': (6.2000, 102.1700), 'population': 30000},
    'Bachok': {'coords': (6.0700, 102.4000), 'population': 20000},
    'Kuala Krai': {'coords': (5.5300, 102.2000), 'population': 20000},
    'Gua Musang': {'coords': (4.8800, 101.9600), 'population': 15000},
    'Kuala Terengganu': {'coords': (5.3303, 103.1408), 'population': 400000},
    'Kemaman': {'coords': (4.2300, 103.4200), 'population': 60000},
    'Chukai': {'coords': (4.2200, 103.4200), 'population': 40000},
    'Kerteh': {'coords': (4.5200, 103.4500), 'population': 20000},
    'Paka': {'coords': (4.6400, 103.4400), 'population': 15000},
    'Dungun': {'coords': (4.7700, 103.4200), 'population': 40000},
    'Marang': {'coords': (5.2000, 103.2100), 'population': 20000},
    'Kuala Berang': {'coords': (5.0700, 102.9500), 'population': 15000},
    'Jerteh': {'coords': (5.7400, 102.5100), 'population': 30000},
    'Besut': {'coords': (5.7300, 102.5600), 'population': 25000},
    'Setiu': {'coords': (5.5800, 102.8000), 'population': 15000},
    'Kuantan': {'coords': (3.8077, 103.3260), 'population': 600000},
    'Pekan': {'coords': (3.4900, 103.3900), 'population': 50000},
    'Temerloh': {'coords': (3.4500, 102.4200), 'population': 100000},
    'Bentong': {'coords': (3.5200, 101.9100), 'population': 60000},
    'Raub': {'coords': (3.7900, 101.8600), 'population': 50000},
    'Kuala Lipis': {'coords': (4.1800, 102.0500), 'population': 20000},
    'Jerantut': {'coords': (3.9400, 102.3600), 'population': 30000},
    'Mentakab': {'coords': (3.4900, 102.3500), 'population': 40000},
    'Cameron Highlands': {'coords': (4.4700, 101.3800), 'population': 40000},
    'Genting Highlands': {'coords': (3.4200, 101.7900), 'population': 30000},
    'Kuala Rompin': {'coords': (2.8200, 103.4800), 'population': 20000},
    'Cherating': {'coords': (4.1300, 103.3900), 'population': 10000},
    'Balok': {'coords': (3.9500, 103.3700), 'population': 15000},
    'Gambang': {'coords': (3.7100, 103.0900), 'population': 20000},
    'Maran': {'coords': (3.5800, 102.7700), 'population': 15000},
}

WEST_SPACEPORT_FACILITY_TAGS = {
    'hospital': [('amenity', 'hospital'), ('amenity', 'clinic')],
    'airport': [('aeroway', 'aerodrome'), ('aeroway', 'airport'), ('aeroway', 'heliport')],
    'port': [('harbour', 'yes'), ('amenity', 'ferry_terminal'), ('waterway', 'port')],
    'power_plant': [('power', 'plant'), ('power', 'substation'), ('power', 'generator')],
    'road': [('highway', 'motorway'), ('highway', 'trunk'), ('highway', 'primary')],
    'railway': [('railway', 'rail'), ('railway', 'station')],
    'telecom': [('telecom', 'tower'), ('telecom', 'exchange'), ('man_made', 'tower')],
    'population_center': [('place', 'city'), ('place', 'town'), ('place', 'village')],
}

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Location:
    lat: float
    lon: float
    name: str = ""
    properties: Dict = field(default_factory=dict)

@dataclass
class AnalysisStep:
    step_number: int
    name: str
    description: str
    status: str = "pending"
    result: Any = None
    execution_time: float = 0.0
    reasoning: str = ""

@dataclass
class AnalysisResult:
    query: str
    steps: List[AnalysisStep] = field(default_factory=list)
    final_result: Any = None
    total_time: float = 0.0
    timestamp: str = ""
    success: bool = False

@dataclass
class MemoryEntry:
    query: str
    query_embedding: List[float] = field(default_factory=list)
    result_summary: str = ""
    success: bool = False
    execution_time: float = 0.0
    timestamp: str = ""
    parameters_used: Dict = field(default_factory=dict)

# ============================================================================
# MEMORY REPOSITORY
# ============================================================================

class MemoryRepository:
    def __init__(self, db_path: str = "spaceportvbase_memory.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                query_hash TEXT NOT NULL,
                region TEXT DEFAULT 'unknown',
                result_summary TEXT,
                success INTEGER,
                execution_time REAL,
                parameters TEXT,
                timestamp TEXT,
                embedding BLOB
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_type TEXT NOT NULL,
                parameter_name TEXT NOT NULL,
                optimal_value TEXT,
                success_rate REAL,
                usage_count INTEGER DEFAULT 1,
                last_updated TEXT
            )
        """)
        conn.commit()
        conn.close()

    def store_analysis(self, entry: MemoryEntry, region: str = "unknown"):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query_hash = hashlib.md5(entry.query.lower().encode()).hexdigest()
        cursor.execute("""
            INSERT INTO analysis_memory
            (query, query_hash, region, result_summary, success, execution_time,
             parameters, timestamp, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.query, query_hash, region, entry.result_summary,
            1 if entry.success else 0, entry.execution_time,
            json.dumps(entry.parameters_used), entry.timestamp,
            pickle.dumps(entry.query_embedding)
        ))
        conn.commit()
        conn.close()

    def get_all_analyses(self, limit: int = 20, region: Optional[str] = None) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if region:
            cursor.execute(
                "SELECT * FROM analysis_memory WHERE region = ? ORDER BY timestamp DESC LIMIT ?",
                (region, limit))
        else:
            cursor.execute(
                "SELECT * FROM analysis_memory ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                'query': row[1],
                'region': row[3],
                'result_summary': row[4],
                'success': bool(row[5]),
                'execution_time': row[6],
                'parameters': json.loads(row[7]) if row[7] else {},
                'timestamp': row[8]
            })
        conn.close()
        return results

    def find_similar_analyses(self, query: str, limit: int = 5) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analysis_memory ORDER BY timestamp DESC LIMIT 100")
        rows = cursor.fetchall()
        if not query or not query.strip():
            conn.close()
            return []
        keywords = query.lower().split()
        results = []
        for row in rows:
            stored_query = row[1].lower()
            match_score = sum(1 for kw in keywords if kw in stored_query)
            if match_score > 0:
                results.append({
                    'query': row[1],
                    'region': row[3],
                    'result_summary': row[4],
                    'success': bool(row[5]),
                    'execution_time': row[6],
                    'parameters': json.loads(row[7]) if row[7] else {},
                    'timestamp': row[8],
                    'match_score': match_score
                })
        conn.close()
        results.sort(key=lambda x: x['match_score'], reverse=True)
        return results[:limit]

    def get_learned_parameter(self, analysis_type: str, parameter_name: str) -> Optional[str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT optimal_value, success_rate FROM learned_parameters
            WHERE analysis_type = ? AND parameter_name = ?
            ORDER BY success_rate DESC LIMIT 1
        """, (analysis_type, parameter_name))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def update_learned_parameter(self, analysis_type: str, parameter_name: str,
                                  value: str, success: bool):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, success_rate, usage_count FROM learned_parameters
            WHERE analysis_type = ? AND parameter_name = ? AND optimal_value = ?
        """, (analysis_type, parameter_name, value))
        row = cursor.fetchone()
        if row:
            new_count = row[2] + 1
            new_rate = ((row[1] * row[2]) + (1 if success else 0)) / new_count
            cursor.execute("""
                UPDATE learned_parameters
                SET success_rate = ?, usage_count = ?, last_updated = ?
                WHERE id = ?
            """, (new_rate, new_count, datetime.now().isoformat(), row[0]))
        else:
            cursor.execute("""
                INSERT INTO learned_parameters
                (analysis_type, parameter_name, optimal_value, success_rate,
                 usage_count, last_updated)
                VALUES (?, ?, ?, ?, 1, ?)
            """, (analysis_type, parameter_name, value,
                  1.0 if success else 0.0, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def get_analysis_stats(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM analysis_memory")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM analysis_memory WHERE success = 1")
        successful = cursor.fetchone()[0]
        cursor.execute("SELECT AVG(execution_time) FROM analysis_memory")
        avg_time = cursor.fetchone()[0] or 0
        conn.close()
        return {
            'total_analyses': total,
            'successful_analyses': successful,
            'success_rate': successful / total if total > 0 else 0,
            'avg_execution_time': avg_time
        }

# ============================================================================
# STRATEGY BASE CLASSES
# ============================================================================

class AnalysisStrategy(ABC):
    @abstractmethod
    def analyse(self, location: Location, params: Dict) -> Dict:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

class RateLimiter:
    def __init__(self, calls_per_second: float = 0.5):
        self.calls_per_second = calls_per_second
        self.last_call = 0

    def wait(self):
        now = time.time()
        time_since_last = now - self.last_call
        min_interval = 1.0 / self.calls_per_second
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        self.last_call = time.time()

# ============================================================================
# BORNEO STRATEGIES
# ============================================================================

class BorneoSuitabilityStrategy(AnalysisStrategy):
    def get_name(self) -> str:
        return "Spaceport Suitability Analysis (Borneo HYBRID)"

    def _get_elevation_quick(self, location: Location) -> tuple:
        try:
            elevation_url = f"https://api.open-elevation.com/api/v1/lookup?locations={location.lat},{location.lon}"
            response = requests.get(elevation_url, timeout=3)
            data = response.json()
            elev = data['results'][0]['elevation']
            if 50 <= elev <= 200:
                return 5.0, elev, 'Live Elevation API'
            elif 200 < elev <= 500:
                return 4.5, elev, 'Live Elevation API'
            elif 20 <= elev < 50:
                return 4.0, elev, 'Live Elevation API'
            elif 0 <= elev < 20:
                return 2.0, elev, 'Live Elevation API'
            else:
                return 3.0, elev, 'Live Elevation API'
        except Exception:
            lat, lon = location.lat, location.lon
            if lat > 5.8 and lat < 6.2 and lon > 116.4 and lon < 116.8:
                return 4.5, 1500, 'Fallback: Kinabalu region'
            elif lat > 4.5 and lon > 117.5:
                return 3.5, 300, 'Fallback: E. Sabah hills'
            elif lat > 2.5 and lon > 114.0 and lon < 115.5:
                return 3.5, 200, 'Fallback: Sarawak interior'
            else:
                return 3.0, 50, 'Fallback: Lowland area'

    def _get_weather(self, location: Location) -> Optional[Dict]:
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": location.lat,
                "longitude": location.lon,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,"
                           "wind_direction_10m,wind_gusts_10m",
                "wind_speed_unit": "ms",
                "timezone": "auto",
            }
            r = requests.get(url, params=params, timeout=4)
            data = r.json()
            cur = data.get("current", {})
            return {
                "temperature_c": cur.get("temperature_2m"),
                "humidity_pct": cur.get("relative_humidity_2m"),
                "wind_speed_ms": cur.get("wind_speed_10m"),
                "wind_direction_deg": cur.get("wind_direction_10m"),
                "wind_gust_ms": cur.get("wind_gusts_10m"),
                "source": "Open-Meteo (Live)",
                "time": cur.get("time"),
            }
        except Exception:
            return None

    def _score_wind(self, wind_speed_ms, wind_gust_ms) -> tuple:
        if wind_speed_ms is None:
            return 3.0, "Unknown", "Weather unavailable — neutral score"
        if wind_speed_ms < 4:
            return 5.0, "Excellent", f"Calm ({wind_speed_ms:.1f} m/s) — ideal for launches"
        elif wind_speed_ms < 6:
            return 4.5, "Good", f"Light breeze ({wind_speed_ms:.1f} m/s) — very suitable"
        elif wind_speed_ms < 8:
            return 4.0, "Good", f"Moderate wind ({wind_speed_ms:.1f} m/s) — manageable"
        elif wind_speed_ms < 12:
            return 3.0, "Moderate", f"Fairly windy ({wind_speed_ms:.1f} m/s) — schedule around it"
        else:
            return 2.0, "Poor", f"High wind ({wind_speed_ms:.1f} m/s) — challenging launches"

    def _geographic_score_coastal(self, location: Location) -> tuple:
        lat, lon = location.lat, location.lon
        if lon > 117.5:
            return 5.0, 0, 'Geographic: East coast'
        elif lon > 116.5:
            return 4.0, 10, 'Geographic: Near coast'
        elif lon > 115.5:
            return 3.5, 20, 'Geographic: Coastal'
        elif lon > 114.5:
            return 3.0, 30, 'Geographic: Inland'
        else:
            return 2.0, 50, 'Geographic: Interior'

    def _geographic_score_population(self, location: Location) -> tuple:
        lat, lon = location.lat, location.lon
        min_dist = 999
        for name, data in BORNEO_STATIC_SETTLEMENTS.items():
            s_lat, s_lon = data['coords']
            dist = self._haversine(lat, lon, s_lat, s_lon)
            min_dist = min(min_dist, dist)
        if min_dist > 80:
            return 5.0, 0, 'Geographic: Remote'
        elif min_dist > 50:
            return 4.0, 1, 'Geographic: Rural'
        elif min_dist > 30:
            return 3.0, 2, 'Geographic: Semi-rural'
        elif min_dist > 15:
            return 2.0, 5, 'Geographic: Near town'
        else:
            return 1.0, 10, 'Geographic: Near city'

    def _geographic_score_infrastructure(self, location: Location) -> tuple:
        lat, lon = location.lat, location.lon
        min_dist = 999
        for name, coords in BORNEO_STATIC_AIRPORTS.items():
            a_lat, a_lon = coords
            dist = self._haversine(lat, lon, a_lat, a_lon)
            min_dist = min(min_dist, dist)
        details = {
            'airports': 1 if min_dist < 60 else 0,
            'major_roads': 2 if min_dist < 30 else 0,
            'ports': 0,
            'power_facilities': 0
        }
        if min_dist < 30:
            return 4.5, details, 'Geographic: Near airport'
        elif min_dist < 60:
            return 3.5, details, 'Geographic: Airport nearby'
        elif min_dist < 100:
            return 2.5, details, 'Geographic: Some access'
        else:
            return 1.5, details, 'Geographic: Remote'

    def _geographic_score_land(self, location: Location) -> tuple:
        lat, lon = location.lat, location.lon
        min_dist = 999
        for name, data in BORNEO_STATIC_SETTLEMENTS.items():
            s_lat, s_lon = data['coords']
            dist = self._haversine(lat, lon, s_lat, s_lon)
            min_dist = min(min_dist, dist)
        details = {
            'forest_areas': 30 if min_dist > 50 else 10,
            'developed_areas': 2 if min_dist > 50 else 10,
            'agriculture': 5
        }
        if min_dist > 80:
            return 5.0, details, 'Geographic: Abundant land'
        elif min_dist > 50:
            return 4.0, details, 'Geographic: Good land'
        elif min_dist > 30:
            return 3.0, details, 'Geographic: Moderate land'
        elif min_dist > 15:
            return 2.0, details, 'Geographic: Limited land'
        else:
            return 1.0, details, 'Geographic: Scarce land'

    def _geographic_score_flood(self, elevation_m: float) -> tuple:
        if elevation_m > 100:
            return 5.0, 'Low'
        elif elevation_m > 50:
            return 4.0, 'Low'
        elif elevation_m > 20:
            return 3.0, 'Moderate'
        else:
            return 1.5, 'High'

    def _score_latitudinal_advantage(self, lat: float) -> float:
        abs_lat = abs(lat)
        if abs_lat <= 1:
            return 5.0
        elif abs_lat <= 3:
            return 4.5
        elif abs_lat <= 5:
            return 4.0
        elif abs_lat <= 7:
            return 3.0
        elif abs_lat <= 10:
            return 2.0
        else:
            return 1.0

    def _haversine(self, lat1, lon1, lat2, lon2) -> float:
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2
             + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
             * math.sin(dlon / 2) ** 2)
        return R * 2 * math.asin(min(1, math.sqrt(a)))

    def _try_osm_in_background(self, location: Location, radius: int) -> Optional[Dict]:
        try:
            overpass_url = "https://overpass-api.de/api/interpreter"
            results = {}
            query = f"""
            [out:json][timeout:5];
            (
              node["aeroway"="aerodrome"](around:{radius},{location.lat},{location.lon});
              way["aeroway"="aerodrome"](around:{radius},{location.lat},{location.lon});
            );
            out count;
            """
            response = requests.post(overpass_url, data={'data': query}, timeout=5)
            data = response.json()
            results['airport_count'] = len(data.get('elements', []))
            query = f"""
            [out:json][timeout:5];
            (node["place"~"city|town|village"](around:{radius},{location.lat},{location.lon}););
            out count;
            """
            response = requests.post(overpass_url, data={'data': query}, timeout=5)
            data = response.json()
            results['settlement_count'] = len(data.get('elements', []))
            query = f"""
            [out:json][timeout:5];
            (way["highway"~"motorway|trunk|primary"](around:{radius},{location.lat},{location.lon}););
            out count;
            """
            response = requests.post(overpass_url, data={'data': query}, timeout=5)
            data = response.json()
            results['road_count'] = len(data.get('elements', []))
            query = f"""
            [out:json][timeout:5];
            (way["natural"="coastline"](around:{radius},{location.lat},{location.lon}););
            out count;
            """
            response = requests.post(overpass_url, data={'data': query}, timeout=5)
            data = response.json()
            results['coastline_count'] = len(data.get('elements', []))
            return results
        except Exception:
            return None

    def analyse(self, location: Location, params: Dict) -> Dict:
        radius = params.get('radius', 10000)
        weights = params.get('weights', {
            'elevation': 0.15,
            'population_density': 0.18,
            'coastal_proximity': 0.13,
            'infrastructure_access': 0.13,
            'land_availability': 0.13,
            'flood_risk': 0.10,
            'latitudinal_advantage': 0.08,
            'wind_conditions': 0.10,
        })
        scores = {}
        details = {}
        data_sources = []
        data_source_details = []
        osm_data = None
        osm_available = False
        weather_data = None

        elevation_score, elevation_m, elev_source = self._get_elevation_quick(location)
        data_sources.append(elev_source)
        data_source_details.append(f"Elevation: {elev_source}")
        scores['elevation'] = elevation_score
        details['elevation'] = {
            'score': elevation_score,
            'value': f"{elevation_m:.0f}m",
            'weight': weights['elevation'],
            'source': elev_source
        }

        pop_score, pop_density, pop_source = self._geographic_score_population(location)
        data_sources.append(pop_source)
        data_source_details.append(f"Population: {pop_source}")
        scores['population_density'] = pop_score
        details['population_density'] = {
            'score': pop_score,
            'value': f"{pop_density:.1f} people/km²" if pop_density > 0 else "Very Low",
            'weight': weights['population_density'],
            'source': pop_source
        }

        coastal_score, distance_to_coast, coastal_source = self._geographic_score_coastal(location)
        data_sources.append(coastal_source)
        data_source_details.append(f"Coastal: {coastal_source}")
        scores['coastal_proximity'] = coastal_score
        details['coastal_proximity'] = {
            'score': coastal_score,
            'value': f"{distance_to_coast:.1f}km",
            'weight': weights['coastal_proximity'],
            'source': coastal_source
        }

        infra_score, infra_details, infra_source = self._geographic_score_infrastructure(location)
        data_sources.append(infra_source)
        data_source_details.append(f"Infrastructure: {infra_source}")
        scores['infrastructure_access'] = infra_score
        details['infrastructure_access'] = {
            'score': infra_score,
            'value': infra_details,
            'weight': weights['infrastructure_access'],
            'source': infra_source
        }

        land_score, land_details, land_source = self._geographic_score_land(location)
        data_sources.append(land_source)
        data_source_details.append(f"Land: {land_source}")
        scores['land_availability'] = land_score
        details['land_availability'] = {
            'score': land_score,
            'value': land_details,
            'weight': weights['land_availability'],
            'source': land_source
        }

        flood_score, flood_risk = self._geographic_score_flood(elevation_m)
        scores['flood_risk'] = flood_score
        details['flood_risk'] = {
            'score': flood_score,
            'value': flood_risk,
            'weight': weights['flood_risk'],
            'source': 'From elevation'
        }

        lat_score = self._score_latitudinal_advantage(location.lat)
        scores['latitudinal_advantage'] = lat_score
        details['latitudinal_advantage'] = {
            'score': lat_score,
            'value': f"{abs(location.lat):.1f}°{'N' if location.lat > 0 else 'S'}",
            'weight': weights['latitudinal_advantage'],
            'source': 'Geographic'
        }

        weather_data = self._get_weather(location)
        if weather_data:
            ws = weather_data.get('wind_speed_ms')
            wg = weather_data.get('wind_gust_ms')
            wind_score, wind_rating, wind_explanation = self._score_wind(ws, wg)
            data_source_details.append(f"Wind: {wind_explanation}")
            weather_data['wind_rating'] = wind_rating
            weather_data['wind_explanation'] = wind_explanation
        else:
            wind_score, wind_rating, wind_explanation = 3.0, "Unknown", "Weather unavailable"
            data_source_details.append("Wind: Weather API unavailable — neutral score")
        scores['wind_conditions'] = wind_score
        details['wind_conditions'] = {
            'score': wind_score,
            'value': weather_data.get('wind_speed_ms') and f"{weather_data['wind_speed_ms']:.1f} m/s" or "N/A",
            'weight': weights['wind_conditions'],
            'source': weather_data.get('source', 'Unavailable') if weather_data else 'Unavailable'
        }

        total_score = sum(scores[k] * weights.get(k, 0) for k in scores if k in weights)
        max_possible = sum(weights.values()) * 5.0
        percentage = (total_score / max_possible) * 100 if max_possible > 0 else 0

        penalty = 0.0
        penalty_reasons = []
        if elevation_m < 20:
            penalty += 15.0
            penalty_reasons.append(f"Very low elevation ({elevation_m:.0f}m): -15%")
        if flood_risk == 'High':
            penalty += 10.0
            penalty_reasons.append("High flood risk: -10%")
        if pop_density > 5:
            penalty += 10.0
            penalty_reasons.append("High population density: -10%")
        if isinstance(land_details, dict) and land_details.get('developed_areas', 0) >= 10:
            penalty += 8.0
            penalty_reasons.append("Scarce land availability: -8%")
        if weather_data and weather_data.get('wind_speed_ms'):
            if weather_data['wind_speed_ms'] > 12:
                penalty += 8.0
                penalty_reasons.append(f"Very high wind ({weather_data['wind_speed_ms']:.1f} m/s): -8%")

        percentage = max(0.0, min(100.0, percentage - penalty))

        if percentage >= 80:
            rating, emoji, rec = 'Excellent', '🚀', 'Highly recommended for spaceport development'
        elif percentage >= 65:
            rating, emoji, rec = 'Good', '👍', 'Suitable with minor site preparation'
        elif percentage >= 50:
            rating, emoji, rec = 'Moderate', '👌', 'Suitable with significant site preparation'
        elif percentage >= 35:
            rating, emoji, rec = 'Limited', '⚠️', 'Marginal - requires major investment'
        else:
            rating, emoji, rec = 'Poor', '❌', 'Not recommended for spaceport development'

        try:
            osm_data = self._try_osm_in_background(location, radius)
            if osm_data and any(v > 0 for v in osm_data.values()):
                osm_available = True
                data_source_details.append(
                    f"🌐 OSM Background: Found {osm_data.get('airport_count', 0)} airports, "
                    f"{osm_data.get('settlement_count', 0)} settlements")
        except Exception:
            pass

        return {
            'success': True, 'scores': scores, 'details': details,
            'weighted_score': total_score, 'max_possible_score': max_possible,
            'suitability_percentage': round(percentage, 1),
            'base_percentage': round((total_score / max_possible * 100) if max_possible > 0 else 0, 1),
            'penalty_applied': round(penalty, 1),
            'penalty_reasons': penalty_reasons,
            'rating': rating, 'rating_emoji': emoji, 'recommendation': rec,
            'radius_used': radius,
            'location': f"{location.name or 'Borneo location'} ({location.lat:.4f}, {location.lon:.4f})",
            'elevation_m': elevation_m, 'population_density': pop_density,
            'coastal_distance_km': distance_to_coast, 'flood_risk': flood_risk,
            'lat_deg': abs(location.lat),
            'data_sources': data_sources,
            'data_source_details': data_source_details,
            'used_osm': osm_available, 'osm_data': osm_data if osm_available else None,
            'weather': weather_data,
            'wind_speed_ms': weather_data.get('wind_speed_ms') if weather_data else None,
            'wind_gust_ms': weather_data.get('wind_gust_ms') if weather_data else None,
            'wind_direction_deg': weather_data.get('wind_direction_deg') if weather_data else None,
            'temperature_c': weather_data.get('temperature_c') if weather_data else None,
            'humidity_pct': weather_data.get('humidity_pct') if weather_data else None,
            'used_fallback': True, 'from_cache': False,
            'analysis_method': 'HYBRID: Geographic Rules + OSM + Weather'
        }


class BorneoProximityStrategy(AnalysisStrategy):
    def get_name(self) -> str:
        return "Proximity Analysis (Borneo)"

    def analyse(self, location: Location, params: Dict) -> Dict:
        amenity_type = params.get('amenity_type', 'hospital')
        radius = params.get('radius', 5000)
        tags_to_query = BORNEO_SPACEPORT_FACILITY_TAGS.get(amenity_type, [('amenity', amenity_type)])
        query_parts = []
        for key, value in tags_to_query:
            query_parts.append(f'node["{key}"="{value}"](around:{radius},{location.lat},{location.lon});')
            query_parts.append(f'way["{key}"="{value}"](around:{radius},{location.lat},{location.lon});')
        query_body = "\n".join(query_parts)
        query = f"[out:json][timeout:45];\n(\n{query_body}\n);\nout center;"
        try:
            headers = {'User-Agent': 'StarbaseV/1.0'}
            response = requests.post("https://overpass-api.de/api/interpreter",
                                   data={'data': query}, headers=headers, timeout=45)
            response.raise_for_status()
            data = response.json()
            elements = data.get('elements', [])
            results = []
            seen_locations = set()
            for elem in elements:
                lat = elem.get('lat') or elem.get('center', {}).get('lat')
                lon = elem.get('lon') or elem.get('center', {}).get('lon')
                if lat and lon:
                    loc_key = f"{round(lat, 5)}_{round(lon, 5)}"
                    if loc_key not in seen_locations:
                        seen_locations.add(loc_key)
                        tags = elem.get('tags', {})
                        name = tags.get('name', tags.get('brand', 'Unknown'))
                        results.append({'name': name, 'lat': lat, 'lon': lon,
                                        'type': amenity_type, 'tags': tags})
            return {'success': True, 'count': len(results), 'amenities': results,
                    'radius': radius, 'amenity_type': amenity_type,
                    'location': f"Borneo ({location.lat:.4f}, {location.lon:.4f})"}
        except Exception as e:
            return {'success': False, 'error': str(e), 'amenities': [], 'count': 0,
                    'radius': radius, 'amenity_type': amenity_type}


class BorneoStrategySelector:
    _strategies = {
        'spaceport': BorneoSuitabilityStrategy,
        'proximity': BorneoProximityStrategy,
    }

    @classmethod
    def get_strategy(cls, strategy_type: str) -> AnalysisStrategy:
        strategy_class = cls._strategies.get(strategy_type)
        if not strategy_class:
            raise ValueError(f"Unknown strategy: {strategy_type}")
        return strategy_class()

    @classmethod
    def available_strategies(cls) -> List[str]:
        return list(cls._strategies.keys())

# ============================================================================
# WEST MALAYSIA STRATEGIES
# ============================================================================

class WestSuitabilityStrategy(AnalysisStrategy):
    def get_name(self) -> str:
        return "Spaceport Suitability Analysis (West Malaysia HYBRID)"

    def _get_elevation_quick(self, location: Location) -> tuple:
        try:
            url = f"https://api.open-elevation.com/api/v1/lookup?locations={location.lat},{location.lon}"
            r = requests.get(url, timeout=3)
            elev = r.json()['results'][0]['elevation']
            if 50 <= elev <= 200:
                return 5.0, elev, 'Live Elevation API'
            elif 200 < elev <= 500:
                return 4.5, elev, 'Live Elevation API'
            elif 20 <= elev < 50:
                return 4.0, elev, 'Live Elevation API'
            elif 0 <= elev < 20:
                return 2.0, elev, 'Live Elevation API'
            else:
                return 3.0, elev, 'Live Elevation API'
        except Exception:
            lat, lon = location.lat, location.lon
            if 3.3 < lat < 4.6 and 101.3 < lon < 101.9:
                return 4.5, 1200, 'Fallback: Titiwangsa highlands'
            elif lat > 4.5 and 101.5 < lon < 102.5:
                return 3.5, 250, 'Fallback: Kelantan interior'
            elif 3.5 < lat < 4.6 and 101.9 < lon < 102.8:
                return 3.5, 300, 'Fallback: Pahang interior'
            elif lat < 2.5 and 102.5 < lon < 103.8:
                return 3.0, 80, 'Fallback: Johor interior'
            else:
                return 3.0, 30, 'Fallback: Coastal lowland'

    def _get_weather(self, location: Location) -> Optional[Dict]:
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": location.lat,
                "longitude": location.lon,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,"
                           "wind_direction_10m,wind_gusts_10m",
                "wind_speed_unit": "ms",
                "timezone": "auto",
            }
            r = requests.get(url, params=params, timeout=4)
            data = r.json()
            cur = data.get("current", {})
            return {
                "temperature_c": cur.get("temperature_2m"),
                "humidity_pct": cur.get("relative_humidity_2m"),
                "wind_speed_ms": cur.get("wind_speed_10m"),
                "wind_direction_deg": cur.get("wind_direction_10m"),
                "wind_gust_ms": cur.get("wind_gusts_10m"),
                "source": "Open-Meteo (Live)",
                "time": cur.get("time"),
            }
        except Exception:
            return None

    def _score_wind(self, wind_speed_ms, wind_gust_ms) -> tuple:
        if wind_speed_ms is None:
            return 3.0, "Unknown", "Weather unavailable — neutral score"
        if wind_speed_ms < 4:
            return 5.0, "Excellent", f"Calm ({wind_speed_ms:.1f} m/s) — ideal for launches"
        elif wind_speed_ms < 6:
            return 4.5, "Good", f"Light breeze ({wind_speed_ms:.1f} m/s) — very suitable"
        elif wind_speed_ms < 8:
            return 4.0, "Good", f"Moderate wind ({wind_speed_ms:.1f} m/s) — manageable"
        elif wind_speed_ms < 12:
            return 3.0, "Moderate", f"Fairly windy ({wind_speed_ms:.1f} m/s) — schedule around it"
        else:
            return 2.0, "Poor", f"High wind ({wind_speed_ms:.1f} m/s) — challenging launches"

    def _geographic_score_coastal(self, location: Location) -> tuple:
        lat, lon = location.lat, location.lon
        if lon > 103.0:
            return 5.0, 0, 'Geographic: East coast (South China Sea)'
        elif lon > 102.5:
            return 4.5, 5, 'Geographic: Near east coast'
        elif lon > 101.5:
            return 3.5, 15, 'Geographic: Central'
        elif lon > 100.5:
            return 3.0, 25, 'Geographic: Near west coast'
        else:
            return 2.5, 5, 'Geographic: West coast (Strait of Malacca)'

    def _geographic_score_population(self, location: Location) -> tuple:
        lat, lon = location.lat, location.lon
        min_dist = 999
        closest_pop = 0
        for name, data in WEST_STATIC_SETTLEMENTS.items():
            s_lat, s_lon = data['coords']
            dist = self._haversine(lat, lon, s_lat, s_lon)
            if dist < min_dist:
                min_dist = dist
                closest_pop = data['population']
        if min_dist > 60:
            return 5.0, 0.2, 'Geographic: Remote'
        elif min_dist > 35:
            return 4.0, 1.0, 'Geographic: Rural'
        elif min_dist > 20:
            return 3.0, 2.5, 'Geographic: Semi-rural'
        elif min_dist > 10:
            return 2.0, 5.0, 'Geographic: Near town'
        else:
            return 1.0, 12.0, 'Geographic: Near city'

    def _geographic_score_infrastructure(self, location: Location) -> tuple:
        lat, lon = location.lat, location.lon
        min_dist = 999
        for name, coords in WEST_STATIC_AIRPORTS.items():
            d = self._haversine(lat, lon, coords[0], coords[1])
            min_dist = min(min_dist, d)
        details = {
            'airports': 1 if min_dist < 60 else 0,
            'major_roads': 2 if min_dist < 30 else 0,
            'ports': 0, 'power_facilities': 0
        }
        if min_dist < 30:
            return 4.5, details, 'Geographic: Near airport'
        elif min_dist < 60:
            return 3.5, details, 'Geographic: Airport nearby'
        elif min_dist < 100:
            return 2.5, details, 'Geographic: Some access'
        else:
            return 1.5, details, 'Geographic: Remote'

    def _geographic_score_land(self, location: Location) -> tuple:
        lat, lon = location.lat, location.lon
        min_dist = 999
        for name, data in WEST_STATIC_SETTLEMENTS.items():
            d = self._haversine(lat, lon, data['coords'][0], data['coords'][1])
            min_dist = min(min_dist, d)
        details = {
            'forest_areas': 30 if min_dist > 40 else 10,
            'developed_areas': 2 if min_dist > 40 else 10,
            'agriculture': 5
        }
        if min_dist > 60:
            return 5.0, details, 'Geographic: Abundant land'
        elif min_dist > 35:
            return 4.0, details, 'Geographic: Good land'
        elif min_dist > 20:
            return 3.0, details, 'Geographic: Moderate land'
        elif min_dist > 10:
            return 2.0, details, 'Geographic: Limited land'
        else:
            return 1.0, details, 'Geographic: Scarce land'

    def _geographic_score_flood(self, elevation_m: float) -> tuple:
        if elevation_m > 100:
            return 5.0, 'Low'
        elif elevation_m > 50:
            return 4.0, 'Low'
        elif elevation_m > 20:
            return 3.0, 'Moderate'
        else:
            return 1.5, 'High'

    def _score_latitudinal_advantage(self, lat: float) -> float:
        a = abs(lat)
        if a <= 1.5:
            return 5.0
        elif a <= 3:
            return 4.5
        elif a <= 5:
            return 4.0
        elif a <= 7:
            return 3.0
        else:
            return 2.0

    def _haversine(self, lat1, lon1, lat2, lon2) -> float:
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2
             + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
             * math.sin(dlon / 2) ** 2)
        return R * 2 * math.asin(min(1, math.sqrt(a)))

    def _try_osm_in_background(self, location: Location, radius: int) -> Optional[Dict]:
        try:
            url = "https://overpass-api.de/api/interpreter"
            results = {}
            q = f'[out:json][timeout:5];(node["aeroway"="aerodrome"](around:{radius},{location.lat},{location.lon});way["aeroway"="aerodrome"](around:{radius},{location.lat},{location.lon}););out count;'
            results['airport_count'] = len(requests.post(url, data={'data': q}, timeout=5).json().get('elements', []))
            q = f'[out:json][timeout:5];(node["place"~"city|town|village"](around:{radius},{location.lat},{location.lon}););out count;'
            results['settlement_count'] = len(requests.post(url, data={'data': q}, timeout=5).json().get('elements', []))
            q = f'[out:json][timeout:5];(way["highway"~"motorway|trunk|primary"](around:{radius},{location.lat},{location.lon}););out count;'
            results['road_count'] = len(requests.post(url, data={'data': q}, timeout=5).json().get('elements', []))
            q = f'[out:json][timeout:5];(way["natural"="coastline"](around:{radius},{location.lat},{location.lon}););out count;'
            results['coastline_count'] = len(requests.post(url, data={'data': q}, timeout=5).json().get('elements', []))
            return results
        except Exception:
            return None

    def analyse(self, location: Location, params: Dict) -> Dict:
        radius = params.get('radius', 10000)
        weights = params.get('weights', {
            'elevation': 0.15,
            'population_density': 0.18,
            'coastal_proximity': 0.13,
            'infrastructure_access': 0.13,
            'land_availability': 0.13,
            'flood_risk': 0.10,
            'latitudinal_advantage': 0.08,
            'wind_conditions': 0.10,
        })
        scores, details = {}, {}
        data_source_details = []

        elevation_score, elevation_m, elev_source = self._get_elevation_quick(location)
        scores['elevation'] = elevation_score
        details['elevation'] = {'score': elevation_score, 'value': f"{elevation_m:.0f}m",
                                'weight': weights['elevation'], 'source': elev_source}
        data_source_details.append(f"Elevation: {elev_source}")

        pop_score, pop_density, pop_source = self._geographic_score_population(location)
        scores['population_density'] = pop_score
        details['population_density'] = {'score': pop_score,
                                         'value': f"{pop_density:.1f} people/km²",
                                         'weight': weights['population_density'],
                                         'source': pop_source}
        data_source_details.append(f"Population: {pop_source}")

        coastal_score, dist_coast, coastal_source = self._geographic_score_coastal(location)
        scores['coastal_proximity'] = coastal_score
        details['coastal_proximity'] = {'score': coastal_score, 'value': f"{dist_coast:.1f}km",
                                        'weight': weights['coastal_proximity'],
                                        'source': coastal_source}
        data_source_details.append(f"Coastal: {coastal_source}")

        infra_score, infra_details, infra_source = self._geographic_score_infrastructure(location)
        scores['infrastructure_access'] = infra_score
        details['infrastructure_access'] = {'score': infra_score, 'value': infra_details,
                                            'weight': weights['infrastructure_access'],
                                            'source': infra_source}
        data_source_details.append(f"Infrastructure: {infra_source}")

        land_score, land_details, land_source = self._geographic_score_land(location)
        scores['land_availability'] = land_score
        details['land_availability'] = {'score': land_score, 'value': land_details,
                                        'weight': weights['land_availability'],
                                        'source': land_source}
        data_source_details.append(f"Land: {land_source}")

        flood_score, flood_risk = self._geographic_score_flood(elevation_m)
        scores['flood_risk'] = flood_score
        details['flood_risk'] = {'score': flood_score, 'value': flood_risk,
                                 'weight': weights['flood_risk'], 'source': 'From elevation'}

        lat_score = self._score_latitudinal_advantage(location.lat)
        scores['latitudinal_advantage'] = lat_score
        details['latitudinal_advantage'] = {'score': lat_score,
                                            'value': f"{abs(location.lat):.1f}°N",
                                            'weight': weights['latitudinal_advantage'],
                                            'source': 'Geographic'}

        weather_data = self._get_weather(location)
        if weather_data:
            ws = weather_data.get('wind_speed_ms')
            wg = weather_data.get('wind_gust_ms')
            wind_score, wind_rating, wind_explanation = self._score_wind(ws, wg)
            data_source_details.append(f"Wind: {wind_explanation}")
            weather_data['wind_rating'] = wind_rating
            weather_data['wind_explanation'] = wind_explanation
        else:
            wind_score, wind_rating, wind_explanation = 3.0, "Unknown", "Weather unavailable"
            data_source_details.append("Wind: Weather API unavailable — neutral score")
        scores['wind_conditions'] = wind_score
        details['wind_conditions'] = {
            'score': wind_score,
            'value': weather_data.get('wind_speed_ms') and f"{weather_data['wind_speed_ms']:.1f} m/s" or "N/A",
            'weight': weights['wind_conditions'],
            'source': weather_data.get('source', 'Unavailable') if weather_data else 'Unavailable'
        }

        total_score = sum(scores[k] * weights.get(k, 0) for k in scores if k in weights)
        max_possible = sum(weights.values()) * 5.0
        percentage = (total_score / max_possible) * 100 if max_possible > 0 else 0

        penalty = 0.0
        penalty_reasons = []
        if elevation_m < 20:
            penalty += 15.0
            penalty_reasons.append(f"Very low elevation ({elevation_m:.0f}m): -15%")
        if flood_risk == 'High':
            penalty += 10.0
            penalty_reasons.append("High flood risk: -10%")
        if pop_density > 5:
            penalty += 10.0
            penalty_reasons.append("High population density: -10%")
        if isinstance(land_details, dict) and land_details.get('developed_areas', 0) >= 10:
            penalty += 8.0
            penalty_reasons.append("Scarce land availability: -8%")
        if weather_data and weather_data.get('wind_speed_ms'):
            if weather_data['wind_speed_ms'] > 12:
                penalty += 8.0
                penalty_reasons.append(f"Very high wind ({weather_data['wind_speed_ms']:.1f} m/s): -8%")

        percentage = max(0.0, min(100.0, percentage - penalty))

        if percentage >= 80:
            rating, emoji, rec = 'Excellent', '🚀', 'Highly recommended for spaceport development'
        elif percentage >= 65:
            rating, emoji, rec = 'Good', '👍', 'Suitable with minor site preparation'
        elif percentage >= 50:
            rating, emoji, rec = 'Moderate', '👌', 'Suitable with significant site preparation'
        elif percentage >= 35:
            rating, emoji, rec = 'Limited', '⚠️', 'Marginal - requires major investment'
        else:
            rating, emoji, rec = 'Poor', '❌', 'Not recommended for spaceport development'

        osm_data = None
        osm_available = False
        try:
            osm_data = self._try_osm_in_background(location, radius)
            if osm_data and any(v > 0 for v in osm_data.values()):
                osm_available = True
                data_source_details.append(
                    f"🌐 OSM Background: Found {osm_data.get('airport_count', 0)} airports, "
                    f"{osm_data.get('settlement_count', 0)} settlements")
        except Exception:
            pass

        return {
            'success': True, 'scores': scores, 'details': details,
            'weighted_score': total_score, 'max_possible_score': max_possible,
            'suitability_percentage': round(percentage, 1),
            'base_percentage': round((total_score / max_possible * 100) if max_possible > 0 else 0, 1),
            'penalty_applied': round(penalty, 1),
            'penalty_reasons': penalty_reasons,
            'rating': rating, 'rating_emoji': emoji, 'recommendation': rec,
            'radius_used': radius,
            'location': f"{location.name or 'West Malaysia location'} ({location.lat:.4f}, {location.lon:.4f})",
            'elevation_m': elevation_m, 'population_density': pop_density,
            'coastal_distance_km': dist_coast, 'flood_risk': flood_risk,
            'lat_deg': abs(location.lat),
            'data_source_details': data_source_details,
            'used_osm': osm_available, 'osm_data': osm_data if osm_available else None,
            'weather': weather_data,
            'wind_speed_ms': weather_data.get('wind_speed_ms') if weather_data else None,
            'wind_gust_ms': weather_data.get('wind_gust_ms') if weather_data else None,
            'wind_direction_deg': weather_data.get('wind_direction_deg') if weather_data else None,
            'temperature_c': weather_data.get('temperature_c') if weather_data else None,
            'humidity_pct': weather_data.get('humidity_pct') if weather_data else None,
            'used_fallback': True, 'from_cache': False,
            'analysis_method': 'HYBRID: Geographic Rules + OSM + Weather'
        }


class WestProximityStrategy(AnalysisStrategy):
    def get_name(self) -> str:
        return "Proximity Analysis (West Malaysia)"

    def analyse(self, location: Location, params: Dict) -> Dict:
        amenity_type = params.get('amenity_type', 'hospital')
        radius = params.get('radius', 5000)
        tags = WEST_SPACEPORT_FACILITY_TAGS.get(amenity_type, [('amenity', amenity_type)])
        parts = []
        for k, v in tags:
            parts.append(f'node["{k}"="{v}"](around:{radius},{location.lat},{location.lon});')
            parts.append(f'way["{k}"="{v}"](around:{radius},{location.lat},{location.lon});')
        query = f"[out:json][timeout:45];({chr(10).join(parts)});out center;"
        try:
            r = requests.post("https://overpass-api.de/api/interpreter",
                              data={'data': query},
                              headers={'User-Agent': 'StarbaseV/1.0'}, timeout=45)
            r.raise_for_status()
            results, seen = [], set()
            for elem in r.json().get('elements', []):
                lat = elem.get('lat') or elem.get('center', {}).get('lat')
                lon = elem.get('lon') or elem.get('center', {}).get('lon')
                if lat and lon:
                    key = f"{round(lat, 5)}_{round(lon, 5)}"
                    if key not in seen:
                        seen.add(key)
                        tags_d = elem.get('tags', {})
                        results.append({
                            'name': tags_d.get('name', tags_d.get('brand', 'Unknown')),
                            'lat': lat, 'lon': lon, 'type': amenity_type, 'tags': tags_d
                        })
            return {'success': True, 'count': len(results), 'amenities': results,
                    'radius': radius, 'amenity_type': amenity_type,
                    'location': f"West Malaysia ({location.lat:.4f}, {location.lon:.4f})"}
        except Exception as e:
            return {'success': False, 'error': str(e), 'amenities': [],
                    'count': 0, 'radius': radius, 'amenity_type': amenity_type}


class WestStrategySelector:
    _strategies = {'spaceport': WestSuitabilityStrategy,
                   'proximity': WestProximityStrategy}

    @classmethod
    def get_strategy(cls, t: str) -> AnalysisStrategy:
        c = cls._strategies.get(t)
        if not c:
            raise ValueError(f"Unknown strategy: {t}")
        return c()

# ============================================================================
# UNIFIED AGENT
# ============================================================================

class GeoAIAgent:
    def __init__(self):
        self.memory_repo = MemoryRepository()
        self.rate_limiter = RateLimiter(calls_per_second=0.5)
        self.short_term_memory: Dict[str, Any] = {}
        self.current_analysis: Optional[AnalysisResult] = None

    def reason_about_query(self, query: str) -> tuple:
        steps = []
        steps.append({'step': 'Understanding Query',
                      'reasoning': f"Analysing spaceport site selection request: '{query}'",
                      'action': 'parse_intent'})
        similar = self.memory_repo.find_similar_analyses(query, limit=3)
        if similar:
            steps.append({'step': 'Memory Recall',
                          'reasoning': f"Found {len(similar)} similar past analyses.",
                          'action': 'apply_learned_parameters',
                          'prior_experience': similar[0]})
        analysis_type = 'spaceport'
        steps.append({'step': 'Strategy Selection',
                      'reasoning': 'Using Spaceport Suitability strategy.',
                      'action': 'use_spaceport_strategy'})
        learned_radius = self.memory_repo.get_learned_parameter(analysis_type, 'radius')
        if learned_radius:
            steps.append({'step': 'Parameter Optimisation',
                          'reasoning': f"Using learned optimal radius of {learned_radius}m.",
                          'action': 'apply_learned_radius', 'value': learned_radius})
        else:
            steps.append({'step': 'Parameter Selection',
                          'reasoning': 'Using default radius of 10km.',
                          'action': 'use_default_radius', 'value': '10000'})
        steps.append({'step': 'Execution Planning',
                      'reasoning': f'Will execute {analysis_type} analysis.',
                      'action': 'prepare_execution'})
        return steps, analysis_type

    def execute_analysis(self, location, query, params, region, progress_callback=None):
        start_time = time.time()
        result = AnalysisResult(query=query, timestamp=datetime.now().isoformat())
        reasoning_steps, analysis_type = self.reason_about_query(query)
        for i, step_info in enumerate(reasoning_steps):
            result.steps.append(AnalysisStep(
                step_number=i + 1, name=step_info['step'],
                description=step_info['reasoning'], status='completed',
                reasoning=step_info['reasoning']))
        if progress_callback:
            progress_callback(0.3, "Reasoning complete, executing hybrid analysis...")
        try:
            if region == "borneo":
                strategy = BorneoStrategySelector.get_strategy(analysis_type)
            else:
                strategy = WestStrategySelector.get_strategy(analysis_type)
            self.rate_limiter.wait()
            analysis_result = strategy.analyse(location, params)
            analysis_result['from_cache'] = False
            if analysis_result.get('success'):
                used_osm = analysis_result.get('used_osm', False)
                result.steps.append(AnalysisStep(
                    step_number=len(result.steps) + 1,
                    name="Data Source Validation",
                    description=f"Method: {analysis_result.get('analysis_method', 'HYBRID')}",
                    status='completed',
                    reasoning=f"Used {'OSM + Geographic' if used_osm else 'Geographic'} rules"))
            result.steps.append(AnalysisStep(
                step_number=len(result.steps) + 1,
                name=f"Execute {strategy.get_name()}",
                description=f"Running {analysis_type} analysis on {location.name or 'location'}",
                status='completed' if analysis_result.get('success') else 'failed',
                result=analysis_result,
                reasoning=f"Analysis returned {len(str(analysis_result))} bytes of data"))
            result.final_result = analysis_result
            result.success = analysis_result.get('success', False)
        except Exception as e:
            result.steps.append(AnalysisStep(
                step_number=len(result.steps) + 1,
                name="Analysis Execution",
                description="Executing spatial analysis",
                status='failed',
                reasoning=f"Error: {str(e)}"))
            result.success = False
        if progress_callback:
            progress_callback(0.8, "Storing results in memory...")
        result.total_time = time.time() - start_time
        memory_entry = MemoryEntry(
            query=query,
            result_summary=str(result.final_result)[:500] if result.final_result else "",
            success=result.success,
            execution_time=result.total_time,
            timestamp=result.timestamp,
            parameters_used=params)
        self.memory_repo.store_analysis(memory_entry, region=region)
        if result.success:
            self.memory_repo.update_learned_parameter(
                analysis_type, 'radius', str(params.get('radius', 10000)), True)
        self.short_term_memory['last_analysis'] = result
        self.short_term_memory['last_location'] = location
        if progress_callback:
            progress_callback(1.0, "Complete")
        return result

# ============================================================================
# UI FUNCTIONS
# ============================================================================

def init_session_state():
    if 'agent' not in st.session_state:
        st.session_state.agent = GeoAIAgent()
    if 'analysis_history' not in st.session_state:
        st.session_state.analysis_history = []
    if 'selected_location_borneo' not in st.session_state:
        st.session_state.selected_location_borneo = Location(
            lat=6.8860, lon=116.8430, name="Kudat Peninsula, Sabah")
    if 'selected_location_west' not in st.session_state:
        st.session_state.selected_location_west = Location(
            lat=1.3600, lon=104.1700, name="Pengerang, Johor")
    if 'reasoning_log' not in st.session_state:
        st.session_state.reasoning_log = []
    if 'current_results' not in st.session_state:
        st.session_state.current_results = None
    if 'basemap_choice' not in st.session_state:
        st.session_state.basemap_choice = "OpenStreetMap"
    if 'show_radius_circle' not in st.session_state:
        st.session_state.show_radius_circle = True
    if 'comparison_mode' not in st.session_state:
        st.session_state.comparison_mode = False
    if 'candidate_scores' not in st.session_state:
        st.session_state.candidate_scores = {}
    if 'show_corridor' not in st.session_state:
        st.session_state.show_corridor = True
    if 'show_heatmap' not in st.session_state:
        st.session_state.show_heatmap = False
    if 'wind_history' not in st.session_state:
        st.session_state.wind_history = None
    if 'wind_history_key' not in st.session_state:
        st.session_state.wind_history_key = None


def get_current_location():
    if st.session_state.active_region == "borneo":
        return st.session_state.selected_location_borneo
    return st.session_state.selected_location_west


def set_current_location(loc):
    if st.session_state.active_region == "borneo":
        st.session_state.selected_location_borneo = loc
    else:
        st.session_state.selected_location_west = loc


def get_current_candidates():
    if st.session_state.active_region == "borneo":
        return BORNEO_SPACEPORT_CANDIDATES
    return WEST_MALAYSIA_SPACEPORT_CANDIDATES


def get_current_locations():
    if st.session_state.active_region == "borneo":
        return BORNEO_LOCATIONS
    return WEST_MALAYSIA_LOCATIONS


def get_tiles_for_basemap(basemap_choice: str) -> str:
    if basemap_choice == "Satellite":
        return "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    return "OpenStreetMap"


def render_region_selector_sidebar():
    st.markdown("""
    <div style="text-align: center; padding: 10px 0;">
        <div style="font-size: 2.2rem; font-family: 'Courier New', monospace;
             background: linear-gradient(90deg, #00f0ff, #b026ff, #ff2d95);
             -webkit-background-clip: text; -webkit-text-fill-color: transparent;
             font-weight: 900; letter-spacing: 3px;">🚀 STARBASEV</div>
        <div style="color: #00f0ff; font-size: 0.75rem;
             font-family: 'Courier New', monospace; letter-spacing: 5px;">
            SITE SELECTOR</div>
        <div class="cyber-divider"></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="color: #39ff14; font-family: 'Courier New', monospace;
         letter-spacing: 2px; font-size: 0.9rem; margin-bottom: 5px;">
        🌏 ACTIVE REGION
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏝️ BORNEO", use_container_width=True,
                     type="primary" if st.session_state.active_region == "borneo" else "secondary",
                     key="region_borneo_btn"):
            st.session_state.active_region = "borneo"
            st.session_state.current_results = None
            st.session_state.reasoning_log = []
            st.session_state.candidate_scores = {}
            st.session_state.wind_history = None
            st.rerun()
    with col2:
        if st.button("🌏 WEST MY", use_container_width=True,
                     type="primary" if st.session_state.active_region == "west_malaysia" else "secondary",
                     key="region_west_btn"):
            st.session_state.active_region = "west_malaysia"
            st.session_state.current_results = None
            st.session_state.reasoning_log = []
            st.session_state.candidate_scores = {}
            st.session_state.wind_history = None
            st.rerun()

    region_label = "BORNEO (Sabah & Sarawak)" if st.session_state.active_region == "borneo" else "WEST MALAYSIA (Peninsular)"
    st.markdown(f"""
    <div style="text-align: center; color: #8080a0; font-family: 'Courier New', monospace;
         font-size: 0.7rem; letter-spacing: 2px; padding: 5px 0;">
        {region_label}
    </div>
    """, unsafe_allow_html=True)


def render_region_sub_selector():
    if st.session_state.active_region == "borneo":
        regions = {
            '🌏 All Borneo': 'all',
            '🏝️ Sabah Only': 'sabah',
            '🏝️ Sarawak Only': 'sarawak',
            '🚀 Spaceport Candidates': 'candidates'
        }
        selected_region = st.selectbox("Select Region", options=list(regions.keys()),
                                       index=0, key="borneo_region")
        region_key = regions[selected_region]
        if region_key == 'sabah':
            locations = SABAH_LOCATIONS
            st.info(f"🏝️ Showing {len(locations)} locations in Sabah")
        elif region_key == 'sarawak':
            locations = SARAWAK_LOCATIONS
            st.info(f"🏝️ Showing {len(locations)} locations in Sarawak")
        elif region_key == 'candidates':
            locations = BORNEO_SPACEPORT_CANDIDATES
            st.info(f"🚀 Showing {len(locations)} spaceport candidate sites")
        else:
            locations = BORNEO_LOCATIONS
            st.info(f"🌏 Showing {len(locations)} locations across Borneo")
        return locations, region_key
    else:
        regions = {
            '🌏 All West Malaysia': 'all',
            '🏝️ Northern (Perlis, Kedah, Penang, Perak)': 'north',
            '🏙️ Central (Selangor, KL, Putrajaya, N. Sembilan)': 'central',
            '🌴 Southern (Melaka, Johor)': 'south',
            '🌊 East Coast (Kelantan, Terengganu, Pahang)': 'east',
            '🚀 Spaceport Candidates': 'candidates'
        }
        sel = st.selectbox("Select Region", options=list(regions.keys()),
                           index=0, key="west_region")
        rk = regions[sel]
        north = ['Perlis', 'Kedah', 'Penang', 'Perak']
        central = ['Selangor', 'Kuala Lumpur', 'Putrajaya', 'Negeri Sembilan']
        south = ['Melaka', 'Johor']
        east = ['Kelantan', 'Terengganu', 'Pahang']
        if rk == 'all':
            locs = WEST_MALAYSIA_LOCATIONS
            st.info(f"🌏 Showing {len(locs)} locations across West Malaysia")
        elif rk == 'candidates':
            locs = WEST_MALAYSIA_SPACEPORT_CANDIDATES
            st.info(f"🚀 Showing {len(locs)} spaceport candidate sites")
        else:
            sl = {'north': north, 'central': central, 'south': south, 'east': east}[rk]
            locs = {k: v for k, v in WEST_MALAYSIA_LOCATIONS.items()
                    if any(f"({s})" in k for s in sl)}
            st.info(f"📍 Showing {len(locs)} locations in {sel}")
        return locs, rk


def render_sidebar():
    with st.sidebar:
        render_region_selector_sidebar()

        cache_stats = api_cache.get_stats()
        st.markdown(f"""
        <div style="color: #a0a0c0; font-family: 'Courier New', monospace; font-size: 0.7rem;
             letter-spacing: 1px; text-align: center;
             border: 1px solid rgba(0, 240, 255, 0.1);
             border-radius: 4px; padding: 4px 8px; margin-bottom: 10px;">
            ⚡ CACHE: {cache_stats['total_cached']} RESPONSES
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="color: #39ff14; font-family: 'Courier New', monospace;
             letter-spacing: 2px; font-size: 0.9rem; margin-bottom: 5px;">
            🔍 SEARCH ANY LOCATION
        </div>
        """, unsafe_allow_html=True)
        search_query = st.text_input(
            "Address or 'lat,lon'",
            placeholder="e.g. Kudat or 6.88,116.84",
            key="search_query",
            label_visibility="collapsed")
        if search_query and st.button("🔍 SEARCH", key="search_btn",
                                      use_container_width=True):
            parsed = parse_coordinates(search_query)
            if parsed:
                set_current_location(Location(
                    lat=parsed['lat'], lon=parsed['lon'], name=parsed['display_name']))
                st.success(f"📍 {parsed['display_name']}")
                st.rerun()
            else:
                with st.spinner("Searching address..."):
                    result = geocode_query(search_query)
                if result:
                    set_current_location(Location(
                        lat=result['lat'], lon=result['lon'],
                        name=result['display_name'][:80]))
                    st.success(f"📍 {result['display_name'][:60]}...")
                    st.rerun()
                else:
                    st.error("Not found. Try 'lat,lon' or full address.")

        st.divider()
        st.markdown("""
        <div style="color: #00f0ff; font-family: 'Courier New', monospace;
             letter-spacing: 2px; font-size: 0.9rem; margin-bottom: 10px;">
            ⚡ LOCATION SELECTOR
        </div>
        """, unsafe_allow_html=True)
        locations, region = render_region_sub_selector()
        quick_location = st.selectbox("Select Location", list(locations.keys()),
                                      index=0, key="quick_location")
        if st.button("⚡ GO TO LOCATION", use_container_width=True, key="go_location"):
            coords = locations[quick_location]
            set_current_location(Location(
                lat=coords[0], lon=coords[1], name=quick_location))
            st.rerun()
        st.caption("Or click on the map to select any location")
        st.divider()

        st.markdown("""
        <div style="color: #00f0ff; font-family: 'Courier New', monospace;
             letter-spacing: 2px; font-size: 0.9rem; margin-bottom: 10px;">
            🗺️ MAP SETTINGS
        </div>
        """, unsafe_allow_html=True)
        basemap_choice = st.radio(
            "Map Style",
            options=["🗺️ OpenStreetMap", "🛰️ Satellite"],
            index=0 if st.session_state.basemap_choice == "OpenStreetMap" else 1,
            horizontal=True, label_visibility="collapsed", key="basemap_radio")
        if "Satellite" in basemap_choice:
            st.session_state.basemap_choice = "Satellite"
        else:
            st.session_state.basemap_choice = "OpenStreetMap"
        st.session_state.show_radius_circle = st.checkbox(
            "Show Search Radius", value=True, key="show_radius")
        st.session_state.show_corridor = st.checkbox(
            "🌊 Show Launch Corridor", value=True, key="show_corridor_cb")
        st.session_state.show_heatmap = st.checkbox(
            "🔥 Show Suitability Heatmap (after Compare All)",
            value=False, key="show_heatmap_cb")
        st.divider()

        st.markdown("""
        <div style="color: #00f0ff; font-family: 'Courier New', monospace;
             letter-spacing: 2px; font-size: 0.9rem; margin-bottom: 10px;">
            ⚙️ ANALYSIS PARAMETERS
        </div>
        """, unsafe_allow_html=True)
        radius = st.slider("Assessment Radius (m)", 2000, 20000, 10000, 1000,
                           key="radius")
        st.divider()

        st.markdown("""
        <div style="color: #00f0ff; font-family: 'Courier New', monospace;
             letter-spacing: 2px; font-size: 0.9rem; margin-bottom: 10px;">
            📊 SITE RANKING
        </div>
        """, unsafe_allow_html=True)
        if st.session_state.current_results:
            result_data = st.session_state.current_results
            if 'suitability_percentage' in result_data:
                pct = result_data['suitability_percentage']
                rating = result_data['rating']
                color = ("#39ff14" if pct >= 80 else "#00f0ff" if pct >= 65
                         else "#ff2d95" if pct >= 50 else "#ff6600")
                st.markdown(f"""
                <div style="text-align: center; padding: 15px; border: 1px solid rgba(0, 240, 255, 0.2);
                     border-radius: 8px; background: rgba(0, 240, 255, 0.05);">
                    <div style="font-size: 2.5rem; font-weight: 900; color: {color};
                         font-family: 'Courier New', monospace;">{pct}%</div>
                    <div style="color: #d0d0e8; font-family: 'Courier New', monospace;
                         letter-spacing: 2px; font-size: 0.8rem;">{rating}</div>
                    <div style="color: #8080a0; font-family: 'Courier New', monospace;
                         font-size: 0.7rem; margin-top: 5px;">
                        {result_data['recommendation'][:50]}...</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Run an analysis to see site ranking")
        if st.button("🔄 COMPARE ALL", use_container_width=True, key="compare_all"):
            st.session_state.comparison_mode = True
            st.rerun()
        if st.button("🧹 CLEAR", use_container_width=True, key="clear_results"):
            st.session_state.current_results = None
            st.session_state.reasoning_log = []
            st.session_state.candidate_scores = {}
            st.session_state.wind_history = None
            st.success("Results cleared!")
            st.rerun()
        if st.button("🗑️ CLEAR CACHE", use_container_width=True, key="clear_cache"):
            api_cache.clear()
            st.success("Cache cleared!")
            st.rerun()
        st.divider()

        st.markdown("""
        <div style="color: #00f0ff; font-family: 'Courier New', monospace;
             letter-spacing: 2px; font-size: 0.9rem; margin-bottom: 10px;">
            🧠 AGENT MEMORY
        </div>
        """, unsafe_allow_html=True)
        stats = st.session_state.agent.memory_repo.get_analysis_stats()
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div style="text-align: center; padding: 8px; border: 1px solid rgba(0, 240, 255, 0.1);
                 border-radius: 4px;">
                <div style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.6rem;
                     letter-spacing: 1px;">ANALYSES</div>
                <div style="color: #00f0ff; font-family: 'Courier New', monospace;
                     font-size: 1.2rem; font-weight: bold;">{stats['total_analyses']}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 8px; border: 1px solid rgba(0, 240, 255, 0.1);
                 border-radius: 4px;">
                <div style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.6rem;
                     letter-spacing: 1px;">SUCCESS RATE</div>
                <div style="color: #39ff14; font-family: 'Courier New', monospace;
                     font-size: 1.2rem; font-weight: bold;">{stats['success_rate']*100:.0f}%</div>
            </div>
            """, unsafe_allow_html=True)
        if st.button("🗑️ CLEAR MEMORY", use_container_width=True, key="clear_memory"):
            Path("spaceportvbase_memory.db").unlink(missing_ok=True)
            st.session_state.agent = GeoAIAgent()
            st.session_state.analysis_history = []
            st.session_state.current_results = None
            st.session_state.reasoning_log = []
            st.session_state.candidate_scores = {}
            st.success("All memory cleared!")
            st.rerun()
        return {'radius': radius}


def render_map(params):
    region_name = "Borneo" if st.session_state.active_region == "borneo" else "West Malaysia"
    st.subheader(f"🗺️ {region_name} Spaceport Site Map")

    if st.session_state.active_region == "borneo":
        default_center = [5.0, 117.0]
    else:
        default_center = [4.2, 102.0]

    center = default_center
    location_name = region_name
    current_loc = get_current_location()
    if current_loc:
        center = [current_loc.lat, current_loc.lon]
        location_name = current_loc.name or f"{region_name} Location"

    basemap_choice = st.session_state.get('basemap_choice', 'OpenStreetMap')
    tiles_url = get_tiles_for_basemap(basemap_choice)
    try:
        if basemap_choice == "Satellite":
            m = folium.Map(location=center, zoom_start=7, tiles=tiles_url,
                           attr='Esri World Imagery')
        else:
            m = folium.Map(location=center, zoom_start=7, tiles="OpenStreetMap")
    except Exception:
        m = folium.Map(location=center, zoom_start=7)

    if current_loc:
        marker_color = 'red'
        result_data = st.session_state.get('current_results', None)
        if result_data and 'suitability_percentage' in result_data:
            pct = result_data['suitability_percentage']
            if pct >= 80:
                marker_color = 'green'
            elif pct >= 65:
                marker_color = 'lightgreen'
            elif pct >= 50:
                marker_color = 'orange'
            elif pct >= 35:
                marker_color = 'lightred'
            else:
                marker_color = 'red'
        folium.Marker(
            center,
            popup=f"<b>🚀 {location_name}</b><br>Lat: {center[0]:.6f}<br>"
                  f"Lon: {center[1]:.6f}<br>🏝️ {region_name}, Malaysia",
            tooltip="🚀 Candidate Site - Click for details",
            icon=folium.Icon(color=marker_color, icon='rocket', prefix='fa')
        ).add_to(m)
        if st.session_state.get('show_radius_circle', True):
            radius = params.get('radius', 10000)
            folium.Circle(center, radius=radius, color='#2ecc71', fill=True,
                          fillColor='#2ecc71', fillOpacity=0.1, weight=2,
                          tooltip=f"Assessment radius: {radius}m").add_to(m)

        if st.session_state.get('show_corridor', True):
            corridor = compute_launch_azimuth(center[0], center[1])
            poly_coords = compute_corridor_polygon(
                center[0], center[1],
                corridor['azimuth_deg'],
                corridor['corridor_length_km'],
                width_km=20.0)
            folium.Polygon(
                locations=poly_coords,
                color='#39ff14',
                weight=2,
                fill=True,
                fillColor='#39ff14',
                fillOpacity=0.12,
                tooltip=f"🌊 Launch Corridor → {corridor['direction_label']}"
            ).add_to(m)
            end_pt = poly_coords[2]
            folium.PolyLine(
                locations=[(center[0], center[1]), end_pt],
                color='#39ff14', weight=3, opacity=0.8, dash_array='10,5'
            ).add_to(m)

    result_data = st.session_state.get('current_results', None)
    if result_data and 'suitability_percentage' in result_data:
        pct = result_data['suitability_percentage']
        rating = result_data.get('rating', 'Unknown')
        recommendation = result_data.get('recommendation', '')
        if pct >= 80:
            color = 'green'
        elif pct >= 65:
            color = 'lightgreen'
        elif pct >= 50:
            color = 'orange'
        elif pct >= 35:
            color = 'lightred'
        else:
            color = 'red'
        folium.Circle(center, radius=params.get('radius', 10000), color=color,
                      fill=True, fillColor=color, fillOpacity=0.15, weight=3,
                      tooltip=f"🚀 Suitability: {rating} ({pct}%)\n{recommendation}").add_to(m)

    if st.session_state.get('show_heatmap', False):
        scores = st.session_state.get('candidate_scores', {})
        if scores:
            heat_data = []
            candidates = get_current_candidates()
            for site_name, score in scores.items():
                if site_name in candidates:
                    coords = candidates[site_name]
                    heat_data.append([coords[0], coords[1], float(score) / 100.0])
            if heat_data:
                HeatMap(heat_data, radius=35, blur=25, min_opacity=0.3,
                        gradient={0.3: '#ff2d95', 0.5: '#ffe84d', 0.7: '#00f0ff', 1.0: '#39ff14'}
                        ).add_to(m)
        else:
            st.caption("ℹ️ Heatmap appears after clicking **Compare All** once.")

    try:
        Fullscreen(position='topleft').add_to(m)
    except Exception:
        pass
    try:
        MiniMap(toggle_display=True, position='bottomright').add_to(m)
    except Exception:
        pass
    try:
        MousePosition(position='bottomleft', prefix=f'{region_name} Coords: ').add_to(m)
    except Exception:
        pass

    map_data = st_folium(m, width=None, height=500, use_container_width=True,
                         key="main_map")
    if map_data and map_data.get('last_clicked'):
        clicked_lat = map_data['last_clicked']['lat']
        clicked_lon = map_data['last_clicked']['lng']
        current = get_current_location()
        if (current is None or
                abs(current.lat - clicked_lat) > 0.0001 or
                abs(current.lon - clicked_lon) > 0.0001):
            set_current_location(Location(
                lat=clicked_lat, lon=clicked_lon,
                name=f"{region_name} Location"))
            st.rerun()

    if st.session_state.get('show_corridor', True):
        corridor = compute_launch_azimuth(center[0], center[1])
        st.markdown(f"""
        <div class="corridor-box">
            <div style="color: #39ff14; font-family: 'Courier New', monospace;
                 font-size: 0.85rem; letter-spacing: 2px; font-weight: bold;">
                🌊 LAUNCH CORRIDOR
            </div>
            <div style="color: #ffffff; font-family: 'Courier New', monospace;
                 font-size: 0.8rem; margin-top: 5px;">
                <b>Direction:</b> {corridor['direction_label']}<br>
                <b>Azimuth:</b> {corridor['azimuth_deg']:.0f}°<br>
                <b>Corridor length:</b> {corridor['corridor_length_km']} km<br>
                <b>Safety:</b> {corridor['safety_note']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    if result_data and 'suitability_percentage' in result_data:
        if result_data.get('used_osm', False):
            st.success(f"🚀 {result_data['rating']} Suitability: "
                       f"{result_data['suitability_percentage']}% (🌐 OSM + 🌤️ Weather)")
        else:
            st.success(f"🚀 {result_data['rating']} Suitability: "
                       f"{result_data['suitability_percentage']}% (📍 Geographic Rules)")
        st.info(f"💡 {result_data['recommendation']}")


def render_query_interface(params):
    region_name = "Borneo" if st.session_state.active_region == "borneo" else "West Malaysia"
    st.subheader("💬 Natural Language Query")
    with st.expander("💡 Example Spaceport Queries", expanded=False):
        st.markdown(f"""
        **🚀 Spaceport Site Selection ({region_name}):**
        - "Find the best location for a spaceport in {region_name}"
        - "Which site has the best launch characteristics?"
        - "Evaluate this site for rocket launch facilities"
        - "Compare all candidate sites for spaceport development"
        - "What are the advantages of this site for a spaceport?"

        **📊 Site Suitability:**
        - "Assess flood risk at this location"
        - "What's the elevation here?"
        - "Check infrastructure access"
        - "Is this area suitable for a launch facility?"
        - "How windy is this site?"
        """)
    query = st.text_area("Describe what you want to analyse for spaceport site selection:",
                         placeholder=f"e.g., Find the best location for a spaceport in {region_name}",
                         height=100, key="query_input")
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        analyse_btn = st.button("🚀 ANALYSE SITE", type="primary",
                                use_container_width=True, key="analyse_btn")
    with col2:
        clear_btn = st.button("🧹 CLEAR", use_container_width=True, key="clear_query_btn")
    if clear_btn:
        st.session_state.current_results = None
        st.session_state.reasoning_log = []
        st.rerun()
    if analyse_btn and get_current_location():
        with st.spinner("🧠 HYBRID: INSTANT results + OSM + weather..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            def update_progress(progress, status):
                progress_bar.progress(progress)
                status_text.text(status)
            result = st.session_state.agent.execute_analysis(
                get_current_location(),
                query if query else "Evaluate this site for spaceport development",
                params,
                st.session_state.active_region,
                progress_callback=update_progress)
            st.session_state.analysis_history.append(result)
            st.session_state.reasoning_log = result.steps
            st.session_state.current_results = result.final_result
            st.session_state.wind_history = None
            st.session_state.wind_history_key = None
            progress_bar.empty()
            status_text.empty()
            if result.success:
                st.success(f"✅ Spaceport site analysis complete in {result.total_time:.2f}s")
                st.rerun()
            else:
                st.error("❌ Analysis failed. Check reasoning log for details.")
    elif analyse_btn and not get_current_location():
        st.warning("Please select a location first!")


def render_reasoning_log():
    st.subheader("🧠 Agent Reasoning (Chain of Thought)")
    if not st.session_state.reasoning_log:
        st.info("Run a spaceport site analysis to see the agent's reasoning process.")
        return
    for step in st.session_state.reasoning_log:
        status_icon = ("✅" if step.status == "completed"
                       else "❌" if step.status == "failed" else "⏳")
        with st.expander(f"{status_icon} Step {step.step_number}: {step.name}",
                         expanded=True):
            st.write(f"**Reasoning:** {step.reasoning}")
            if step.execution_time > 0:
                st.write(f"**Execution Time:** {step.execution_time:.3f}s")
            if step.result and step.name.startswith("Execute"):
                st.json(step.result)


def render_results():
    region_name = "Borneo" if st.session_state.active_region == "borneo" else "West Malaysia"
    st.subheader(f"🚀 {region_name} Spaceport Site Analysis Results")
    history = st.session_state.get('analysis_history', [])
    if not history:
        st.info("No analysis results yet. Run a spaceport site analysis to see results here.")
        return
    last_result = history[-1]
    if not last_result.final_result:
        st.warning("No results available.")
        return
    result_data = last_result.final_result
    if not result_data.get('success', False):
        st.error(f"Analysis failed: {result_data.get('error', 'Unknown error')}")
        return
    if 'suitability_percentage' in result_data:
        if result_data.get('used_osm', False):
            st.success("🌐 **HYBRID: OSM + Weather + Geographic Rules**")
        else:
            st.success("📍 **Geographic Rules (INSTANT)** - OSM unavailable")

        if result_data.get('penalty_applied', 0) > 0:
            with st.expander(f"⚠️ Score Penalty Applied: -{result_data['penalty_applied']}%"):
                st.write(f"**Base score:** {result_data.get('base_percentage', 0)}%")
                st.write(f"**Penalty:** -{result_data['penalty_applied']}%")
                st.write("**Reasons:**")
                for r in result_data.get('penalty_reasons', []):
                    st.warning(r)
                st.write(f"**Final score:** {result_data['suitability_percentage']}%")

        if 'data_source_details' in result_data:
            with st.expander("📊 Data Sources Used"):
                for detail in result_data['data_source_details']:
                    if '🌐' in detail:
                        st.success(f"🌐 {detail}")
                    elif 'Wind' in detail:
                        st.info(f"🌬️ {detail}")
                    elif 'Geographic' in detail:
                        st.info(f"📍 {detail}")
                    elif 'Fallback' in detail:
                        st.warning(f"⚠️ {detail}")
                    else:
                        st.success(f"✅ {detail}")

        weather = result_data.get('weather')
        if weather:
            with st.expander("🌤️ Live Weather Data (Open-Meteo)", expanded=False):
                wc1, wc2, wc3 = st.columns(3)
                with wc1:
                    if weather.get('wind_speed_ms') is not None:
                        st.metric("💨 Wind Speed", f"{weather['wind_speed_ms']:.1f} m/s",
                                  delta=weather.get('wind_rating', ''))
                    if weather.get('temperature_c') is not None:
                        st.metric("🌡️ Temperature", f"{weather['temperature_c']:.1f}°C")
                with wc2:
                    if weather.get('wind_gust_ms') is not None:
                        st.metric("🌪️ Wind Gust", f"{weather['wind_gust_ms']:.1f} m/s")
                    if weather.get('humidity_pct') is not None:
                        st.metric("💧 Humidity", f"{weather['humidity_pct']:.0f}%")
                with wc3:
                    if weather.get('wind_direction_deg') is not None:
                        dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
                        deg = weather['wind_direction_deg']
                        compass = dirs[int((deg + 22.5) % 360 // 45)]
                        st.metric("🧭 Wind Direction", f"{compass} ({deg:.0f}°)")
                if weather.get('wind_explanation'):
                    st.caption(f"**Assessment:** {weather['wind_explanation']}")

        if result_data.get('used_osm', False) and result_data.get('osm_data'):
            with st.expander("🌐 OSM Data Found (Up-to-Date)"):
                st.json(result_data['osm_data'])

        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        with c1:
            st.metric("🚀 Spaceport Suitability",
                      f"{result_data['suitability_percentage']}%",
                      delta=f"{result_data['rating']} {result_data['rating_emoji']}")
            st.caption(result_data['recommendation'])
        with c2:
            st.metric("Elevation", f"{result_data.get('elevation_m', 0):.0f}m")
        with c3:
            st.metric("Latitude", f"{result_data.get('lat_deg', 0):.1f}°N")
        with c4:
            ws = result_data.get('wind_speed_ms')
            if ws is not None:
                st.metric("💨 Wind", f"{ws:.1f} m/s")
            else:
                st.metric("💨 Wind", "N/A")

        lat = result_data.get('lat_deg', 0)
        elev = result_data.get('elevation_m', 0)
        payload = compute_payload_delta_v(lat, elev)
        st.markdown(f"""
        <div class="payload-box">
            <div style="color: #00f0ff; font-family: 'Courier New', monospace;
                 font-size: 1rem; font-weight: bold; letter-spacing: 2px;
                 margin-bottom: 8px;">
                🚀 PAYLOAD / DELTA-V ESTIMATE
            </div>
            <div style="color: #ffffff; font-family: 'Courier New', monospace;
                 font-size: 0.85rem; line-height: 1.7;">
                <b>Rotation bonus:</b> +{payload['dv_bonus_ms']} m/s
                (vs Cape Canaveral)<br>
                <b>LEO payload:</b> ~{payload['leo_payload_t']} t
                <span style="color:#39ff14;">(+{payload['pct_improvement']}%)</span><br>
                <b>GTO payload:</b> ~{payload['gto_payload_t']} t<br>
                <b>Earth rotation speed:</b> {payload['rotation_speed_ms']} m/s
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("📅 30-Day Historical Wind (Open-Meteo Archive)", expanded=False):
            loc_lat = None
            loc_lon = None
            try:
                loc_str = result_data.get('location', '')
                if '(' in loc_str and ')' in loc_str:
                    coords_part = loc_str.split('(')[1].split(')')[0]
                    lat_str, lon_str = coords_part.split(',')
                    loc_lat = float(lat_str.strip())
                    loc_lon = float(lon_str.strip())
            except Exception:
                pass

            if loc_lat is None or loc_lon is None:
                st.info("Cannot extract coordinates from result.")
            else:
                cache_key = f"{loc_lat:.4f}_{loc_lon:.4f}"
                if st.session_state.get('wind_history_key') != cache_key:
                    with st.spinner("Fetching 30-day wind history..."):
                        hist = fetch_wind_history(loc_lat, loc_lon, days=30)
                    st.session_state.wind_history = hist
                    st.session_state.wind_history_key = cache_key

                hist = st.session_state.get('wind_history')
                if hist:
                    wc1, wc2, wc3 = st.columns(3)
                    with wc1:
                        st.metric("💨 Avg Max Wind", f"{hist['mean_wind']:.1f} m/s")
                    with wc2:
                        st.metric("🌪️ Peak Wind", f"{hist['max_wind']:.1f} m/s")
                    with wc3:
                        st.metric("✅ Calm Days (<6 m/s)",
                                  f"{hist['calm_days']}/{hist['total_days']}")
                    if len(hist['df']) > 0:
                        chart_df = hist['df'].set_index('date')[['wind_max', 'gust_max']]
                        chart_df.columns = ['Daily Max Wind (m/s)', 'Daily Max Gust (m/s)']
                        st.line_chart(chart_df)
                        st.caption("Source: Open-Meteo Archive API (free)")
                else:
                    st.warning("Could not fetch historical wind. API may be temporarily unavailable.")

        st.write("---")
        st.write("**Detailed Scoring Breakdown:**")
        details = result_data.get('details', {})
        scores = result_data.get('scores', {})
        score_data = []
        for key, detail in details.items():
            weight = detail.get('weight', 0)
            score = scores.get(key, 0)
            weighted = score * weight
            source = detail.get('source', 'Unknown')
            if 'Geographic' in source:
                source_emoji = '📍'
            elif 'Live' in source:
                source_emoji = '✅'
            elif 'Open-Meteo' in source:
                source_emoji = '🌤️'
            elif 'Fallback' in source:
                source_emoji = '⚠️'
            else:
                source_emoji = 'ℹ️'
            score_data.append({
                'Criteria': key.replace('_', ' ').title(),
                'Score': f"{score:.1f}/5",
                'Value': detail.get('value', 'N/A'),
                'Weight': f"{weight*100:.0f}%",
                'Weighted': f"{weighted:.2f}",
                'Source': f"{source_emoji} {source[:35]}{'...' if len(source) > 35 else ''}"
            })
        df = pd.DataFrame(score_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        chart_data = pd.DataFrame([
            {'Criteria': row['Criteria'], 'Score': float(row['Score'].split('/')[0])}
            for row in score_data])
        st.bar_chart(chart_data.set_index('Criteria'))

        st.write("---")
        st.write("**💾 Save & Export**")
        action_col1, action_col2 = st.columns([1, 2])

        _lat, _lon = lat, 0.0
        try:
            if '(' in result_data.get('location', ''):
                coords_part = result_data['location'].split('(')[1].split(')')[0]
                _lat_s, _lon_s = coords_part.split(',')
                _lat = float(_lat_s.strip())
                _lon = float(_lon_s.strip())
        except Exception:
            pass

        site_label = result_data.get('location', 'Unknown').split('(')[0].strip()
        already_saved = is_favorite(site_label, _lat, _lon)
        region_name = "Borneo" if st.session_state.active_region == "borneo" else "West Malaysia"

        with action_col1:
            if already_saved:
                st.success("⭐ Saved!")
            else:
                if st.button("⭐ Save to Favorites", use_container_width=True,
                             key="save_fav_btn"):
                    ok = add_favorite(site_label, _lat, _lon, region_name.lower(),
                                      result_data.get('suitability_percentage', 0),
                                      result_data.get('rating', ''))
                    if ok:
                        st.success("⭐ Added to favorites!")
                        st.rerun()
                    else:
                        st.info("Already in favorites")

        with action_col2:
            st.caption("⬇️ **Download Report**")
            dl1, dl2, dl3 = st.columns(3)
            with dl1:
                report_txt = generate_report_text(result_data)
                st.download_button(
                    "📄 TXT",
                    data=report_txt,
                    file_name=f"starbasev_report_{site_label[:20].replace(' ','_')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="dl_txt")
            with dl2:
                csv_buf = StringIO()
                df.to_csv(csv_buf, index=False)
                st.download_button(
                    "📊 CSV",
                    data=csv_buf.getvalue(),
                    file_name=f"starbasev_scores_{site_label[:20].replace(' ','_')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="dl_csv")
            with dl3:
                def _make_json_safe(o):
                    if isinstance(o, (str, int, float, bool)) or o is None:
                        return o
                    if isinstance(o, dict):
                        return {k: _make_json_safe(v) for k, v in o.items()}
                    if isinstance(o, (list, tuple)):
                        return [_make_json_safe(v) for v in o]
                    return str(o)
                try:
                    json_str = json.dumps(
                        _make_json_safe(result_data),
                        indent=2, ensure_ascii=False)
                except Exception:
                    json_str = json.dumps(
                        {'location': result_data.get('location'),
                         'suitability_percentage': result_data.get('suitability_percentage')},
                        indent=2)
                st.download_button(
                    "🔗 JSON",
                    data=json_str,
                    file_name=f"starbasev_full_{site_label[:20].replace(' ','_')}.json",
                    mime="application/json",
                    use_container_width=True,
                    key="dl_json")

        st.write("---")
        st.write("**📋 Detailed Recommendation Strategy**")
        recommendations = generate_recommendation_strategy(result_data)
        risk = recommendations.get('risk_level', 'Unknown')
        risk_color = ('#ff2d95' if risk in ('High', 'Very High')
                      else '#39ff14' if risk == 'Low' else '#ffe84d')

        st.markdown(f"""
        <div class="recommendation-container">
            <div class="recommendation-title">🎯 Overall Feasibility</div>
            <div style="color: #ffffff; font-family: 'Courier New', monospace;
                 font-size: 1.1rem; padding: 10px;">
                {recommendations.get('overall_feasibility', 'Assessment not available')}
            </div>
            <div style="display: flex; gap: 20px; margin-top: 10px; flex-wrap: wrap;">
                <div style="color: #8080a0; font-family: 'Courier New', monospace;
                     font-size: 0.8rem; border: 1px solid rgba(0,240,255,0.1);
                     padding: 8px 15px; border-radius: 8px;">
                    💰 Investment Required: <span style="color: #00f0ff; font-weight: bold;">
                    {recommendations.get('investment_required', 'Unknown')}</span>
                </div>
                <div style="color: #8080a0; font-family: 'Courier New', monospace;
                     font-size: 0.8rem; border: 1px solid rgba(255,45,149,0.3);
                     padding: 8px 15px; border-radius: 8px;">
                    ⚠️ Risk Level: <span style="color: {risk_color}; font-weight: bold;">
                    {risk}</span>
                </div>
                <div style="color: #8080a0; font-family: 'Courier New', monospace;
                     font-size: 0.8rem; border: 1px solid rgba(255,45,149,0.3);
                     padding: 8px 15px; border-radius: 8px;">
                    🚨 Critical Actions: <span style="color: #ff2d95; font-weight: bold;">
                    {recommendations.get('critical_action_count', 0)}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        for bucket, title in [
            ('immediate_actions', '🔴 IMMEDIATE ACTIONS (0-6 Months)'),
            ('short_term_actions', '🟡 SHORT-TERM ACTIONS (6-18 Months)'),
            ('long_term_actions', '🟢 LONG-TERM ACTIONS (18-36 Months)')]:
            if recommendations[bucket]:
                st.markdown(f"""
                <div class="recommendation-container">
                    <div class="recommendation-title">{title}</div>
                """, unsafe_allow_html=True)
                for action in recommendations[bucket]:
                    st.markdown(f"""
                    <div class="recommendation-item">
                        <span class="icon">{action.get('priority', '')}</span>
                        {action['text']}
                        <span style="float: right; color: #8080a0; font-size: 0.8rem;">
                            {action.get('cost', '')}</span>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        st.write("---")
        st.write("**📋 Summary**")
        recommendation = result_data.get('recommendation', '')
        rating = result_data.get('rating', 'Unknown')
        emoji = result_data.get('rating_emoji', '')
        if rating in ['Excellent', 'Good']:
            st.success(f"{emoji} **{rating}** - {recommendation}")
        elif rating == 'Moderate':
            st.warning(f"{emoji} **{rating}** - {recommendation}")
        else:
            st.error(f"{emoji} **{rating}** - {recommendation}")

    elif 'amenities' in result_data:
        amenity_type = result_data.get('amenity_type', 'location')
        count = result_data.get('count', 0)
        radius = result_data.get('radius', 0)
        location_info = result_data.get('location', 'Location')
        st.write(f"**Found {count} {amenity_type}(s) within {radius}m in {location_info}**")
        if result_data['amenities']:
            df = pd.DataFrame(result_data['amenities'])
            display_cols = [col for col in ['name', 'lat', 'lon', 'type'] if col in df.columns]
            st.dataframe(df[display_cols], use_container_width=True)


def render_comparison_mode():
    region_name = "Borneo" if st.session_state.active_region == "borneo" else "West Malaysia"
    candidates = get_current_candidates()
    st.subheader(f"🔄 Site Comparison Dashboard ({region_name})")
    with st.spinner(f"Analysing all {region_name} candidate sites (HYBRID + Weather)..."):
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        for i, (name, coords) in enumerate(candidates.items()):
            status_text.text(f"Analysing: {name}")
            progress_bar.progress((i + 1) / len(candidates))
            location = Location(lat=coords[0], lon=coords[1], name=name)
            params = {'radius': 10000}
            try:
                if st.session_state.active_region == "borneo":
                    strategy = BorneoStrategySelector.get_strategy('spaceport')
                else:
                    strategy = WestStrategySelector.get_strategy('spaceport')
                result = strategy.analyse(location, params)
                if result.get('success'):
                    results.append({
                        'Site': name,
                        'Suitability %': result['suitability_percentage'],
                        'Rating': result['rating'],
                        'Elevation (m)': result.get('elevation_m', 0),
                        'Wind (m/s)': (result.get('wind_speed_ms')
                                       if result.get('wind_speed_ms') is not None else 'N/A'),
                        'Flood Risk': result.get('flood_risk', 'Unknown'),
                        'Latitude (°)': result.get('lat_deg', 0),
                        'Method': '🌐 OSM + 🌤️' if result.get('used_osm', False) else '📍 Geographic',
                        'Recommendation': result['recommendation'][:50] + '...',
                        'Data': result
                    })
            except Exception as e:
                results.append({
                    'Site': name, 'Suitability %': 0, 'Rating': 'Error',
                    'Elevation (m)': 0, 'Wind (m/s)': 'N/A',
                    'Flood Risk': 'Unknown', 'Latitude (°)': abs(coords[0]),
                    'Method': 'Error', 'Recommendation': f"Error: {str(e)[:50]}",
                    'Data': None
                })
        progress_bar.empty()
        status_text.empty()
        if results:
            df = pd.DataFrame(results)
            df_sorted = df.sort_values('Suitability %', ascending=False)
            st.write(f"**📊 Comparison of {len(results)} Candidate Sites**")
            top_site = df_sorted.iloc[0]
            st.success(f"🚀 **Top Recommended Site: {top_site['Site']}** "
                       f"({top_site['Suitability %']:.1f}%)")
            st.caption(top_site['Recommendation'])
            display_cols = ['Site', 'Suitability %', 'Rating', 'Elevation (m)',
                            'Wind (m/s)', 'Flood Risk', 'Latitude (°)', 'Method']
            st.dataframe(df_sorted[display_cols], use_container_width=True, hide_index=True)
            chart_data = df_sorted[['Site', 'Suitability %']].set_index('Site')
            st.bar_chart(chart_data)
            st.session_state.candidate_scores = {
                row['Site']: row['Suitability %'] for _, row in df.iterrows()}
            st.write("---")
            st.write("**🗺️ Site Map with Suitability Scores**")
            st.caption("💡 Turn on **🔥 Show Suitability Heatmap** in the sidebar for a heatmap view.")
            basemap_choice = st.session_state.get('basemap_choice', 'OpenStreetMap')
            tiles_url = get_tiles_for_basemap(basemap_choice)
            if st.session_state.active_region == "borneo":
                map_center = [5.0, 117.0]
            else:
                map_center = [4.2, 102.0]
            if basemap_choice == "Satellite":
                m = folium.Map(location=map_center, zoom_start=7,
                               tiles=tiles_url, attr='Esri World Imagery')
            else:
                m = folium.Map(location=map_center, zoom_start=7, tiles="OpenStreetMap")
            for _, row in df.iterrows():
                name = row['Site']
                score = row['Suitability %']
                if score >= 80:
                    color = 'green'
                elif score >= 65:
                    color = 'lightgreen'
                elif score >= 50:
                    color = 'orange'
                elif score >= 35:
                    color = 'lightred'
                else:
                    color = 'red'
                coords = candidates.get(name, (0, 0))
                folium.Marker(
                    coords,
                    popup=f"<b>{name}</b><br>Suitability: {score:.1f}%<br>"
                          f"Rating: {row['Rating']}<br>Wind: {row['Wind (m/s)']} m/s<br>"
                          f"Method: {row['Method']}",
                    tooltip=f"{name}: {score:.1f}%",
                    icon=folium.Icon(color=color, icon='rocket', prefix='fa')
                ).add_to(m)
            if st.session_state.get('show_heatmap', False):
                heat_data = []
                for _, row in df.iterrows():
                    name = row['Site']
                    if name in candidates:
                        coords = candidates[name]
                        heat_data.append([coords[0], coords[1], float(row['Suitability %']) / 100.0])
                if heat_data:
                    HeatMap(heat_data, radius=35, blur=25, min_opacity=0.3,
                            gradient={0.3: '#ff2d95', 0.5: '#ffe84d', 0.7: '#00f0ff', 1.0: '#39ff14'}
                            ).add_to(m)
            try:
                Fullscreen(position='topleft').add_to(m)
            except Exception:
                pass
            st_folium(m, width=None, height=400, use_container_width=True,
                      key="comparison_map")
            selected_site = st.selectbox("Select a site for detailed analysis:",
                                        df_sorted['Site'].tolist(),
                                        key="compare_select")
            if selected_site:
                coords = candidates[selected_site]
                set_current_location(Location(
                    lat=coords[0], lon=coords[1], name=selected_site))
                st.session_state.comparison_mode = False
                st.rerun()


def render_favorites_explorer(region_filter: Optional[str] = None):
    st.subheader("⭐ Saved Favorites")
    favs = get_favorites()
    if region_filter:
        favs = [f for f in favs if f['region'] == region_filter.lower()]
    if not favs:
        st.info("No favorites saved yet. Click ⭐ Save to Favorites on any analysis result.")
        return
    st.write(f"**{len(favs)} saved site(s)**")
    for f in favs:
        with st.expander(f"⭐ {f['name']} — {f['score']:.1f}% ({f['rating']})"):
            st.write(f"**Coordinates:** {f['lat']:.4f}, {f['lon']:.4f}")
            st.write(f"**Region:** {f['region'].title()}")
            st.write(f"**Added:** {f['added_at'][:19]}")
            c1, c2 = st.columns(2)
            with c1:
                if st.button(f"📍 Load this site", key=f"load_fav_{f['id']}"):
                    set_current_location(Location(
                        lat=f['lat'], lon=f['lon'], name=f['name']))
                    st.rerun()
            with c2:
                if st.button(f"🗑️ Remove", key=f"del_fav_{f['id']}"):
                    remove_favorite(f['id'])
                    st.success("Removed")
                    st.rerun()


def render_memory_explorer():
    st.subheader("💾 Memory Explorer")
    tab1, tab2 = st.tabs(["Past Analyses", "Learned Parameters"])
    agent = st.session_state.agent
    with tab1:
        all_analyses = agent.memory_repo.get_all_analyses(limit=20)
        if all_analyses:
            st.write(f"**{len(all_analyses)} past analyses stored**")
            for entry in all_analyses:
                query_preview = (entry['query'][:50] + "..."
                                 if len(entry['query']) > 50 else entry['query'])
                with st.expander(f"{'✅' if entry['success'] else '❌'} {query_preview}"):
                    st.write(f"**Query:** {entry['query']}")
                    st.write(f"**Region:** {entry.get('region', 'unknown')}")
                    st.write(f"**Success:** {'✅ Yes' if entry['success'] else '❌ No'}")
                    st.write(f"**Execution Time:** {entry['execution_time']:.2f}s")
                    st.write(f"**Timestamp:** {entry['timestamp']}")
        else:
            st.info("No past analyses stored yet.")
    with tab2:
        try:
            conn = sqlite3.connect("spaceportvbase_memory.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM learned_parameters ORDER BY success_rate DESC")
            rows = cursor.fetchall()
            conn.close()
            if rows:
                st.write(f"**{len(rows)} learned parameters**")
                df = pd.DataFrame(rows, columns=['ID', 'Analysis Type', 'Parameter',
                                                 'Value', 'Success Rate', 'Usage Count',
                                                 'Last Updated'])
                st.dataframe(df[['Analysis Type', 'Parameter', 'Value',
                                 'Success Rate', 'Usage Count']],
                             use_container_width=True)
            else:
                st.info("No learned parameters yet.")
        except Exception:
            st.info("No learned parameters yet.")

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
    init_favorites_db()
    init_session_state()

    region_name = "BORNEO" if st.session_state.active_region == "borneo" else "WEST MALAYSIA"
    region_subtitle = ("SABAH & SARAWAK · SITE SELECTOR"
                       if st.session_state.active_region == "borneo"
                       else "PENINSULAR MALAYSIA · SITE SELECTOR")

    st.markdown(f"""
    <div style="text-align: center; padding: 20px 0 10px 0;">
        <div class="main-title">🚀 STARBASEV</div>
        <div class="subtitle">{region_name} · {region_subtitle}</div>
        <div class="cyber-divider"></div>
        <div style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.7rem;
             letter-spacing: 4px; margin-top: 5px;">
            ⚡ HYBRID · OSM LIVE · 🌤️ WEATHER LIVE · INSTANT RESULTS ⚡
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.active_region == "borneo":
        total_locations = len(SABAH_LOCATIONS) + len(SARAWAK_LOCATIONS)
        total_candidates = len(BORNEO_SPACEPORT_CANDIDATES)
        regions_label = "SABAH · SARAWAK"
    else:
        total_locations = len(WEST_MALAYSIA_LOCATIONS)
        total_candidates = len(WEST_MALAYSIA_SPACEPORT_CANDIDATES)
        regions_label = "PENINSULAR MALAYSIA"

    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; padding: 8px 15px;
         border: 1px solid rgba(0, 240, 255, 0.1); border-radius: 8px;
         background: rgba(0, 240, 255, 0.03); margin-bottom: 15px;">
        <span style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.7rem;
             letter-spacing: 1px;">📍 LOCATIONS LOADED</span>
        <span style="color: #00f0ff; font-family: 'Courier New', monospace; font-size: 0.8rem;
             font-weight: bold; letter-spacing: 1px;">
             {total_locations} (+ {total_candidates} candidates)</span>
        <span style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.6rem;
             letter-spacing: 1px;">{regions_label}</span>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.get('comparison_mode', False):
        render_comparison_mode()
        if st.button("← BACK TO SINGLE SITE", key="back_single"):
            st.session_state.comparison_mode = False
            st.rerun()
        st.divider()
        return

    params = render_sidebar()

    col1, col2 = st.columns([1.5, 1])
    with col1:
        render_map(params)
        render_query_interface(params)
    with col2:
        current_loc = get_current_location()
        if current_loc:
            name = current_loc.name or f"{region_name} Location"
            st.markdown(f"""
            <div style="padding: 10px 15px; border: 1px solid rgba(0, 240, 255, 0.15);
                 border-radius: 8px; background: rgba(0, 240, 255, 0.03); margin-bottom: 15px;">
                <div style="color: #8080a0; font-family: 'Courier New', monospace;
                     font-size: 0.6rem; letter-spacing: 1px;">SELECTED LOCATION</div>
                <div style="color: #00f0ff; font-family: 'Courier New', monospace;
                     font-size: 0.9rem;">{name}</div>
                <div style="color: #8080a0; font-family: 'Courier New', monospace;
                     font-size: 0.6rem; letter-spacing: 1px;">
                    {current_loc.lat:.4f}, {current_loc.lon:.4f}
                </div>
            </div>
            """, unsafe_allow_html=True)
        render_reasoning_log()

    st.divider()

    tab_results, tab_favs, tab_mem = st.tabs(["📊 Results", "⭐ Favorites", "💾 Memory"])
    with tab_results:
        render_results()
    with tab_favs:
        region_filter = "borneo" if st.session_state.active_region == "borneo" else "west malaysia"
        render_favorites_explorer(region_filter=region_filter)
    with tab_mem:
        render_memory_explorer()

    st.markdown("""
    <div class="cyber-divider"></div>
    <div style="text-align: center; padding: 15px 0; color: #333;
         font-family: 'Courier New', monospace; font-size: 0.6rem; letter-spacing: 2px;">
        <span style="color: #00f0ff;">[</span>
        STARBASEV · CYBERPUNK EDITION · SINGLE PAGE
        <span style="color: #00f0ff;">]</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(BMC_BUTTON_HTML, unsafe_allow_html=True)


if __name__ == "__main__":
    main()