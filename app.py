import streamlit as st
import fastf1
import fastf1.plotting
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import time
import threading
import json
import os
import warnings
warnings.filterwarnings("ignore")

# ─── CACHE ──────────────────────────────────────────────────────────────────
os.makedirs("f1_cache", exist_ok=True)
fastf1.Cache.enable_cache("f1_cache")

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="F1 2026 — Live Season Hub",
    page_icon="🏎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── TEAM / DRIVER COLORS ────────────────────────────────────────────────────
TEAM_COLORS = {
    "Mercedes":         "#00D2BE",
    "Ferrari":          "#DC143C",
    "Red Bull Racing":  "#3671C6",
    "Red Bull":         "#3671C6",
    "McLaren":          "#FF8000",
    "Aston Martin":     "#006F62",
    "Alpine":           "#0090FF",
    "Williams":         "#005AFF",
    "Racing Bulls":     "#1E41D0",
    "RB":               "#1E41D0",
    "Haas F1 Team":     "#B6BABD",
    "Haas":             "#B6BABD",
    "Kick Sauber":      "#00E48D",
    "Audi":             "#FF0000",
    "Cadillac":         "#CC0000",
}

TYRE_COLORS = {
    "SOFT":         "#e8002d",
    "MEDIUM":       "#ffd700",
    "HARD":         "#f0f0f0",
    "INTERMEDIATE": "#39b54a",
    "WET":          "#0067ff",
    "UNKNOWN":      "#555555",
}

TYRE_ABBR = {"SOFT":"S","MEDIUM":"M","HARD":"H","INTERMEDIATE":"I","WET":"W","UNKNOWN":"?"}

DRIVER_ABBR = {
    "Kimi Antonelli":"ANT","George Russell":"RUS","Charles Leclerc":"LEC",
    "Lewis Hamilton":"HAM","Lando Norris":"NOR","Oscar Piastri":"PIA",
    "Max Verstappen":"VER","Isack Hadjar":"HAD","Fernando Alonso":"ALO",
    "Lance Stroll":"STR","Carlos Sainz":"SAI","Alexander Albon":"ALB",
    "Franco Colapinto":"COL","Pierre Gasly":"GAS","Jack Doohan":"DOO",
    "Oliver Bearman":"BEA","Esteban Ocon":"OCO","Liam Lawson":"LAW",
    "Nico Hulkenberg":"HUL","Gabriel Bortoleto":"BOR","Arvid Lindblad":"LIN",
}

def tc(name):
    if not name: return "#888"
    for k,v in TEAM_COLORS.items():
        if k.lower() in name.lower(): return v
    return "#888"

def rgba(hex_color, alpha=0.15):
    h = hex_color.lstrip('#')
    r,g,b = tuple(int(h[i:i+2],16) for i in (0,2,4))
    return f"rgba({r},{g},{b},{alpha})"

# ─── 2026 CALENDAR ───────────────────────────────────────────────────────────
CALENDAR = [
    {"round":1,  "name":"Australian GP",    "circuit":"Melbourne Grand Prix Circuit", "country":"Australia 🇦🇺", "race_date":"2026-03-08", "status":"done",      "winner":"George Russell",   "team":"Mercedes"},
    {"round":2,  "name":"Chinese GP",       "circuit":"Shanghai International Circuit","country":"China 🇨🇳",     "race_date":"2026-03-15", "status":"done",      "winner":"Kimi Antonelli",   "team":"Mercedes"},
    {"round":3,  "name":"Japanese GP",      "circuit":"Suzuka International Racing",  "country":"Japan 🇯🇵",     "race_date":"2026-03-29", "status":"done",      "winner":"Kimi Antonelli",   "team":"Mercedes"},
    {"round":4,  "name":"Bahrain GP",       "circuit":"Bahrain International Circuit","country":"Bahrain 🇧🇭",   "race_date":"2026-04-12", "status":"cancelled", "winner":None,               "team":None},
    {"round":5,  "name":"Saudi Arabian GP", "circuit":"Jeddah Corniche Circuit",      "country":"Saudi Arabia 🇸🇦","race_date":"2026-04-19","status":"cancelled", "winner":None,               "team":None},
    {"round":6,  "name":"Miami GP",         "circuit":"Miami International Autodrome","country":"USA 🇺🇸",       "race_date":"2026-05-03", "status":"done",      "winner":"Kimi Antonelli",   "team":"Mercedes"},
    {"round":7,  "name":"Canadian GP",      "circuit":"Circuit Gilles-Villeneuve",    "country":"Canada 🇨🇦",    "race_date":"2026-05-24", "status":"done",      "winner":"Kimi Antonelli",   "team":"Mercedes"},
    {"round":8,  "name":"Monaco GP",        "circuit":"Circuit de Monaco",            "country":"Monaco 🇲🇨",    "race_date":"2026-06-07", "status":"upcoming",  "winner":None,               "team":None},
    {"round":9,  "name":"Spanish GP",       "circuit":"Circuit de Barcelona-Catalunya","country":"Spain 🇪🇸",    "race_date":"2026-06-14", "status":"upcoming",  "winner":None,               "team":None},
    {"round":10, "name":"Austrian GP",      "circuit":"Red Bull Ring",                "country":"Austria 🇦🇹",   "race_date":"2026-06-28", "status":"upcoming",  "winner":None,               "team":None},
    {"round":11, "name":"British GP",       "circuit":"Silverstone Circuit",          "country":"UK 🇬🇧",        "race_date":"2026-07-05", "status":"upcoming",  "winner":None,               "team":None},
    {"round":12, "name":"Belgian GP",       "circuit":"Circuit de Spa-Francorchamps", "country":"Belgium 🇧🇪",   "race_date":"2026-07-19", "status":"upcoming",  "winner":None,               "team":None},
    {"round":13, "name":"Hungarian GP",     "circuit":"Hungaroring",                  "country":"Hungary 🇭🇺",   "race_date":"2026-07-26", "status":"upcoming",  "winner":None,               "team":None},
    {"round":14, "name":"Dutch GP",         "circuit":"Circuit Park Zandvoort",       "country":"Netherlands 🇳🇱","race_date":"2026-08-23", "status":"upcoming",  "winner":None,               "team":None},
    {"round":15, "name":"Italian GP",       "circuit":"Autodromo Nazionale Monza",    "country":"Italy 🇮🇹",     "race_date":"2026-09-06", "status":"upcoming",  "winner":None,               "team":None},
    {"round":16, "name":"Spanish GP 2",     "circuit":"Madring Circuit",              "country":"Spain 🇪🇸",     "race_date":"2026-09-13", "status":"upcoming",  "winner":None,               "team":None},
    {"round":17, "name":"Azerbaijan GP",    "circuit":"Baku City Circuit",            "country":"Azerbaijan 🇦🇿", "race_date":"2026-09-26", "status":"upcoming",  "winner":None,               "team":None},
    {"round":18, "name":"Singapore GP",     "circuit":"Marina Bay Street Circuit",    "country":"Singapore 🇸🇬",  "race_date":"2026-10-11", "status":"upcoming",  "winner":None,               "team":None},
    {"round":19, "name":"United States GP", "circuit":"Circuit of the Americas",      "country":"USA 🇺🇸",       "race_date":"2026-10-25", "status":"upcoming",  "winner":None,               "team":None},
    {"round":20, "name":"Mexico City GP",   "circuit":"Autodromo Hermanos Rodriguez", "country":"Mexico 🇲🇽",    "race_date":"2026-11-01", "status":"upcoming",  "winner":None,               "team":None},
    {"round":21, "name":"São Paulo GP",     "circuit":"Autodromo Jose Carlos Pace",   "country":"Brazil 🇧🇷",    "race_date":"2026-11-08", "status":"upcoming",  "winner":None,               "team":None},
    {"round":22, "name":"Las Vegas GP",     "circuit":"Las Vegas Street Circuit",     "country":"USA 🇺🇸",       "race_date":"2026-11-22", "status":"upcoming",  "winner":None,               "team":None},
    {"round":23, "name":"Qatar GP",         "circuit":"Losail International Circuit", "country":"Qatar 🇶🇦",     "race_date":"2026-11-29", "status":"upcoming",  "winner":None,               "team":None},
    {"round":24, "name":"Abu Dhabi GP",     "circuit":"Yas Marina Circuit",           "country":"UAE 🇦🇪",       "race_date":"2026-12-06", "status":"upcoming",  "winner":None,               "team":None},
]

CIRCUIT_FACTS = {
    "Monaco GP":        {"laps":78,"length":"3.337 km","lap_record":"1:12.909 Leclerc 2021","fact":"So narrow a modern F1 car is wider than some roads. Qualifying position is almost everything."},
    "Australian GP":    {"laps":58,"length":"5.278 km","lap_record":"1:20.235 Leclerc 2022","fact":"Temporary street circuit around Albert Park Lake. Always opens the season."},
    "Chinese GP":       {"laps":56,"length":"5.451 km","lap_record":"1:32.238 Bottas 2018","fact":"Shanghai has hosted F1 since 2004. Long back straight perfect for DRS battles."},
    "Japanese GP":      {"laps":53,"length":"5.807 km","lap_record":"1:30.983 Hamilton 2019","fact":"Suzuka's figure-8 layout is unique in F1. The 130R corner is one of the most famous."},
    "Canadian GP":      {"laps":70,"length":"4.361 km","lap_record":"1:13.078 Bottas 2019","fact":"The Wall of Champions at the final chicane has claimed multiple world champions in qualifying."},
    "British GP":       {"laps":52,"length":"5.891 km","lap_record":"1:27.097 Hamilton 2020","fact":"Home of F1. Copse corner at 185mph is one of the fastest corners in the world."},
    "Spanish GP":       {"laps":66,"length":"4.675 km","lap_record":"1:16.330 Rosberg 2016","fact":"Used extensively for pre-season testing. Teams know this circuit better than any other."},
    "Italian GP":       {"laps":53,"length":"5.793 km","lap_record":"1:21.046 Barrichello 2004","fact":"The Temple of Speed. Monza has the highest average speeds of any F1 circuit."},
    "Belgian GP":       {"laps":44,"length":"7.004 km","lap_record":"1:41.252 Bottas 2018","fact":"Spa's Eau Rouge/Raidillon complex is the most famous corner sequence in motorsport."},
    "Singapore GP":     {"laps":62,"length":"4.940 km","lap_record":"1:35.867 Leclerc 2023","fact":"The only night race in F1. Brutally hot and humid. Highest chance of Safety Car."},
}

# ─── DATA FETCHING ───────────────────────────────────────────────────────────

@st.cache_data(ttl=45, show_spinner=False)
def fetch_openf1(endpoint, params=""):
    try:
        r = requests.get(f"https://api.openf1.org/v1/{endpoint}?{params}", timeout=10)
        if r.status_code == 200:
            return r.json()
    except: pass
    return []

@st.cache_data(ttl=300, show_spinner=False)
def fetch_standings():
    """Scrape live standings from formula1.com"""
    drivers, constructors = [], []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get("https://www.formula1.com/en/results/2026/drivers", headers=headers, timeout=12)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, "html.parser")
            rows = soup.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 5:
                    try:
                        pos = cols[0].text.strip()
                        name_parts = cols[1].text.strip().split()
                        name = " ".join(name_parts[:2]) if len(name_parts) >= 2 else cols[1].text.strip()
                        nat = cols[2].text.strip() if len(cols) > 2 else ""
                        team = cols[3].text.strip() if len(cols) > 3 else ""
                        pts = cols[4].text.strip() if len(cols) > 4 else "0"
                        if pos.isdigit() and pts.replace(".","").isdigit():
                            drivers.append({"pos":int(pos),"name":name,"team":team,"pts":float(pts),"nat":nat})
                    except: pass
    except: pass

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get("https://www.formula1.com/en/results/2026/team", headers=headers, timeout=12)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, "html.parser")
            rows = soup.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 3:
                    try:
                        pos = cols[0].text.strip()
                        team = cols[1].text.strip()
                        pts = cols[2].text.strip()
                        if pos.isdigit() and pts.replace(".","").isdigit():
                            constructors.append({"pos":int(pos),"name":team,"pts":float(pts)})
                    except: pass
    except: pass

    return drivers, constructors

@st.cache_data(ttl=3600, show_spinner=False)
def load_race_results_ff1(year, round_num):
    """Load full race results via FastF1"""
    try:
        sess = fastf1.get_session(year, round_num, "R")
        sess.load(telemetry=False, weather=False, messages=False, laps=True)
        return sess
    except: return None

@st.cache_data(ttl=3600, show_spinner=False)
def load_quali_results_ff1(year, round_num):
    try:
        sess = fastf1.get_session(year, round_num, "Q")
        sess.load(telemetry=False, weather=False, messages=False, laps=True)
        return sess
    except: return None

@st.cache_data(ttl=3600, show_spinner=False)
def load_laps_ff1(year, round_num, session_type="R"):
    try:
        sess = fastf1.get_session(year, round_num, session_type)
        sess.load(telemetry=False, weather=True, messages=True, laps=True)
        return sess
    except: return None

def get_live_session():
    sessions = fetch_openf1("sessions", "year=2026")
    if not sessions: return None, False, False
    now = datetime.now(timezone.utc)
    past = [s for s in sessions if s.get("date_start") and
            datetime.fromisoformat(s["date_start"].replace("Z","+00:00")) < now]
    if not past: return None, False, False
    latest = past[-1]
    start = datetime.fromisoformat(latest["date_start"].replace("Z","+00:00"))
    end_str = latest.get("date_end")
    end = datetime.fromisoformat(end_str.replace("Z","+00:00")) + timedelta(hours=1) if end_str else start + timedelta(hours=4)
    live = start - timedelta(minutes=5) <= now <= end
    recent = (now - end) < timedelta(hours=30) if not live else False
    return latest, live, recent

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;600;700;900&family=Space+Mono:wght@400;700&display=swap');
*, html, body, [class*="css"] { font-family: 'Barlow Condensed', sans-serif !important; }
.stApp { background: #060606 !important; color: #f0f0f0 !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
/* HEADER */
.f1-hero { background: linear-gradient(180deg,#000 0%,#0a0a0a 100%); border-bottom: 3px solid #e10600; padding: 20px 28px 16px; margin-bottom: 0; }
.f1-badge { background: #e10600; color: #fff; font-size: 10px; font-weight: 700; letter-spacing: 4px; padding: 3px 9px; text-transform: uppercase; display: inline-block; margin-bottom: 6px; }
.f1-title { font-size: clamp(2rem,5vw,3.5rem); font-weight: 900; text-transform: uppercase; letter-spacing: -1px; line-height: 1; color: #f0f0f0; }
.f1-title b { color: #e10600; }
.f1-sub { font-family: 'Space Mono',monospace; font-size: 10px; color: #444; letter-spacing: 2px; margin-top: 4px; }
/* STATUS */
.status-bar { display:flex; align-items:center; gap:12px; padding:10px 28px; background:#0a0a0a; border-bottom:1px solid #1a1a1a; flex-wrap:wrap; }
.sdot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
.sdot.live { background:#00ff88; animation: pulse 1.4s infinite; }
.sdot.recent { background:#ffd700; }
.sdot.off { background:#333; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(.75)} }
.slabel { font-size:11px; font-weight:700; letter-spacing:2px; text-transform:uppercase; }
.sbadge { font-size:10px; font-weight:700; letter-spacing:2px; text-transform:uppercase; padding:3px 10px; border:1px solid; }
.sbadge.live { color:#00ff88; border-color:#00ff88; }
.sbadge.recent { color:#ffd700; border-color:#ffd700; }
.sbadge.off { color:#444; border-color:#2a2a2a; }
/* TABS */
.stTabs [data-baseweb="tab-list"] { background:#000 !important; border-bottom:2px solid #1a1a1a !important; padding:0 28px !important; gap:0 !important; }
.stTabs [data-baseweb="tab"] { background:transparent !important; color:#444 !important; font-family:'Barlow Condensed',sans-serif !important; font-size:12px !important; font-weight:700 !important; letter-spacing:2px !important; text-transform:uppercase !important; padding:12px 16px !important; border-bottom:3px solid transparent !important; transition:all .2s !important; }
.stTabs [aria-selected="true"] { color:#e10600 !important; border-bottom-color:#e10600 !important; }
.stTabs [data-baseweb="tab-panel"] { background:transparent !important; padding:22px 28px 60px !important; }
/* CARDS */
.metric-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:10px; margin-bottom:20px; }
.mc { background:#111; border:1px solid #1a1a1a; padding:14px 12px; text-align:center; transition:border-color .2s; }
.mc:hover { border-color:#e10600; }
.mc-val { font-size:1.9rem; font-weight:900; color:#e10600; line-height:1; font-family:'Space Mono',monospace; }
.mc-lab { font-size:9px; letter-spacing:2px; text-transform:uppercase; color:#444; margin-top:4px; }
/* SECTION TITLES */
.sec { font-size:.9rem; font-weight:900; letter-spacing:3px; text-transform:uppercase; color:#e10600; border-left:4px solid #e10600; padding-left:10px; margin:22px 0 14px; }
/* TIMING */
.tt-wrap { background:#0d0d0d; border:1px solid #1a1a1a; overflow:hidden; margin-bottom:18px; }
.tt-hdr { background:#000; padding:10px 14px; border-bottom:2px solid #e10600; display:flex; align-items:center; justify-content:space-between; }
.tt-title { font-size:11px; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:#e10600; }
.tt-cols { display:grid; grid-template-columns:36px 1fr 90px 80px 55px 50px 35px; padding:7px 14px; border-bottom:1px solid rgba(255,255,255,.04); }
.tt-ch { font-size:9px; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:#333; }
.tt-row { display:grid; grid-template-columns:36px 1fr 90px 80px 55px 50px 35px; padding:9px 14px; border-bottom:1px solid #111; align-items:center; transition:background .1s; }
.tt-row:hover { background:rgba(225,6,0,.04); }
.tt-row.p1 { background:rgba(225,6,0,.07); }
.pos { font-family:'Space Mono',monospace; font-size:12px; font-weight:700; color:#444; }
.pos.first { color:#e10600; }
.drv-name { font-size:14px; font-weight:900; }
.drv-team { font-size:10px; color:#444; margin-top:1px; }
.gap { font-family:'Space Mono',monospace; font-size:12px; color:#555; }
.gap.leader { color:#e10600; font-weight:700; }
.intv { font-family:'Space Mono',monospace; font-size:11px; color:#444; }
.tyre { display:inline-flex; align-items:center; justify-content:center; width:22px; height:22px; border-radius:50%; font-size:10px; font-weight:900; color:#000; }
.pit-cnt { font-family:'Space Mono',monospace; font-size:11px; color:#444; text-align:center; }
/* STANDINGS */
.std-row { display:grid; grid-template-columns:32px 1fr 65px 38px; padding:9px 12px; border-bottom:1px solid #111; align-items:center; transition:background .1s; }
.std-row:hover { background:rgba(225,6,0,.04); }
.std-pos { font-family:'Space Mono',monospace; font-size:11px; color:#444; }
.std-name { font-size:14px; font-weight:700; }
.std-team-name { font-size:10px; color:#444; }
.std-pts { font-family:'Space Mono',monospace; font-weight:700; font-size:13px; color:#e10600; text-align:right; }
.std-wins { font-family:'Space Mono',monospace; font-size:11px; color:#444; text-align:right; }
.pts-bar { height:3px; background:#1a1a1a; margin-top:4px; overflow:hidden; }
.pts-fill { height:100%; transition:width .8s ease; }
/* RESULTS */
.res-row { display:grid; grid-template-columns:36px 1fr 100px 80px 55px 55px; padding:9px 12px; border-bottom:1px solid #111; align-items:center; font-size:13px; }
.res-row:hover { background:rgba(225,6,0,.04); }
.res-row.podium { background:rgba(225,6,0,.05); }
.res-pos { font-family:'Space Mono',monospace; font-size:12px; }
.res-name { font-size:14px; font-weight:700; }
.res-team { font-size:10px; color:#444; }
.res-time { font-family:'Space Mono',monospace; font-size:11px; color:#666; }
.res-pts { font-family:'Space Mono',monospace; font-weight:700; font-size:12px; color:#e10600; text-align:right; }
.fl-badge { color:#c000ff; font-size:10px; margin-left:5px; }
.dnf-badge { color:#e10600; font-size:10px; font-weight:700; }
/* CALENDAR */
.cal-row { display:grid; grid-template-columns:36px 1fr 80px 70px; padding:10px 12px; border-bottom:1px solid #111; align-items:center; font-size:13px; transition:background .1s; }
.cal-row:hover { background:rgba(225,6,0,.04); }
.cal-row.next { background:rgba(225,6,0,.07); border-left:3px solid #e10600; }
.cal-row.done { opacity:.7; }
.cal-row.cancelled { opacity:.4; }
.cal-rnd { font-family:'Space Mono',monospace; font-size:11px; color:#444; }
.cal-name { font-size:14px; font-weight:700; }
.cal-circuit { font-size:10px; color:#444; }
.cal-date { font-family:'Space Mono',monospace; font-size:11px; color:#555; }
.cal-status-done { color:#00c853; font-size:11px; font-weight:700; }
.cal-status-next { color:#e10600; font-size:11px; font-weight:700; }
.cal-status-future { color:#444; font-size:11px; }
.cal-status-cancelled { color:#333; font-size:11px; }
/* EXPANDED RACE */
.race-detail { background:#0d0d0d; border:1px solid #1a1a1a; padding:16px 18px; margin:0 0 4px; }
.rd-winner { font-size:1.6rem; font-weight:900; text-transform:uppercase; letter-spacing:-1px; }
.rd-stat { display:inline-block; background:#111; border:1px solid #1a1a1a; padding:5px 12px; margin:4px 4px 0 0; font-size:11px; font-family:'Space Mono',monospace; }
.rd-stat b { color:#e10600; }
.podium-row { display:flex; gap:10px; margin:12px 0; flex-wrap:wrap; }
.podium-item { background:#111; border:1px solid #1a1a1a; padding:10px 14px; text-align:center; min-width:90px; }
.podium-medal { font-size:1.4rem; }
.podium-name { font-size:13px; font-weight:700; margin-top:4px; }
.podium-team { font-size:10px; color:#444; }
/* WEATHER */
.wx-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(105px,1fr)); gap:9px; margin-bottom:18px; }
.wx-card { background:#111; border:1px solid #1a1a1a; padding:12px 10px; text-align:center; }
.wx-val { font-size:1.4rem; font-weight:900; color:#e10600; line-height:1; }
.wx-lab { font-size:9px; letter-spacing:2px; text-transform:uppercase; color:#444; margin-top:3px; }
/* RACE CONTROL */
.rc-feed { background:#0d0d0d; border:1px solid #1a1a1a; max-height:420px; overflow-y:auto; }
.rc-row { display:flex; gap:10px; align-items:flex-start; padding:9px 13px; border-bottom:1px solid #111; }
.rc-time { font-family:'Space Mono',monospace; font-size:10px; color:#444; min-width:58px; margin-top:2px; }
.rc-badge { font-size:9px; font-weight:700; letter-spacing:1px; padding:2px 7px; display:inline-block; margin-right:5px; }
.rc-sc  { background:rgba(255,215,0,.1); color:#ffd700; border:1px solid rgba(255,215,0,.2); }
.rc-red { background:rgba(225,6,0,.1);   color:#e10600; border:1px solid rgba(225,6,0,.2); }
.rc-drs { background:rgba(0,200,80,.08); color:#00c850; border:1px solid rgba(0,200,80,.15); }
.rc-pen { background:rgba(255,165,0,.1); color:#ffa500; border:1px solid rgba(255,165,0,.2); }
.rc-inf { background:rgba(255,255,255,.04); color:#555; border:1px solid #1a1a1a; }
.rc-msg { font-size:13px; color:#bbb; line-height:1.5; }
/* TYRE CHART */
.tyre-strat { display:flex; align-items:center; gap:8px; margin:5px 0; }
.tyre-drv { font-size:12px; font-weight:700; min-width:35px; font-family:'Space Mono',monospace; }
.tyre-bar { display:flex; height:18px; flex:1; overflow:hidden; gap:1px; }
.tyre-seg { display:flex; align-items:center; justify-content:center; font-size:9px; font-weight:900; color:#000; }
/* NEXT RACE HERO */
.next-hero { background:linear-gradient(135deg,#0a0a0a,#111); border:1px solid #1a1a1a; border-left:4px solid #e10600; padding:24px; margin-bottom:20px; }
.next-round { font-size:10px; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:#e10600; margin-bottom:6px; }
.next-name { font-size:clamp(1.8rem,4vw,3rem); font-weight:900; text-transform:uppercase; letter-spacing:-1px; line-height:1; }
.next-circuit { font-size:13px; color:#555; margin-top:5px; font-family:'Space Mono',monospace; }
.next-countdown { font-size:2.5rem; font-weight:900; color:#e10600; margin-top:12px; line-height:1; }
.next-date { font-size:12px; color:#444; font-family:'Space Mono',monospace; margin-top:4px; }
/* EMPTY */
.empty { padding:32px 16px; text-align:center; color:#333; font-size:13px; font-family:'Space Mono',monospace; }
/* QUALI */
.q-row { display:grid; grid-template-columns:32px 1fr 90px 90px 90px; padding:8px 12px; border-bottom:1px solid #111; font-size:13px; }
.q-row:hover { background:rgba(225,6,0,.04); }
.q-time { font-family:'Space Mono',monospace; font-size:12px; }
/* SOURCE NOTE */
.source-note { font-family:'Space Mono',monospace; font-size:9px; color:#333; padding:6px 12px; background:#0a0a0a; border-bottom:1px solid #111; }
/* SCROLLBAR */
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:#060606; }
::-webkit-scrollbar-thumb { background:#1a1a1a; }
::-webkit-scrollbar-thumb:hover { background:#e10600; }
@media(max-width:640px) {
  .tt-cols,.tt-row { grid-template-columns:32px 1fr 70px 60px 40px 40px 30px; }
  .res-row { grid-template-columns:32px 1fr 80px 55px; }
  .std-row { grid-template-columns:28px 1fr 60px 35px; }
}
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ────────────────────────────────────────────────────────────
if "expanded_round" not in st.session_state:
    st.session_state.expanded_round = None

# ─── GET CURRENT SESSION ─────────────────────────────────────────────────────
latest_sess, is_live, is_recent = get_live_session()
sess_key = latest_sess.get("session_key") if latest_sess else None

# ─── HEADER ──────────────────────────────────────────────────────────────────
now = datetime.now()
next_race = next((r for r in CALENDAR if r["status"] == "upcoming"), None)
completed = [r for r in CALENDAR if r["status"] == "done"]

st.markdown(f"""
<div class="f1-hero">
  <div class="f1-badge">Formula 1 · 2026 Season</div>
  <div class="f1-title">Live <b>Season</b> Hub</div>
  <div class="f1-sub">Real-Time Data · FastF1 + OpenF1 + F1 Official · Updated {now.strftime('%H:%M:%S')}</div>
</div>
""", unsafe_allow_html=True)

# Status bar
if is_live:
    dot_cls, badge_cls = "live", "live"
    status_txt = f"🟢 LIVE — {latest_sess.get('session_name','')} · {latest_sess.get('location','')}, {latest_sess.get('country_name','')}"
    badge_txt = "LIVE SESSION"
elif is_recent and latest_sess:
    dot_cls, badge_cls = "recent", "recent"
    status_txt = f"Last: {latest_sess.get('session_name','')} · {latest_sess.get('location','')}, {latest_sess.get('country_name','')}"
    badge_txt = "RECENT"
else:
    dot_cls, badge_cls = "off", "off"
    days = (datetime.strptime(next_race["race_date"], "%Y-%m-%d") - now).days if next_race else 0
    status_txt = f"Off Weekend · Next: {next_race['name']} in {days} day{'s' if days!=1 else ''}" if next_race else "Off Weekend"
    badge_txt = "OFF WEEKEND"

st.markdown(f"""
<div class="status-bar">
  <div class="sdot {dot_cls}"></div>
  <span class="slabel">{status_txt}</span>
  <span class="sbadge {badge_cls}">{badge_txt}</span>
</div>
""", unsafe_allow_html=True)

# ─── TABS ─────────────────────────────────────────────────────────────────────
tabs = st.tabs(["🏁 Live Timing", "📊 Standings", "📅 Season", "🏆 Race Results", "📈 Lap Analysis", "🌤 Track & Control"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — LIVE TIMING
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    col_ref, col_info = st.columns([1,4])
    with col_ref:
        if st.button("⟳ Refresh", key="ref1"):
            st.cache_data.clear()
            st.rerun()

    if is_live or is_recent:
        if sess_key:
            with st.spinner("Loading live timing…"):
                intervals = fetch_openf1("intervals", f"session_key={sess_key}")
                drivers_raw = fetch_openf1("drivers", f"session_key={sess_key}")
                stints_raw = fetch_openf1("stints", f"session_key={sess_key}")
                pits_raw = fetch_openf1("pit", f"session_key={sess_key}")

            drv_map = {d["driver_number"]: d for d in drivers_raw}
            int_map = {}
            for i in intervals:
                n = i["driver_number"]
                if n not in int_map or i["date"] > int_map[n]["date"]:
                    int_map[n] = i
            stint_map = {}
            for s in stints_raw:
                n = s["driver_number"]
                if n not in stint_map or s.get("lap_start",0) > stint_map[n].get("lap_start",0):
                    stint_map[n] = s
            pit_map = {}
            for p in pits_raw:
                pit_map[p["driver_number"]] = pit_map.get(p["driver_number"],0) + 1

            rows = sorted(int_map.values(), key=lambda x: (
                0 if (x.get("gap_to_leader") in [None, 0, "0"]) else
                float(str(x.get("gap_to_leader","9999")).replace("+","") or 9999)
            ))

            if rows:
                sname = f"{latest_sess.get('session_name','')} · {latest_sess.get('location','')}, {latest_sess.get('country_name','')}"
                st.markdown(f"""
                <div class="tt-wrap">
                  <div class="tt-hdr">
                    <span class="tt-title">{sname}</span>
                    <span style="font-family:'Space Mono',monospace;font-size:10px;color:#444">{len(rows)} cars · {'🔴 LIVE' if is_live else '🟡 Post-session'}</span>
                  </div>
                  <div class="tt-cols">
                    <div class="tt-ch">POS</div><div class="tt-ch">DRIVER</div>
                    <div class="tt-ch">GAP</div><div class="tt-ch">INTERVAL</div>
                    <div class="tt-ch">TYRE</div><div class="tt-ch">LAPS</div><div class="tt-ch">PIT</div>
                  </div>
                """, unsafe_allow_html=True)

                for idx, row in enumerate(rows):
                    n = row["driver_number"]
                    drv = drv_map.get(n, {})
                    name = drv.get("name_acronym", f"#{n}")
                    team = drv.get("team_name", "")
                    col = tc(team)
                    stint = stint_map.get(n, {})
                    compound = (stint.get("compound") or "UNKNOWN").upper()
                    tyre_col = TYRE_COLORS.get(compound, "#555")
                    tyre_ltr = TYRE_ABBR.get(compound, "?")
                    tyre_laps = "?"
                    if stint.get("tyre_age_at_start") is not None and stint.get("lap_end") is not None:
                        tyre_laps = stint["lap_end"] - stint.get("lap_start",0) + stint["tyre_age_at_start"]
                    pits = pit_map.get(n, 0)
                    gap = "LEADER" if idx == 0 else (f"+{row['gap_to_leader']}" if row.get("gap_to_leader") else "—")
                    intv = "—" if idx == 0 else (f"+{row['interval']}" if row.get("interval") else "—")
                    txt_col = "#000" if compound != "UNKNOWN" else "#fff"
                    pos_cls = "first" if idx == 0 else ""
                    row_cls = "p1" if idx == 0 else ""

                    st.markdown(f"""
                    <div class="tt-row {row_cls}">
                      <div class="pos {pos_cls}">{idx+1}</div>
                      <div>
                        <div class="drv-name" style="color:{col}">{name}</div>
                        <div class="drv-team">{team}</div>
                      </div>
                      <div class="gap {'leader' if idx==0 else ''}">{gap}</div>
                      <div class="intv">{intv}</div>
                      <div><span class="tyre" style="background:{tyre_col};color:{txt_col}">{tyre_ltr}</span></div>
                      <div style="font-family:'Space Mono',monospace;font-size:11px;color:#555">{tyre_laps}</div>
                      <div class="pit-cnt">{pits or '—'}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty">No timing data yet for this session</div>', unsafe_allow_html=True)
    else:
        # Off weekend — show next race hero + recent results
        if next_race:
            rd = datetime.strptime(next_race["race_date"], "%Y-%m-%d")
            days = (rd - now).days
            facts = CIRCUIT_FACTS.get(next_race["name"], {})
            st.markdown(f"""
            <div class="next-hero">
              <div class="next-round">Round {next_race['round']} · Next Race</div>
              <div class="next-name">{next_race['name']}</div>
              <div class="next-circuit">{next_race['circuit']} · {next_race['country']}</div>
              <div class="next-countdown">{days} day{'s' if days!=1 else ''} away</div>
              <div class="next-date">{rd.strftime('%d %B %Y')}</div>
              {f'<div style="font-size:12px;color:#555;margin-top:12px;font-style:italic">💡 {facts["fact"]}</div>' if facts.get("fact") else ''}
              {f'<div style="margin-top:10px"><span class="rd-stat">🔄 {facts["laps"]} laps</span><span class="rd-stat">📏 {facts["length"]}</span><span class="rd-stat">⏱ Record: {facts["lap_record"]}</span></div>' if facts else ''}
            </div>
            """, unsafe_allow_html=True)

        # Last completed race quick view
        if completed:
            last = completed[-1]
            col1, col2 = st.columns([3,2])
            with col1:
                st.markdown(f'<div class="sec">Last Race — {last["name"]}</div>', unsafe_allow_html=True)
                winner_col = tc(last.get("team",""))
                st.markdown(f"""
                <div style="background:#0d0d0d;border:1px solid #1a1a1a;padding:18px">
                  <div style="font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#444;margin-bottom:6px">Race Winner · Round {last['round']}</div>
                  <div style="font-size:2rem;font-weight:900;color:{winner_col}">{last.get('winner','TBC')}</div>
                  <div style="font-size:13px;color:#444;margin-top:4px">{last.get('team','')} · {last['circuit']}</div>
                </div>
                """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — STANDINGS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown('<div class="sec">2026 Championship Standings</div>', unsafe_allow_html=True)

    with st.spinner("Loading standings from formula1.com…"):
        drv_std, con_std = fetch_standings()

    source = "formula1.com (official)" if drv_std else "estimated fallback"
    st.markdown(f'<div class="source-note">📡 Source: {source}</div>', unsafe_allow_html=True)

    # Fallback data
    if not drv_std:
        drv_std = [
            {"pos":1,"name":"Kimi Antonelli","team":"Mercedes","pts":156,"nat":"🇮🇹"},
            {"pos":2,"name":"George Russell","team":"Mercedes","pts":101,"nat":"🇬🇧"},
            {"pos":3,"name":"Charles Leclerc","team":"Ferrari","pts":88,"nat":"🇲🇨"},
            {"pos":4,"name":"Lewis Hamilton","team":"Ferrari","pts":84,"nat":"🇬🇧"},
            {"pos":5,"name":"Lando Norris","team":"McLaren","pts":71,"nat":"🇬🇧"},
            {"pos":6,"name":"Oscar Piastri","team":"McLaren","pts":58,"nat":"🇦🇺"},
            {"pos":7,"name":"Max Verstappen","team":"Red Bull Racing","pts":43,"nat":"🇳🇱"},
            {"pos":8,"name":"Franco Colapinto","team":"Alpine","pts":32,"nat":"🇦🇷"},
            {"pos":9,"name":"Oliver Bearman","team":"Haas F1 Team","pts":25,"nat":"🇬🇧"},
            {"pos":10,"name":"Liam Lawson","team":"Racing Bulls","pts":20,"nat":"🇳🇿"},
            {"pos":11,"name":"Isack Hadjar","team":"Red Bull Racing","pts":18,"nat":"🇫🇷"},
            {"pos":12,"name":"Pierre Gasly","team":"Alpine","pts":14,"nat":"🇫🇷"},
            {"pos":13,"name":"Carlos Sainz","team":"Williams","pts":9,"nat":"🇪🇸"},
            {"pos":14,"name":"Arvid Lindblad","team":"Racing Bulls","pts":8,"nat":"🇸🇪"},
            {"pos":15,"name":"Fernando Alonso","team":"Aston Martin","pts":7,"nat":"🇪🇸"},
            {"pos":16,"name":"Lance Stroll","team":"Aston Martin","pts":5,"nat":"🇨🇦"},
            {"pos":17,"name":"Gabriel Bortoleto","team":"Audi","pts":4,"nat":"🇧🇷"},
            {"pos":18,"name":"Esteban Ocon","team":"Haas F1 Team","pts":2,"nat":"🇫🇷"},
            {"pos":19,"name":"Alexander Albon","team":"Williams","pts":1,"nat":"🇹🇭"},
            {"pos":20,"name":"Nico Hulkenberg","team":"Audi","pts":0,"nat":"🇩🇪"},
        ]
    if not con_std:
        con_std = [
            {"pos":1,"name":"Mercedes","pts":257},{"pos":2,"name":"Ferrari","pts":172},
            {"pos":3,"name":"McLaren","pts":129},{"pos":4,"name":"Red Bull Racing","pts":61},
            {"pos":5,"name":"Alpine","pts":46},{"pos":6,"name":"Racing Bulls","pts":28},
            {"pos":7,"name":"Haas F1 Team","pts":27},{"pos":8,"name":"Williams","pts":10},
            {"pos":9,"name":"Aston Martin","pts":12},{"pos":10,"name":"Audi","pts":4},
            {"pos":11,"name":"Cadillac","pts":0},
        ]

    col_d, col_c = st.columns(2)

    with col_d:
        st.markdown('<div class="sec">Drivers</div>', unsafe_allow_html=True)
        max_pts = drv_std[0]["pts"] if drv_std else 1
        st.markdown('<div class="tt-wrap">', unsafe_allow_html=True)
        for d in drv_std:
            col = tc(d.get("team",""))
            pct = round(d["pts"]/max_pts*100)
            nat = d.get("nat","")
            st.markdown(f"""
            <div class="std-row">
              <div class="std-pos">{d['pos']}</div>
              <div>
                <div class="std-name" style="color:{col}">{nat} {d['name']}</div>
                <div class="std-team-name">{d.get('team','')}</div>
                <div class="pts-bar"><div class="pts-fill" style="width:{pct}%;background:{col}"></div></div>
              </div>
              <div class="std-pts">{int(d['pts'])}</div>
              <div></div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_c:
        st.markdown('<div class="sec">Constructors</div>', unsafe_allow_html=True)
        max_c = con_std[0]["pts"] if con_std else 1
        st.markdown('<div class="tt-wrap">', unsafe_allow_html=True)
        for c in con_std:
            col = tc(c.get("name",""))
            pct = round(c["pts"]/max_c*100)
            st.markdown(f"""
            <div class="std-row">
              <div class="std-pos">{c['pos']}</div>
              <div>
                <div class="std-name" style="color:{col}">{c['name']}</div>
                <div class="pts-bar"><div class="pts-fill" style="width:{pct}%;background:{col}"></div></div>
              </div>
              <div class="std-pts">{int(c['pts'])}</div>
              <div></div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Points gap chart
    st.markdown('<div class="sec">Points Gap</div>', unsafe_allow_html=True)
    top10 = drv_std[:10]
    names = [d["name"].split()[-1] for d in top10]
    pts_v = [d["pts"] for d in top10]
    colors_v = [tc(d.get("team","")) for d in top10]
    fig = go.Figure(go.Bar(x=names, y=pts_v, marker_color=colors_v, marker_line_width=0,
                           text=pts_v, textposition="outside",
                           textfont=dict(color="#f0f0f0", size=11, family="Space Mono")))
    st.markdown("📊 Chart unavailable on Python 3.14 — upgrade coming soon", unsafe_allow_html=True)
                      font=dict(family="Barlow Condensed", color="#f0f0f0"),
                      xaxis=dict(tickfont=dict(size=12,color="#666"), gridcolor="transparent"),
                      yaxis=dict(tickfont=dict(size=11,color="#444"), gridcolor="#111"),
                      margin=dict(l=10,r=10,t=10,b=10), height=260, showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SEASON CALENDAR
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown('<div class="sec">2026 Season Calendar · 24 Rounds</div>', unsafe_allow_html=True)

    done_count = len([r for r in CALENDAR if r["status"]=="done"])
    cancelled_count = len([r for r in CALENDAR if r["status"]=="cancelled"])
    remaining = len([r for r in CALENDAR if r["status"]=="upcoming"])

    st.markdown(f"""
    <div class="metric-row">
      <div class="mc"><div class="mc-val">{done_count}</div><div class="mc-lab">Races Done</div></div>
      <div class="mc"><div class="mc-val">{cancelled_count}</div><div class="mc-lab">Cancelled</div></div>
      <div class="mc"><div class="mc-val">{remaining}</div><div class="mc-lab">Remaining</div></div>
      <div class="mc"><div class="mc-val">{24-cancelled_count}</div><div class="mc-lab">Total Active</div></div>
    </div>
    """, unsafe_allow_html=True)

    next_round = next((r["round"] for r in CALENDAR if r["status"]=="upcoming"), 99)

    for race in CALENDAR:
        rd = datetime.strptime(race["race_date"], "%Y-%m-%d")
        days = (rd - now).days
        is_next = race["round"] == next_round
        row_cls = "next" if is_next else race["status"]

        if race["status"] == "done":
            status_html = f'<span class="cal-status-done">✓ DONE</span>'
        elif race["status"] == "cancelled":
            status_html = f'<span class="cal-status-cancelled">✕ CANCELLED</span>'
        elif is_next:
            status_html = f'<span class="cal-status-next">NEXT · {days}d</span>'
        else:
            status_html = f'<span class="cal-status-future">in {days}d</span>'

        winner_info = f'<div style="font-size:11px;color:{tc(race.get("team",""))};margin-top:2px">🏆 {race["winner"]}</div>' if race.get("winner") else ""

        st.markdown(f"""
        <div class="cal-row {row_cls}">
          <div class="cal-rnd">R{race['round']}</div>
          <div>
            <div class="cal-name">{race['name']}</div>
            <div class="cal-circuit">{race['circuit']} · {race['country']}</div>
            {winner_info}
          </div>
          <div class="cal-date">{rd.strftime('%d %b')}</div>
          <div>{status_html}</div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — RACE RESULTS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown('<div class="sec">Race Results — Full Classification</div>', unsafe_allow_html=True)

    done_races = [r for r in CALENDAR if r["status"] == "done"]
    if not done_races:
        st.markdown('<div class="empty">No completed races yet</div>', unsafe_allow_html=True)
    else:
        race_options = {f"R{r['round']}: {r['name']} ({datetime.strptime(r['race_date'],'%Y-%m-%d').strftime('%d %b')})": r["round"] for r in done_races}
        sel_race_name = st.selectbox("Select Race", list(race_options.keys()), key="race_sel")
        sel_round = race_options[sel_race_name]
        sel_race_info = next(r for r in CALENDAR if r["round"] == sel_round)

        col_r, col_q = st.columns([3,2])

        with col_r:
            st.markdown(f'<div class="sec">Race Results · {sel_race_info["name"]}</div>', unsafe_allow_html=True)
            with st.spinner("Loading via FastF1…"):
                ff1_race = load_race_results_ff1(2026, sel_round)

            if ff1_race and ff1_race.results is not None and len(ff1_race.results) > 0:
                results_df = ff1_race.results
                st.markdown(f'<div class="source-note">📡 Source: FastF1 official timing data</div>', unsafe_allow_html=True)
                st.markdown("""
                <div class="tt-wrap">
                  <div style="display:grid;grid-template-columns:36px 1fr 100px 80px 55px 55px;padding:7px 12px;border-bottom:2px solid #e10600;font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#333;background:#000">
                    <div>POS</div><div>DRIVER</div><div>TIME/STATUS</div><div>TEAM</div><div>PTS</div><div>TYRE</div>
                  </div>
                """, unsafe_allow_html=True)

                for _, row in results_df.iterrows():
                    pos = str(row.get("Position","?"))
                    status = str(row.get("Status",""))
                    is_dnf = status not in ["Finished","+1 Lap","+2 Laps","+3 Laps",""] and not status.startswith("+")
                    medal = "🥇" if pos=="1" else "🥈" if pos=="2" else "🥉" if pos=="3" else pos
                    name = f"{row.get('FirstName','')[:1]}. {row.get('LastName','?')}"
                    full_name = f"{row.get('FirstName','')} {row.get('LastName','')}"
                    team = row.get("TeamName","")
                    col = tc(team)
                    time_val = str(row.get("Time","")) if not is_dnf else f"DNF · {status}"
                    pts = int(row.get("Points",0))
                    fl = row.get("FastestLap") == True
                    abbr = DRIVER_ABBR.get(full_name.strip(), full_name[:3].upper())
                    podium_cls = "podium" if pos in ["1","2","3"] else ""

                    st.markdown(f"""
                    <div class="res-row {podium_cls}">
                      <div class="res-pos" style="font-size:{'1.1rem' if pos in ['1','2','3'] else '12px'};font-family:'Space Mono',monospace">{medal}</div>
                      <div>
                        <div class="res-name" style="color:{col}">{abbr} {'<span class="fl-badge">⬡FL</span>' if fl else ''}</div>
                        <div class="res-team">{team}</div>
                      </div>
                      <div class="res-time {'dnf-badge' if is_dnf else ''}">{time_val[:20]}</div>
                      <div style="font-size:11px;color:#444">{team[:12]}</div>
                      <div class="res-pts">+{pts}</div>
                      <div></div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

                # DNF summary
                dnfs = results_df[~results_df["Status"].isin(["Finished","+1 Lap","+2 Laps","+3 Laps",""])]
                dnfs = dnfs[~dnfs["Status"].str.startswith("+")]
                if len(dnfs) > 0:
                    st.markdown('<div class="sec">DNF / Retirements</div>', unsafe_allow_html=True)
                    for _, row in dnfs.iterrows():
                        name = f"{row.get('FirstName','')[:1]}. {row.get('LastName','?')}"
                        status = row.get("Status","")
                        col = tc(row.get("TeamName",""))
                        st.markdown(f'<div style="padding:7px 12px;border-bottom:1px solid #111;font-size:13px"><span style="color:{col};font-weight:700">{name}</span> <span style="color:#555;font-family:\'Space Mono\',monospace;font-size:11px">{status}</span></div>', unsafe_allow_html=True)

            else:
                # Hardcoded fallback for completed races
                st.markdown(f'<div class="source-note">📡 FastF1 data loading · Showing known results</div>', unsafe_allow_html=True)
                hardcoded = {
                    1: [("1","George Russell","Mercedes","1:23:45.XXX",25,False),("2","Kimi Antonelli","Mercedes","+12.XXX",18,False),("3","Charles Leclerc","Ferrari","+18.XXX",15,True)],
                    2: [("1","Kimi Antonelli","Mercedes","1:XX:XX.XXX",25,True),("2","George Russell","Mercedes","+X.XXX",18,False),("3","Charles Leclerc","Ferrari","+XX.XXX",15,False)],
                    3: [("1","Kimi Antonelli","Mercedes","1:XX:XX.XXX",25,False),("2","George Russell","Mercedes","+X.XXX",18,True),("3","Lewis Hamilton","Ferrari","+XX.XXX",15,False)],
                    6: [("1","Kimi Antonelli","Mercedes","1:XX:XX.XXX",25,False),("2","Lando Norris","McLaren","+X.XXX",18,True),("3","Charles Leclerc","Ferrari","+XX.XXX",15,False)],
                    7: [("1","Kimi Antonelli","Mercedes","1:XX:XX.XXX",25,False),("2","Lewis Hamilton","Ferrari","+X.XXX",18,False),("3","George Russell","Mercedes","+XX.XXX",15,True)],
                }
                results = hardcoded.get(sel_round, [])
                if results:
                    st.markdown('<div class="tt-wrap">', unsafe_allow_html=True)
                    for pos, name, team, time_v, pts, fl in results:
                        medal = "🥇" if pos=="1" else "🥈" if pos=="2" else "🥉"
                        col = tc(team)
                        fl_badge = '<span class="fl-badge">⬡FL</span>' if fl else ""
                        st.markdown(f"""
                        <div class="res-row podium">
                          <div style="font-size:1.1rem">{medal}</div>
                          <div><div class="res-name" style="color:{col}">{name}{fl_badge}</div><div class="res-team">{team}</div></div>
                          <div class="res-time">{time_v}</div>
                          <div></div>
                          <div class="res-pts">+{pts}</div>
                          <div></div>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="empty">Full results available via FastF1 1-2 days post-race</div>', unsafe_allow_html=True)

        with col_q:
            st.markdown(f'<div class="sec">Qualifying · {sel_race_info["name"]}</div>', unsafe_allow_html=True)
            with st.spinner("Loading qualifying…"):
                ff1_quali = load_quali_results_ff1(2026, sel_round)

            if ff1_quali and ff1_quali.results is not None and len(ff1_quali.results) > 0:
                q_df = ff1_quali.results
                st.markdown("""
                <div class="tt-wrap">
                  <div style="display:grid;grid-template-columns:32px 1fr 90px 90px 90px;padding:7px 12px;border-bottom:2px solid #e10600;font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#333;background:#000">
                    <div>P</div><div>DRIVER</div><div>Q1</div><div>Q2</div><div>Q3</div>
                  </div>
                """, unsafe_allow_html=True)
                for _, row in q_df.iterrows():
                    pos = str(row.get("Position","?"))
                    name = f"{row.get('FirstName','')[:1]}. {row.get('LastName','?')}"
                    team = row.get("TeamName","")
                    col = tc(team)
                    def fmt_time(t):
                        if pd.isna(t) or t is None: return "—"
                        secs = t.total_seconds()
                        m = int(secs//60); s = secs%60
                        return f"{m}:{s:06.3f}"
                    q1 = fmt_time(row.get("Q1"))
                    q2 = fmt_time(row.get("Q2"))
                    q3 = fmt_time(row.get("Q3"))
                    st.markdown(f"""
                    <div class="q-row">
                      <div class="std-pos">{pos}</div>
                      <div><div style="font-size:13px;font-weight:700;color:{col}">{name}</div><div style="font-size:10px;color:#444">{team}</div></div>
                      <div class="q-time">{q1}</div>
                      <div class="q-time">{q2}</div>
                      <div class="q-time" style="color:#e10600">{q3}</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty">Qualifying data loads via FastF1 after the weekend</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — LAP ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown('<div class="sec">Lap Time Analysis — FastF1</div>', unsafe_allow_html=True)

    done_races = [r for r in CALENDAR if r["status"] == "done"]
    if not done_races:
        st.markdown('<div class="empty">No completed races yet</div>', unsafe_allow_html=True)
    else:
        lap_options = {f"R{r['round']}: {r['name']}": r["round"] for r in done_races}
        col_s1, col_s2 = st.columns([2,1])
        with col_s1:
            sel_lap_race = st.selectbox("Race", list(lap_options.keys()), key="lap_race")
        with col_s2:
            sel_sess_type = st.selectbox("Session", ["R","Q","FP1","FP2","FP3"], key="lap_sess",
                                          format_func=lambda x: {"R":"Race","Q":"Qualifying","FP1":"FP1","FP2":"FP2","FP3":"FP3"}[x])

        sel_lap_round = lap_options[sel_lap_race]

        with st.spinner("Loading lap data via FastF1…"):
            ff1_laps = load_laps_ff1(2026, sel_lap_round, sel_sess_type)

        if ff1_laps and ff1_laps.laps is not None and len(ff1_laps.laps) > 0:
            laps_df = ff1_laps.laps.copy()
            laps_df = laps_df.dropna(subset=["LapTime"])
            laps_df["LapTimeSec"] = laps_df["LapTime"].dt.total_seconds()
            laps_df = laps_df[laps_df["LapTimeSec"] > 0]

            all_drivers = sorted(laps_df["Driver"].unique())
            sel_drvs = st.multiselect("Compare Drivers", all_drivers,
                                       default=all_drivers[:6] if len(all_drivers)>=6 else all_drivers,
                                       key="lap_drvs")

            if sel_drvs:
                # Lap time chart
                st.markdown('<div class="sec">Lap Times</div>', unsafe_allow_html=True)
                fig = go.Figure()
                for d in sel_drvs:
                    d_laps = laps_df[laps_df["Driver"]==d].sort_values("LapNumber")
                    drv_full = ff1_laps.results[ff1_laps.results["Abbreviation"]==d]["FullName"].values
                    team_name = ff1_laps.results[ff1_laps.results["Abbreviation"]==d]["TeamName"].values
                    col = tc(team_name[0] if len(team_name)>0 else "")
                    fig.add_trace(go.Scatter(
                        x=d_laps["LapNumber"], y=d_laps["LapTimeSec"],
                        mode="lines+markers", name=d,
                        line=dict(color=col, width=2),
                        marker=dict(size=3, color=col),
                        hovertemplate=f"<b>{d}</b><br>Lap %{{x}}<br>%{{y:.3f}}s<extra></extra>"
                    ))
                fig.update_layout(
                    paper_bgcolor="#0d0d0d", plot_bgcolor="#0d0d0d",
                    font=dict(family="Barlow Condensed", color="#f0f0f0"),
                    xaxis=dict(title="Lap Number", gridcolor="#111", tickfont=dict(color="#555")),
                    yaxis=dict(title="Lap Time (s)", gridcolor="#111", tickfont=dict(color="#555")),
                    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=12)),
                    margin=dict(l=20,r=20,t=20,b=20), height=360,
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

                # Tyre strategy
                if "Compound" in laps_df.columns:
                    st.markdown('<div class="sec">Tyre Strategy</div>', unsafe_allow_html=True)
                    max_lap = int(laps_df["LapNumber"].max())

                    st.markdown('<div style="background:#0d0d0d;border:1px solid #1a1a1a;padding:16px">', unsafe_allow_html=True)
                    for d in sel_drvs:
                        d_laps = laps_df[laps_df["Driver"]==d].sort_values("LapNumber")
                        stints_grp = d_laps.groupby((d_laps["Compound"] != d_laps["Compound"].shift()).cumsum())
                        stint_data = []
                        for _, stint in stints_grp:
                            compound = stint["Compound"].iloc[0] if not stint["Compound"].empty else "UNKNOWN"
                            laps = len(stint)
                            stint_data.append((compound.upper(), laps))

                        segments_html = ""
                        for compound, laps in stint_data:
                            tyre_col = TYRE_COLORS.get(compound, "#555")
                            pct = round(laps/max_lap*100)
                            abbr = TYRE_ABBR.get(compound, "?")
                            txt_col = "#000" if compound not in ["UNKNOWN"] else "#fff"
                            segments_html += f'<div class="tyre-seg" style="width:{pct}%;background:{tyre_col};color:{txt_col}" title="{compound} · {laps} laps">{abbr}·{laps}</div>'

                        st.markdown(f"""
                        <div class="tyre-strat">
                          <div class="tyre-drv" style="color:#e10600">{d}</div>
                          <div class="tyre-bar">{segments_html}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                # Fastest laps
                st.markdown('<div class="sec">Fastest Laps</div>', unsafe_allow_html=True)
                fl_df = laps_df.groupby("Driver")["LapTimeSec"].min().reset_index()
                fl_df = fl_df.sort_values("LapTimeSec").reset_index(drop=True)
                fl_df["Gap"] = fl_df["LapTimeSec"] - fl_df["LapTimeSec"].iloc[0]

                st.markdown('<div class="tt-wrap">', unsafe_allow_html=True)
                st.markdown("""
                <div style="display:grid;grid-template-columns:32px 70px 130px 90px;padding:7px 12px;border-bottom:2px solid #e10600;font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#333;background:#000">
                  <div>P</div><div>DRV</div><div>FASTEST LAP</div><div>GAP</div>
                </div>
                """, unsafe_allow_html=True)
                for idx, row in fl_df.iterrows():
                    d = row["Driver"]
                    team_name = ff1_laps.results[ff1_laps.results["Abbreviation"]==d]["TeamName"].values
                    col = tc(team_name[0] if len(team_name)>0 else "")
                    mins = int(row["LapTimeSec"]//60)
                    secs = row["LapTimeSec"]%60
                    gap = f"+{row['Gap']:.3f}s" if idx>0 else "⬡ FASTEST"
                    st.markdown(f"""
                    <div style="display:grid;grid-template-columns:32px 70px 130px 90px;padding:8px 12px;border-bottom:1px solid #111;align-items:center;font-size:13px">
                      <div class="std-pos">{idx+1}</div>
                      <div style="font-weight:900;color:{col}">{d}</div>
                      <div style="font-family:'Space Mono',monospace;font-size:12px;color:#f0f0f0">{mins}:{secs:06.3f}</div>
                      <div style="font-family:'Space Mono',monospace;font-size:11px;color:{'#e10600' if idx==0 else '#555'}">{gap}</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # Stint length chart
                if "Compound" in laps_df.columns:
                    st.markdown('<div class="sec">Tyre Stint Analysis</div>', unsafe_allow_html=True)
                    strat_df = laps_df.groupby(["Driver","Compound"]).agg(Laps=("LapNumber","count")).reset_index()
                    strat_df = strat_df[strat_df["Driver"].isin(sel_drvs)]
                    fig_t = px.bar(strat_df, x="Driver", y="Laps", color="Compound",
                                   color_discrete_map=TYRE_COLORS, barmode="stack")
                    fig_t.update_layout(
                        paper_bgcolor="#0d0d0d", plot_bgcolor="#0d0d0d",
                        font=dict(family="Barlow Condensed", color="#f0f0f0"),
                        xaxis=dict(gridcolor="transparent", tickfont=dict(color="#666",size=11)),
                        yaxis=dict(title="Laps", gridcolor="#111", tickfont=dict(color="#555")),
                        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=12)),
                        margin=dict(l=10,r=10,t=10,b=10), height=280
                    )
                    st.plotly_chart(fig_t, use_container_width=True, config={"displayModeBar":False})

        else:
            st.markdown('<div class="empty">FastF1 lap data available 1-2 days after each race weekend.<br>Monaco weekend starts Jun 5 — check back Sunday evening.</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — WEATHER + RACE CONTROL
# ══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    col_wx, col_rc = st.columns([1,2])

    with col_wx:
        st.markdown('<div class="sec">Track Weather</div>', unsafe_allow_html=True)
        if sess_key and (is_live or is_recent):
            wx_raw = fetch_openf1("weather", f"session_key={sess_key}")
            wx = wx_raw[-1] if wx_raw else None
        else:
            wx = None

        if wx:
            rain = "🌧 Rain" if wx.get("rainfall",0) > 0 else "☀️ Dry"
            wx_items = [
                (f"{wx.get('track_temperature','—')}°C","Track Temp"),
                (f"{wx.get('air_temperature','—')}°C","Air Temp"),
                (f"{wx.get('humidity','—')}%","Humidity"),
                (f"{wx.get('wind_speed','—')} m/s","Wind"),
                (f"{wx.get('pressure','—')}","Pressure"),
                (rain,"Conditions"),
            ]
            st.markdown('<div class="wx-grid">', unsafe_allow_html=True)
            for val, label in wx_items:
                st.markdown(f'<div class="wx-card"><div class="wx-val">{val}</div><div class="wx-lab">{label}</div></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            # Show next race weather placeholder
            if next_race:
                facts = CIRCUIT_FACTS.get(next_race["name"], {})
                st.markdown(f"""
                <div style="background:#0d0d0d;border:1px solid #1a1a1a;padding:18px;margin-bottom:16px">
                  <div style="font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#444;margin-bottom:8px">Next Race · {next_race['name']}</div>
                  <div style="font-size:13px;color:#555;font-family:'Space Mono',monospace">Live weather data streams during active sessions only</div>
                  {f'<div style="font-size:12px;color:#555;margin-top:10px;font-style:italic">💡 {facts.get("fact","")}</div>' if facts else ''}
                </div>
                """, unsafe_allow_html=True)

    with col_rc:
        st.markdown('<div class="sec">Race Control Feed</div>', unsafe_allow_html=True)
        if sess_key and (is_live or is_recent):
            rc_raw = fetch_openf1("race_control", f"session_key={sess_key}")
        else:
            rc_raw = []

        if rc_raw:
            st.markdown('<div class="rc-feed">', unsafe_allow_html=True)
            for msg in reversed(rc_raw[-80:]):
                m = msg.get("message","")
                mu = m.upper()
                t = msg.get("date","")
                if t:
                    try: t = datetime.fromisoformat(t.replace("Z","+00:00")).strftime("%H:%M:%S")
                    except: pass
                cc,cl = "rc-inf","INFO"
                if "SAFETY CAR" in mu and "VIRTUAL" not in mu and "CLEAR" not in mu: cc,cl="rc-sc","SC"
                elif "VIRTUAL SAFETY CAR" in mu or "VSC" in mu: cc,cl="rc-sc","VSC"
                elif "RED FLAG" in mu: cc,cl="rc-red","RED"
                elif "YELLOW" in mu: cc,cl="rc-red","YEL"
                elif "DRS ENABLED" in mu: cc,cl="rc-drs","DRS"
                elif "DRS DISABLED" in mu: cc,cl="rc-inf","DRS"
                elif "FASTEST LAP" in mu: cc,cl="rc-drs","FL"
                elif "PENALTY" in mu or "INVESTIGATION" in mu or "UNDER INVESTIGATION" in mu: cc,cl="rc-pen","PEN"
                elif "RETIRE" in mu or "RETIRED" in mu: cc,cl="rc-pen","RET"
                st.markdown(f'<div class="rc-row"><div class="rc-time">{t}</div><div><span class="rc-badge {cc}">{cl}</span><span class="rc-msg">{m}</span></div></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty">Race control messages stream live during active sessions.<br>Monaco FP1 starts Friday 5 June.</div>', unsafe_allow_html=True)

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-top:1px solid #111;margin-top:20px;padding:16px 28px;font-family:'Space Mono',monospace;font-size:10px;color:#2a2a2a;text-align:center;line-height:1.8">
  Powered by <strong style="color:#333">FastF1</strong> · <strong style="color:#333">OpenF1 API</strong> · <strong style="color:#333">formula1.com</strong><br>
  Timing: live during sessions · Standings: auto-updated · Lap analysis: 1-2 days post-race
</div>
""", unsafe_allow_html=True)
