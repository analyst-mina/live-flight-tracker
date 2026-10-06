# Live Flight Tracker – Dubai & Gulf ✈️

A free, real-time dashboard that shows aircraft flying over Dubai and the Gulf region.

**Tools:** Python, Pandas, Streamlit, PyDeck, OpenSky Network API

## Features
- Live map of aircraft (updates on refresh)
- KPIs: aircraft in the air, on the ground, average altitude, average speed
- Filter by origin country
- Top origin countries chart and altitude chart
- Flight table + CSV download

## How to run
1. Install Anaconda and open Anaconda Prompt.
2. Install packages:
   ```
   pip install streamlit pandas pydeck requests
   ```
3. Put `app.py` and your `credentials.json` (OpenSky API client) in the same folder.
4. Go to that folder and run:
   ```
   streamlit run app.py
   ```
5. The dashboard opens in your browser at http://localhost:8501

## Data source
OpenSky Network (https://opensky-network.org) – free API, live aircraft positions.

## Note
Never upload `credentials.json` to GitHub. Add it to `.gitignore`.
