# ==============================================================================
# app.py — Bucharest Air Quality Dashboard (STARTER)
# ==============================================================================
# Welcome! This file is the heart of the dashboard.
# Streamlit reads it top to bottom every time someone opens your web app.
#
# Your job: fill in the 6 blocks marked   # === TODO N — YOUR CODE HERE ===
# Each TODO has a clear instruction. The slides walk you through every one.
#
# Everything else is already done for you. Don't change it unless a TODO says so.
# ==============================================================================


# ------------------------------------------------------------------------------
# SECTION A — IMPORTS & PAGE CONFIGURATION
# ------------------------------------------------------------------------------

import streamlit as st                          # The web framework — turns Python into a webpage
import pandas as pd                             # Tables of data, like Excel in code
import folium                                   # Interactive maps
from folium.plugins import HeatMap              # The colored "blob" overlay we put on the map
from streamlit_folium import st_folium          # Glue: shows a Folium map inside Streamlit
from datetime import datetime                   # For "last updated" timestamps
import time                                     # For the auto-refresh at the bottom

# Import our own helper file — the API call lives there
from data_fetcher import get_bucharest_air_quality


# ------------------------------------------------------------------------------
# st.set_page_config() — controls the browser tab and overall layout
# Must be the FIRST Streamlit command in the script
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Bucharest Air Quality",         # Text in the browser tab
    page_icon="🌬️",                              # Tab icon (favicon)
    layout="wide",                              # Use the full screen width
    initial_sidebar_state="collapsed",          # Sidebar hidden by default
)


# ------------------------------------------------------------------------------
# === TODO 1 — READ THE API KEY FROM STREAMLIT SECRETS ===
# ------------------------------------------------------------------------------
# Your API key is sensitive. We never put it directly in this file (anyone
# who sees the GitHub repo would have it). Instead, Streamlit has a built-in
# "secrets" system — you paste the key into Streamlit Cloud's settings panel,
# and it shows up here as st.secrets["OPENAQ_API_KEY"].
#
# Problem: if you haven't added the key yet, st.secrets crashes.
# Solution: wrap the read in a try / except — try to read, and if it fails,
# fall back to an empty string and warn the user.
#
# WHAT TO WRITE (replace the line below):
#   - A try block that sets OPENAQ_API_KEY from st.secrets["OPENAQ_API_KEY"]
#   - An except (KeyError, FileNotFoundError) block that sets OPENAQ_API_KEY = ""
#     and calls st.warning("⚠️ OpenAQ API key not configured. Using sample data only.")
# See slide for the exact code.

try:
   OPENAQ_API_KEY = st.secrets["OPENAQ_API_KEY"]
except (KeyError, FileNotFoundError):
    OPENAQ_API_KEY = ""
    st.warning("⚠️ OpenAQ API key not configured. Using sample data only.")
##

# ------------------------------------------------------------------------------
# === TODO 3 — CATEGORIZE PM2.5 INTO COLORED LABELS ===
# ------------------------------------------------------------------------------
# (We define this function up here because the rest of the page uses it.
#  You'll fill it in at Step 13 — for now leave the placeholder so the page loads.)
#
# WHAT IT DOES — takes a PM2.5 value and returns a dict like:
#   {"label": "Moderate", "color": "#FFCC4E", "advice": "..."}
#
# Replace the placeholder `return` line below with an if/elif/else chain.
# Thresholds (μg/m³):
#   < 12   → Good                              color #22C55E
#   < 35   → Moderate                          color #FFCC4E
#   < 55   → Unhealthy for Sensitive Groups    color #FF9800
#   < 150  → Unhealthy                         color #E53935
#   else   → Hazardous                         color #7e22ce
#
# Each return needs three keys: "label", "color", "advice".
# See slide for the exact code.
def get_air_quality_category(pm25: float) -> dict:
    # === TODO 3 — YOUR CODE HERE ===
    if pm25 < 12:
        return {"label": "Good", "color": "#22C55E",
                "advice": "Air quality is great. Enjoy outdoor activities."}
    elif pm25 < 35:
        return {"label": "Moderate", "color": "#FFCC4E",
                "advice": "OK for most. Sensitive groups should limit prolonged exertion."}
    elif pm25 < 55:
        return {"label": "Unhealthy for Sensitive Groups", "color": "#FF9800",
                "advice": "Children, elderly, and asthmatics should avoid outdoor activity."}
    elif pm25 < 150:
        return {"label": "Unhealthy", "color": "#E53935",
                "advice": "Everyone should reduce outdoor exertion."}
    else:
        return {"label": "Hazardous", "color": "#7e22ce",
                "advice": "Stay indoors. Use air filtration if possible."}

# ------------------------------------------------------------------------------
# SECTION B — HEADER & KEY METRICS
# ------------------------------------------------------------------------------

# Fetch the data ONCE and reuse it everywhere
# (cached for 5 minutes inside data_fetcher.py)
df = get_bucharest_air_quality(OPENAQ_API_KEY)


# ------------------------------------------------------------------------------
# HEADER BANNER — title and live timestamp (already done for you)
# ------------------------------------------------------------------------------
st.markdown(
    f"""
    <div style="
        background: linear-gradient(90deg, #0F6E56 0%, #185FA5 100%);
        padding: 20px 32px;
        border-radius: 12px;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
    ">
        <div>
            <div style="font-size: 28px; font-weight: 700;">🌬️ Bucharest Air Quality</div>
            <div style="font-size: 14px; opacity: 0.9; margin-top: 4px;">
                Live data from sensors across Bucharest
            </div>
        </div>
        <div style="text-align: right; font-size: 13px; opacity: 0.9;">
            <div>📅 {datetime.now().strftime('%B %d, %Y')}</div>
            <div>🕒 Updated {datetime.now().strftime('%H:%M')}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# Defensive: if we got no data at all, show an error and stop
if df.empty:
    st.error("⚠️ Unable to load air quality data. Please try again later.")
    st.stop()


# ------------------------------------------------------------------------------
# === TODO 2 — CALCULATE THE 4 METRICS ===
# ------------------------------------------------------------------------------
# Now we need to derive 5 numbers (and 2 station names) from our DataFrame `df`.
# These feed the 4 metric cards at the top of the page.
#
# Useful pandas methods (each is one line):
#   df["pm25"].mean()    → average across all rows
#   df["pm25"].max()     → largest single value
#   df["pm25"].min()     → smallest single value
#   df["pm25"].idxmax()  → the ROW INDEX of the max value
#   df.loc[index, "col"] → look up a cell by row index + column name
#
# WHAT TO WRITE — create these 5 variables:
#   avg_pm25       = the average PM2.5 across the whole DataFrame (round to 1 decimal)
#   sensor_count   = how many rows are in df  (hint: len(df))
#   worst_pm25     = the max PM2.5 reading
#   worst_station  = the station name where worst_pm25 occurred
#   best_pm25      = the min PM2.5 reading
#   best_station   = the station name where best_pm25 occurred

# === TODO 2 — YOUR CODE HERE ===
# (delete these placeholders and write the real lines)
avg_pm25 = round(df["pm25"].mean(), 1)
sensor_count = len(df)
worst_pm25 = df["pm25"].max()
worst_station = df.loc[df["pm25"].idxmax(), "station"]
best_pm25 = df["pm25"].min()
best_station = df.loc[df["pm25"].idxmin(), "station"]


# ------------------------------------------------------------------------------
# METRIC CARDS — display the 4 numbers as Streamlit metric widgets
# (already done for you — uses the variables you just created above)
# ------------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="🌍 City Average PM2.5",
        value=f"{avg_pm25} μg/m³",
        help="Average across all active sensors in Bucharest",
    )

with col2:
    st.metric(
        label=f"🔴 Worst: {worst_station}",
        value=f"{worst_pm25} μg/m³",
        help="The station with the highest PM2.5 reading right now",
    )

with col3:
    st.metric(
        label=f"🟢 Best: {best_station}",
        value=f"{best_pm25} μg/m³",
        help="The station with the lowest PM2.5 reading right now",
    )

with col4:
    st.metric(
        label="📡 Active Sensors",
        value=sensor_count,
        help="How many sensors are currently reporting data",
    )


# Small note showing where the data came from (live API or fallback CSV)
data_source = df["source"].iloc[0]
if data_source == "OpenAQ Live":
    st.caption(f"✅ Data source: **OpenAQ Live API** — last refreshed {df['last_updated'].iloc[0]}")
else:
    st.caption(f"📦 Data source: **{data_source}** — using bundled sample data")


# ------------------------------------------------------------------------------
# SECTION C — ALERT BANNER & FOLIUM HEATMAP
# ------------------------------------------------------------------------------

# Use the helper function (which YOU will write in TODO 3) to convert the
# city-average PM2.5 into a color, label, and advice message
category = get_air_quality_category(avg_pm25)

st.markdown(
    f"""
    <div style="
        background: {category['color']};
        padding: 16px 24px;
        border-radius: 12px;
        margin: 24px 0 16px 0;
        display: flex;
        align-items: center;
        gap: 16px;
        color: #000;
    ">
        <div style="font-size: 28px;">⚠️</div>
        <div>
            <div style="font-size: 18px; font-weight: 700;">{category['label'].upper()}</div>
            <div style="font-size: 13px; margin-top: 2px;">{category['advice']}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------------------
# MAP SECTION HEADER
# ------------------------------------------------------------------------------
st.subheader("🗺️ Live Air Quality Heatmap")
st.caption("Colored zones show pollution intensity across the city. Click a marker for details.")


# Build the Folium base map centered on Bucharest (already done for you)
m = folium.Map(
    location=[44.4268, 26.1025],     # Bucharest center
    zoom_start=11,                    # Good city-level zoom
    tiles="OpenStreetMap",            # Free, no API key
)


# ------------------------------------------------------------------------------
# === TODO 4 — BUILD THE HEATMAP DATA ===
# ------------------------------------------------------------------------------
# The HeatMap plugin needs a list of [latitude, longitude, intensity] triples,
# one for each sensor. We have to build that list from `df`.
#
# Useful pattern (list comprehension):
#   [expression for variable in iterable]
#
# To loop through DataFrame rows we use:  df.iterrows()
# which gives back pairs of (index, row). We ignore the index using `_`.
#
# WHAT TO WRITE — set heat_data to a list comprehension that builds:
#   [row["lat"], row["lon"], row["pm25"]] for each row in df

# === TODO 4 — YOUR CODE HERE ===
heat_data = []  # ← replace with the list comprehension


# Color gradient for the heatmap (already done for you)
gradient = {
    0.0: "#22C55E",   # green — Good
    0.4: "#FFCC4E",   # yellow — Moderate
    0.7: "#FF9800",   # orange — Unhealthy for sensitive
    1.0: "#E53935",   # red — Unhealthy
}

# Add the heat layer to the map
HeatMap(
    heat_data,
    radius=35,
    blur=25,
    min_opacity=0.4,
    gradient=gradient,
).add_to(m)


# ------------------------------------------------------------------------------
# === TODO 5 — ADD A CLICKABLE MARKER FOR EACH SENSOR ===
# ------------------------------------------------------------------------------
# The heatmap shows the big picture, but users also want to click an exact
# sensor and see its precise reading. We add one CircleMarker per row in df.
#
# Pattern (a regular for loop):
#   for _, row in df.iterrows():
#       ... do something with row["station"], row["lat"], row["lon"], row["pm25"]
#
# Inside the loop:
#   1. Call get_air_quality_category(row["pm25"]) → store as sensor_category
#   2. Build popup_html — an f-string with the station name, PM2.5 value,
#      and the category label (see slide for the exact HTML)
#   3. Create a folium.CircleMarker with:
#        - location=[row["lat"], row["lon"]]
#        - radius=8
#        - popup=folium.Popup(popup_html, max_width=250)
#        - tooltip=f"{row['station']}: {row['pm25']} μg/m³"
#        - color="white", weight=2, fill=True
#        - fill_color=sensor_category["color"], fill_opacity=0.9
#      …and call .add_to(m) at the end

# === TODO 5 — YOUR CODE HERE ===
# (a for loop over df.iterrows() goes here — see slide)


# ------------------------------------------------------------------------------
# RENDER THE MAP IN STREAMLIT (already done for you)
# ------------------------------------------------------------------------------
st_folium(
    m,
    width=None,
    height=500,
    returned_objects=[],
)


# ------------------------------------------------------------------------------
# SECTION D — "CAN I EXERCISE OUTSIDE?" RECOMMENDATION PANEL
# ------------------------------------------------------------------------------

st.subheader("🏃 Can I exercise outside?")
st.caption("Based on the current city-average PM2.5 levels.")


# ------------------------------------------------------------------------------
# === TODO 6 — DECIDE THE VERDICT BASED ON avg_pm25 ===
# ------------------------------------------------------------------------------
# We translate the average PM2.5 into a traffic-light style verdict.
# The user shouldn't have to know what "35 μg/m³" means — they want to know:
#   "Can I go for a run? Should my kid play outside?"
#
# WHAT TO WRITE — an if / elif / else chain that sets FOUR variables:
#   verdict_emoji, verdict_text, verdict_color, detailed_message
#
# Use these thresholds and values (see slide for exact text):
#   avg_pm25 < 12   → 🟢 "YES — GO ENJOY IT"     color #22C55E
#   avg_pm25 < 35   → 🟡 "MOSTLY OK"             color #FFCC4E
#   avg_pm25 < 55   → 🟠 "BE CAREFUL"            color #FF9800
#   avg_pm25 < 150  → 🔴 "NOT TODAY"             color #E53935
#   else            → 🟣 "STAY INDOORS"          color #7e22ce

# === TODO 6 — YOUR CODE HERE ===
verdict_emoji = "❓"
verdict_text = "TODO"
verdict_color = "#888888"
detailed_message = "Fill in TODO 6 to see the verdict."


# ------------------------------------------------------------------------------
# RECOMMENDATION CARD — big colored verdict box (already done for you)
# ------------------------------------------------------------------------------
rec_col1, rec_col2 = st.columns([1, 3])

with rec_col1:
    st.markdown(
        f"""
        <div style="
            display: flex;
            justify-content: center;
            align-items: center;
            background: {verdict_color};
            border-radius: 50%;
            width: 140px;
            height: 140px;
            margin: 20px auto;
            font-size: 64px;
        ">
            {verdict_emoji}
        </div>
        """,
        unsafe_allow_html=True,
    )

with rec_col2:
    st.markdown(
        f"""
        <div style="padding: 30px 0 0 0;">
            <div style="font-size: 32px; font-weight: 700; color: {verdict_color};">
                {verdict_text}
            </div>
            <div style="font-size: 14px; margin-top: 8px; line-height: 1.5;">
                {detailed_message}
            </div>
            <div style="font-size: 12px; margin-top: 12px; opacity: 0.7;">
                Current city average: <b>{avg_pm25} μg/m³</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Tip pointing users to the cleanest sensor right now
st.info(
    f"💡 **Tip:** The cleanest air right now is at **{best_station}** "
    f"({best_pm25} μg/m³). If you're flexible on location, that's your best bet."
)


# ------------------------------------------------------------------------------
# SECTION E — STATIONS TABLE, AUTO-REFRESH & FOOTER
# ------------------------------------------------------------------------------

st.subheader("📊 All sensors — detailed view")
st.caption("Sorted by PM2.5 (cleanest first).")

# Build a clean display version of the DataFrame (already done for you)
display_df = df.copy()
display_df["Status"] = display_df["pm25"].apply(
    lambda v: get_air_quality_category(v)["label"]
)
display_df = display_df.sort_values("pm25", ascending=True)
display_df = display_df[["station", "pm25", "Status", "last_updated"]]
display_df = display_df.rename(columns={
    "station": "Station",
    "pm25": "PM2.5 (μg/m³)",
    "last_updated": "Updated",
})
st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)


# ------------------------------------------------------------------------------
# FOOTER (already done for you)
# ------------------------------------------------------------------------------
st.markdown("---")
foot_col1, foot_col2 = st.columns([2, 1])

with foot_col1:
    st.markdown(
        """
        <div style="font-size: 12px; opacity: 0.7;">
            🌬️ <b>Bucharest Air Quality Dashboard</b><br>
            Built during SHIFT4IT bootcamp by <i>hackathon participants</i><br>
            Data: <a href="https://openaq.org" target="_blank">OpenAQ</a> ·
            Map: <a href="https://openstreetmap.org" target="_blank">OpenStreetMap</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

with foot_col2:
    st.markdown(
        f"""
        <div style="font-size: 12px; opacity: 0.7; text-align: right;">
            🔄 Auto-refreshes every 60 seconds<br>
            Last refresh: <b>{datetime.now().strftime('%H:%M:%S')}</b>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------------------
# AUTO-REFRESH — keep the dashboard "live" (already done for you)
# ------------------------------------------------------------------------------
# Sleep for 60s then re-run the whole script. Must be LAST in the file.
time.sleep(60)
st.rerun()
