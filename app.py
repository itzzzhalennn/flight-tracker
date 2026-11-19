import time
from urllib.parse import quote

import pandas as pd
import requests
import streamlit as st

API_BASE = "https://api.adsb.lol"
HEADERS = {"User-Agent": "BeginnerFlightTracker/1.0 (educational project)"}

st.set_page_config(
    page_title="Flight Tracker",
    page_icon="✈️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp { background: #080b12; color: #eef2ff; }
    [data-testid="stHeader"] { background: rgba(8, 11, 18, 0.9); }
    div[data-testid="stMetric"] {
        background: #111827; border: 1px solid #263247;
        padding: 12px; border-radius: 12px;
    }
    .hero {
        padding: 22px; border-radius: 18px;
        background: linear-gradient(120deg, #151d2e, #25111c);
        border: 1px solid #713047; margin-bottom: 18px;
    }
    .muted { color: #aab4c5; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>✈️ FLIGHT TRACKER</h1>
      <p class="muted">Live aircraft positions from the ADS-B network</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "Educational flight-tracking demo. Aircraft broadcasts are not the same as "
    "airline schedule data; gates, ticket status, and guaranteed arrival times are not provided."
)


@st.cache_data(ttl=20, show_spinner=False)
def fetch_json(url: str):
    """Fetch JSON from the public ADSB.lol API and cache it briefly."""
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    return response.json()


def get_aircraft(payload):
    """Normalize the aircraft list returned by the API."""
    if isinstance(payload, dict):
        aircraft = payload.get("ac", [])
        if isinstance(aircraft, list):
            return aircraft
    return []


def safe_number(value):
    try:
        if value is None or value == "ground":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def show_aircraft(aircraft):
    if not aircraft:
        st.warning("No aircraft found. Check the callsign or try again in a moment.")
        return

    rows = []
    for item in aircraft:
        lat = safe_number(item.get("lat"))
        lon = safe_number(item.get("lon"))
        if lat is not None and lon is not None:
            rows.append({"lat": lat, "lon": lon})

    first = aircraft[0]
    callsign = (first.get("flight") or "Unknown").strip()
    registration = first.get("r") or "Unknown"
    hex_code = first.get("hex") or "Unknown"
    altitude = first.get("alt_baro", "Unknown")
    speed = first.get("gs", "Unknown")
    heading = first.get("track", "Unknown")

    a, b, c, d = st.columns(4)
    a.metric("Aircraft found", len(aircraft))
    b.metric("Callsign", callsign)
    c.metric("Altitude", f"{altitude} ft" if isinstance(altitude, (int, float)) else str(altitude))
    d.metric("Ground speed", f"{speed} kt" if isinstance(speed, (int, float)) else str(speed))

    st.subheader("Aircraft details")
    st.write(
        {
            "Registration": registration,
            "ICAO hex": hex_code,
            "Heading": f"{heading}°" if heading != "Unknown" else heading,
            "Squawk": first.get("squawk", "Unknown"),
            "Aircraft type": first.get("t", "Unknown"),
            "Description": first.get("desc", "Unknown"),
        }
    )

    if rows:
        st.subheader("Aircraft map")
        st.map(pd.DataFrame(rows), latitude="lat", longitude="lon")
    else:
        st.info("The aircraft was found, but its current coordinates were not included.")


with st.sidebar:
    st.header("Tracker menu")
    mode = st.radio("Choose a search", ["Search by callsign", "Aircraft near a location"])
    st.divider()
    st.caption("Data source: ADSB.lol")
    st.caption("Please use the refresh button thoughtfully. Public API limits apply.")


if mode == "Search by callsign":
    st.subheader("Search for a flight")
    st.write("Enter the aircraft's radio callsign. For example, an airline flight may use a code like ACA123.")
    callsign_input = st.text_input("Flight callsign", placeholder="e.g. ACA123").strip().upper()
    search = st.button("🔎 Find aircraft", type="primary", use_container_width=True)

    if search:
        if not callsign_input:
            st.error("Enter a callsign first.")
        else:
            url = f"{API_BASE}/v2/callsign/{quote(callsign_input, safe='')}"
            try:
                with st.spinner("Searching live aircraft data..."):
                    payload = fetch_json(url)
                show_aircraft(get_aircraft(payload))
                st.caption(f"Last checked: {time.strftime('%H:%M:%S UTC', time.gmtime())}")
            except requests.HTTPError as exc:
                code = exc.response.status_code if exc.response is not None else "unknown"
                if code == 404:
                    st.warning("No matching aircraft was found right now. It may not be airborne, broadcasting, or covered.")
                elif code == 429:
                    st.error("The public data service rate limit was reached. Wait before trying again.")
                else:
                    st.error(f"The data service returned HTTP {code}. Try again later.")
            except requests.RequestException:
                st.error("Could not connect to the aircraft data service. Check your connection and try again.")
            except ValueError:
                st.error("The data service returned data the app could not read.")


else:
    st.subheader("Find aircraft near a location")
    st.write("Enter coordinates for a place you want to check. This searches a radius around that point.")
    left, right = st.columns(2)
    with left:
        latitude = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=51.0447, format="%.4f")
    with right:
        longitude = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=-114.0719, format="%.4f")
    radius = st.select_slider("Search radius", options=[10, 25, 50, 75, 100], value=25, format_func=lambda x: f"{x} km")
    search_nearby = st.button("📡 Find nearby aircraft", type="primary", use_container_width=True)

    if search_nearby:
        # ADSB.lol distance is specified in nautical miles.
        radius_nm = int(round(radius / 1.852))
        url = f"{API_BASE}/v2/lat/{latitude}/lon/{longitude}/dist/{radius_nm}"
        try:
            with st.spinner("Scanning aircraft in the selected area..."):
                payload = fetch_json(url)
            aircraft = get_aircraft(payload)
            if not aircraft:
                st.info("No aircraft were returned for this area right now.")
            else:
                st.success(f"Found {len(aircraft)} aircraft.")
                rows = []
                for item in aircraft:
                    lat = safe_number(item.get("lat"))
                    lon = safe_number(item.get("lon"))
                    if lat is not None and lon is not None:
                        rows.append({
                            "Callsign": (item.get("flight") or "Unknown").strip(),
                            "Aircraft": item.get("t") or "Unknown",
                            "Altitude (ft)": item.get("alt_baro", "Unknown"),
                            "Speed (kt)": item.get("gs", "Unknown"),
                            "Heading": item.get("track", "Unknown"),
                            "lat": lat,
                            "lon": lon,
                        })
                if rows:
                    frame = pd.DataFrame(rows)
                    st.map(frame, latitude="lat", longitude="lon")
                    st.dataframe(frame.drop(columns=["lat", "lon"]), use_container_width=True, hide_index=True)
                else:
                    st.info("Aircraft were returned without map coordinates.")
        except requests.HTTPError as exc:
            code = exc.response.status_code if exc.response is not None else "unknown"
            st.error(f"The data service returned HTTP {code}. Try again later.")
        except requests.RequestException:
            st.error("Could not connect to the aircraft data service. Check your connection.")
        except ValueError:
            st.error("The data service returned data the app could not read.")


st.divider()
st.caption(
    "Data may be delayed, incomplete, or unavailable. Do not use this app for operational "
    "aviation decisions. ADSB.lol data is provided under the Open Database License (ODbL)."
)
