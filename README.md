# Flight Tracker

A beginner-friendly, mobile-friendly Python flight tracker built with Streamlit and the public ADSB.lol aircraft data API.

## Features
- Search for an aircraft by radio callsign (for example, ACA123).
- Search for aircraft near latitude/longitude coordinates.
- Display aircraft details and plot available positions on a map.
- Briefly cache API responses to avoid unnecessary repeated requests.

## Important limitations
- An airline flight number and an aircraft's radio callsign are not always identical.
- This app reads aircraft broadcast/ADS-B data. It does not provide airline schedules, gates, ticket information, or guaranteed arrival times.
- Coverage can be incomplete, and aircraft may not appear if they are not broadcasting or are outside receiver coverage.
- Do not use this app for real-world flight operations.

## Run locally
Requires Python 3.10 or newer.

```bash
python -m venv .venv
```

Activate the environment:

**Windows**
```bash
.venv\Scripts\activate
```

**macOS/Linux**
```bash
source .venv/bin/activate
```

Install dependencies and start the app:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy for iPhone use
1. Put `app.py`, `requirements.txt`, and this README in a GitHub repository.
2. Open https://share.streamlit.io and sign in with GitHub.
3. Choose **Create app**, select your repository, branch, and `app.py`.
4. Deploy. Streamlit gives you a website URL that opens in Safari on your iPhone.

Official deployment guide: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy
