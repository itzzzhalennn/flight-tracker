
import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(
    page_title="Worldwide Flight Radar",
    page_icon="✈️",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #080b12;
    color: white;
}
h1, h2, h3 {
    color: #ff304f !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🌍 WORLDWIDE FLIGHT RADAR")
st.caption("Live aircraft positions around the world")

@st.cache_data(ttl=900)
def get_aircraft():
    url = "https://opensky-network.org/api/states/all"
    response = requests.get(url, timeout=45)
    response.raise_for_status()
    return response.json()

try:
    with st.spinner("Loading worldwide aircraft..."):
        data = get_aircraft()

    states = data.get("states") or []
    aircraft = []

    for plane in states:
        if plane[5] is None or plane[6] is None:
            continue

        aircraft.append({
            "Callsign": (plane[1] or "Unknown").strip(),
            "ICAO": plane[0],
            "Latitude": plane[6],
            "Longitude": plane[5],
            "Altitude (ft)": round(plane[7] * 3.28084)
                if plane[7] is not None else None,
            "Speed (knots)": round(plane[9] * 1.94384, 1)
                if plane[9] is not None else None,
            "Heading": round(plane[10])
                if plane[10] is not None else None,
            "On ground": plane[8]
        })

    df = pd.DataFrame(aircraft)

    if df.empty:
        st.warning("No aircraft positions are available right now.")
    else:
        airborne = df[df["On ground"] == False]

        a, b = st.columns(2)
        a.metric("Aircraft detected", f"{len(df):,}")
        b.metric("Aircraft airborne", f"{len(airborne):,}")

        st.subheader("🌎 Worldwide aircraft map")
        st.map(df, latitude="Latitude", longitude="Longitude")

        st.subheader("✈️ Aircraft database")

        search = st.text_input("Search callsign or aircraft ICAO")

        results = df

        if search:
            results = df[
                df["Callsign"].str.contains(
                    search, case=False, na=False
                ) |
                df["ICAO"].str.contains(
                    search, case=False, na=False
                )
            ]

        st.dataframe(
            results.drop(columns=["Latitude", "Longitude"]),
            use_container_width=True,
            hide_index=True
        )

except requests.HTTPError as error:
    st.error(f"Aircraft data service error: {error}")
    st.info("The OpenSky API may require authentication or have reached its request limit.")


except requests.RequestException as error:
    st.error(f"Connection failed: {error}")

except Exception as error:
    st.er
