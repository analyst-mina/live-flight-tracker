import json
import time
from pathlib import Path

import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

# ---------- Page setup ----------
st.set_page_config(page_title="Live Flight Tracker - Dubai & Gulf", page_icon="✈️", layout="wide")
st.title("✈️ Live Flight Tracker – Dubai & Gulf")
st.caption("Real-time aircraft data from the OpenSky Network API")

TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
STATES_URL = "https://opensky-network.org/api/states/all"

# Gulf area (south, north, west, east)
BOX = {"lamin": 22.0, "lamax": 30.0, "lomin": 48.0, "lomax": 60.0}

COLUMNS = [
    "icao24", "callsign", "origin_country", "time_position", "last_contact",
    "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
    "true_track", "vertical_rate", "sensors", "geo_altitude", "squawk",
    "spi", "position_source",
]


# ---------- Helpers ----------
def load_credentials():
    """Reads credentials.json from the same folder as app.py."""
    path = Path(__file__).parent / "credentials.json"
    with open(path) as f:
        data = json.load(f)
    client_id = data.get("clientId") or data.get("client_id")
    client_secret = data.get("clientSecret") or data.get("client_secret")
    return client_id, client_secret


@st.cache_data(ttl=1500)  # token is valid ~30 min
def get_token():
    client_id, client_secret = load_credentials()
    r = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


@st.cache_data(ttl=30)  # do not call the API more than every 30 seconds
def get_flights():
    headers = {"Authorization": f"Bearer {get_token()}"}
    r = requests.get(STATES_URL, params=BOX, headers=headers, timeout=30)
    r.raise_for_status()
    states = r.json().get("states") or []
    df = pd.DataFrame(states, columns=COLUMNS)
    df["callsign"] = df["callsign"].fillna("").str.strip()
    df["altitude_m"] = df["baro_altitude"].fillna(0).round(0)
    df["speed_kmh"] = (df["velocity"].fillna(0) * 3.6).round(0)
    df["status"] = df["on_ground"].map({True: "On ground", False: "In the air"})
    df = df.dropna(subset=["latitude", "longitude"])
    return df


# ---------- Sidebar ----------
st.sidebar.header("Filters")
show_ground = st.sidebar.checkbox("Show aircraft on ground", value=False)
auto = st.sidebar.checkbox("Auto-refresh every 60 seconds", value=False)

# ---------- Load data ----------
try:
    df = get_flights()
except Exception as e:
    st.error(f"Could not load data from OpenSky: {e}")
    st.stop()

countries = sorted(df["origin_country"].dropna().unique())
chosen = st.sidebar.multiselect("Origin country", countries)

view = df.copy()
if not show_ground:
    view = view[view["on_ground"] == False]  # noqa: E712
if chosen:
    view = view[view["origin_country"].isin(chosen)]

# ---------- KPIs ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("In the air", int((df["on_ground"] == False).sum()))  # noqa: E712
c2.metric("On the ground", int((df["on_ground"] == True).sum()))  # noqa: E712
c3.metric("Avg altitude (m)", f"{view['altitude_m'].mean():,.0f}" if len(view) else "-")
c4.metric("Avg speed (km/h)", f"{view['speed_kmh'].mean():,.0f}" if len(view) else "-")

# ---------- Map ----------
layer = pdk.Layer(
    "ScatterplotLayer",
    data=view,
    get_position="[longitude, latitude]",
    get_radius=6000,
    get_fill_color="[0, 120, 255, 160]",
    pickable=True,
)
deck = pdk.Deck(
    layers=[layer],
    initial_view_state=pdk.ViewState(latitude=25.2, longitude=55.3, zoom=5.2),
    tooltip={"text": "{callsign}\n{origin_country}\nAltitude: {altitude_m} m\nSpeed: {speed_kmh} km/h"},
)
st.pydeck_chart(deck)

# ---------- Charts ----------
left, right = st.columns(2)
with left:
    st.subheader("Top origin countries")
    st.bar_chart(view["origin_country"].value_counts().head(10))
with right:
    st.subheader("Altitude (m) of aircraft")
    st.bar_chart(view["altitude_m"].round(-3).value_counts().sort_index())

# ---------- Table ----------
st.subheader("Flight table")
st.dataframe(
    view[["callsign", "origin_country", "altitude_m", "speed_kmh", "status"]]
    .sort_values("altitude_m", ascending=False)
    .reset_index(drop=True),
    use_container_width=True,
)
st.download_button(
    "Download data as CSV",
    view.to_csv(index=False).encode("utf-8"),
    "gulf_flights.csv",
    "text/csv",
)

if auto:
    time.sleep(60)
    st.cache_data.clear()
    st.rerun()
