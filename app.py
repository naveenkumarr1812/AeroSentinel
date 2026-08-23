import streamlit as st
import uuid
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from langgraph.types import Command

from graph.workflow import graph, fleet, vision_analyzer, memory_agent


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AeroSentinel",
    page_icon="🛰️",
    layout="wide",
)


# ============================================================
# DESIGN TOKENS + GLOBAL STYLE
# ------------------------------------------------------------
# Aesthetic: tactical mission console / HUD readout — dark
# instrument panel, condensed technical type for headers,
# monospace for telemetry data, reticle-bracket corners as
# the signature motif, three-tier status color language
# (cyan = nominal, amber = caution, red = critical, green =
# cleared/approved). Built for a drone ops product, not a
# generic dashboard skin.
# ============================================================

st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">

    <style>

    :root {
        --bg: #090c10;
        --bg-panel: #10151c;
        --bg-panel-alt: #141a22;
        --border: #232b36;
        --border-active: #34404e;
        --text: #dce3eb;
        --text-dim: #6b7684;
        --cyan: #4fe0d8;
        --cyan-dim: rgba(79, 224, 216, 0.10);
        --amber: #f0a93b;
        --amber-dim: rgba(240, 169, 59, 0.10);
        --red: #f2495c;
        --red-dim: rgba(242, 73, 92, 0.10);
        --green: #5fd97a;
        --green-dim: rgba(95, 217, 122, 0.10);
    }

    /* ---------- base canvas ---------- */

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(ellipse 900px 500px at 15% -10%, rgba(79,224,216,0.06), transparent 60%),
            radial-gradient(ellipse 700px 500px at 100% 0%, rgba(240,169,59,0.04), transparent 55%),
            var(--bg);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    .block-container {
        padding-top: 2rem;
        max-width: 1180px;
    }

    html, body, [class*="css"] {
        color: var(--text);
        font-family: 'JetBrains Mono', monospace;
    }

    p, span, label, div {
        font-family: 'JetBrains Mono', monospace;
    }

    /* ---------- sidebar / mission control console ---------- */

    [data-testid="stSidebar"] {
        background: var(--bg-panel);
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] .block-container {
        padding-top: 1.6rem;
    }

    [data-testid="stSidebar"] h2 {
        font-family: 'Chakra Petch', sans-serif;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--cyan);
        border-bottom: 1px solid var(--border);
        padding-bottom: 10px;
        margin-bottom: 16px;
    }

    [data-testid="stSidebar"] label {
        font-size: 11px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--text-dim);
    }

    [data-testid="stSidebar"] textarea {
        background: var(--bg-panel-alt) !important;
        border: 1px solid var(--border) !important;
        color: var(--text) !important;
        border-radius: 3px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 13px !important;
    }

    [data-testid="stSidebar"] textarea:focus {
        border-color: var(--cyan) !important;
        box-shadow: 0 0 0 1px var(--cyan) !important;
    }

    /* ---------- buttons ---------- */

    .stButton > button {
        width: 100%;
        background: var(--bg-panel-alt);
        border: 1px solid var(--border-active);
        color: var(--text);
        border-radius: 3px;
        font-family: 'Chakra Petch', sans-serif;
        font-weight: 600;
        font-size: 12.5px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 0.55rem 1rem;
        transition: all 0.15s ease;
    }

    .stButton > button:hover {
        border-color: var(--cyan);
        color: var(--cyan);
        background: var(--cyan-dim);
    }

    .stButton > button:active {
        transform: translateY(1px);
    }

    [data-testid="stSidebar"] .stButton:first-of-type > button {
        border-color: var(--cyan);
        color: var(--cyan);
        background: var(--cyan-dim);
    }

    [data-testid="stSidebar"] .stButton:first-of-type > button:hover {
        background: var(--cyan);
        color: #04100e;
    }

    /* ---------- text input ---------- */

    .stTextInput > div > div > input {
        background: var(--bg-panel-alt) !important;
        border: 1px solid var(--border) !important;
        color: var(--text) !important;
        border-radius: 3px !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--cyan) !important;
        box-shadow: 0 0 0 1px var(--cyan) !important;
    }

    /* ---------- expanders (SOP / memory panels) ---------- */

    [data-testid="stExpander"] {
        background: var(--bg-panel);
        border: 1px solid var(--border) !important;
        border-radius: 4px;
    }

    [data-testid="stExpander"] summary {
        font-family: 'JetBrains Mono', monospace;
        font-size: 12.5px;
        color: var(--text);
    }

    /* ---------- misc cleanup ---------- */

    hr {
        border-color: var(--border) !important;
    }

    [data-testid="stCaptionContainer"] {
        color: var(--text-dim) !important;
        letter-spacing: 0.04em;
    }

    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: var(--border-active); border-radius: 4px; }

    /* ---------- signature motif: reticle-bracket panel ---------- */

    .rt-panel {
        position: relative;
        border: 1px solid var(--border);
        background: var(--bg-panel);
        border-radius: 2px;
        padding: 18px 20px;
    }

    .rt-panel::before, .rt-panel::after,
    .rt-corner-tl, .rt-corner-br {
        content: "";
        position: absolute;
        width: 12px;
        height: 12px;
        border-color: var(--cyan);
        opacity: 0.85;
    }

    .rt-panel::before {
        top: -1px; left: -1px;
        border-top: 2px solid var(--cyan);
        border-left: 2px solid var(--cyan);
    }

    .rt-panel::after {
        bottom: -1px; right: -1px;
        border-bottom: 2px solid var(--cyan);
        border-right: 2px solid var(--cyan);
    }

    /* ---------- eyebrow / section label ---------- */

    .rt-eyebrow {
        font-family: 'Chakra Petch', sans-serif;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--text-dim);
        margin: 30px 0 12px 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .rt-eyebrow::after {
        content: "";
        flex: 1;
        height: 1px;
        background: var(--border);
    }

    /* ---------- header block ---------- */

    .rt-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        border: 1px solid var(--border);
        background: linear-gradient(180deg, var(--bg-panel), var(--bg-panel-alt));
        border-radius: 3px;
        padding: 20px 26px;
        margin-bottom: 6px;
        position: relative;
        overflow: hidden;
    }

    .rt-header::before {
        content: "";
        position: absolute;
        inset: 0;
        background: repeating-linear-gradient(
            100deg,
            transparent 0px,
            transparent 38px,
            rgba(79,224,216,0.035) 39px,
            transparent 40px
        );
        pointer-events: none;
    }

    .rt-title {
        font-family: 'Chakra Petch', sans-serif;
        font-size: 30px;
        font-weight: 700;
        letter-spacing: 0.02em;
        color: var(--text);
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .rt-subtitle {
        font-size: 12.5px;
        color: var(--text-dim);
        letter-spacing: 0.05em;
        margin-top: 4px;
    }

    .rt-status-pill {
        font-family: 'Chakra Petch', sans-serif;
        font-size: 11.5px;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        padding: 7px 14px;
        border-radius: 20px;
        display: flex;
        align-items: center;
        gap: 8px;
        white-space: nowrap;
    }

    .dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        display: inline-block;
    }

    .dot-pulse {
        animation: pulse 1.6s ease-in-out infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; box-shadow: 0 0 0 0 currentColor; }
        50% { opacity: 0.55; }
    }

    /* tone helpers */
    .tone-cyan   { color: var(--cyan);  border: 1px solid var(--cyan);  background: var(--cyan-dim); }
    .tone-amber  { color: var(--amber); border: 1px solid var(--amber); background: var(--amber-dim); }
    .tone-red    { color: var(--red);   border: 1px solid var(--red);   background: var(--red-dim); }
    .tone-green  { color: var(--green); border: 1px solid var(--green); background: var(--green-dim); }
    .tone-dim    { color: var(--text-dim); border: 1px solid var(--border); background: var(--bg-panel-alt); }

    /* ---------- stat / telemetry cards ---------- */

    .rt-stat {
        border: 1px solid var(--border);
        background: var(--bg-panel);
        border-radius: 3px;
        padding: 14px 16px;
        height: 100%;
    }

    .rt-stat-label {
        font-family: 'Chakra Petch', sans-serif;
        font-size: 10.5px;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--text-dim);
        margin-bottom: 8px;
    }

    .rt-stat-value {
        font-size: 20px;
        font-weight: 600;
        color: var(--text);
        letter-spacing: 0.01em;
        word-break: break-word;
    }

    /* ---------- pipeline signal chain ---------- */

    .rt-chain {
        display: flex;
        align-items: stretch;
        border: 1px solid var(--border);
        background: var(--bg-panel);
        border-radius: 3px;
        padding: 18px 10px;
        gap: 0;
    }

    .rt-node {
        flex: 1 1 0;
        min-width: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        position: relative;
        padding: 0 3px;
    }

    .rt-node:not(:last-child)::after {
        content: "";
        position: absolute;
        top: 17px;
        left: 58%;
        width: 84%;
        height: 1px;
        background: var(--border-active);
        z-index: 0;
    }

    .rt-node.node-on:not(:last-child)::after {
        background: linear-gradient(90deg, var(--cyan), var(--border-active));
    }

    .rt-node-icon {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        border: 1px solid var(--border-active);
        background: var(--bg-panel-alt);
        z-index: 1;
        position: relative;
        flex-shrink: 0;
    }

    .rt-node.node-on .rt-node-icon {
        border-color: var(--cyan);
        background: var(--cyan-dim);
        box-shadow: 0 0 14px rgba(79,224,216,0.25);
    }

    .rt-node-label {
        font-size: 8.5px;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        text-align: center;
        color: var(--text-dim);
        line-height: 1.25;
        word-break: break-word;
        max-width: 100%;
    }

    .rt-node.node-on .rt-node-label {
        color: var(--text);
    }

    /* ---------- alert / report banner ---------- */

    .rt-alert {
        border-radius: 3px;
        padding: 16px 18px;
        border-left: 3px solid;
        font-size: 13px;
        line-height: 1.55;
        white-space: pre-wrap;
    }

    .rt-alert-title {
        font-family: 'Chakra Petch', sans-serif;
        font-weight: 700;
        font-size: 12px;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 6px;
        display: block;
    }

    /* ---------- architecture table (idle state) ---------- */

    .rt-flow {
        font-family: 'Chakra Petch', sans-serif;
        font-size: 13px;
        letter-spacing: 0.03em;
        color: var(--cyan);
        text-align: center;
        padding: 14px;
        border: 1px dashed var(--border-active);
        border-radius: 3px;
        margin: 16px 0 22px 0;
        background: var(--bg-panel-alt);
    }

    table {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 12.5px !important;
    }

    /* ---------- fleet roster (now rendered per-column, not a CSS grid) ---------- */

    .rt-fleet-card {
        position: relative;
        border: 1px solid var(--border);
        background: var(--bg-panel);
        border-radius: 4px;
        padding: 20px 20px;
        min-height: 168px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }

    .rt-fleet-card.fleet-active {
        border-color: var(--green);
        background: var(--green-dim);
        box-shadow: 0 0 16px rgba(95, 217, 122, 0.22);
    }

    .rt-fleet-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 14px;
        gap: 10px;
    }

    .rt-fleet-name {
        font-family: 'Chakra Petch', sans-serif;
        font-weight: 700;
        font-size: 16px;
        letter-spacing: 0.02em;
        color: var(--text);
        white-space: nowrap;
    }

    .rt-fleet-badge {
        font-family: 'Chakra Petch', sans-serif;
        font-size: 10.5px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 4px 11px;
        border-radius: 12px;
        white-space: nowrap;
    }

    .rt-fleet-meta {
        font-size: 12.5px;
        color: var(--text-dim);
        letter-spacing: 0.03em;
        margin-bottom: 14px;
    }

    .rt-fleet-battery-row {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .rt-fleet-battery-track {
        flex: 1;
        height: 7px;
        border-radius: 4px;
        background: var(--bg-panel-alt);
        border: 1px solid var(--border);
        overflow: hidden;
    }

    .rt-fleet-battery-fill {
        height: 100%;
        border-radius: 4px;
    }

    .rt-fleet-battery-pct {
        font-size: 12.5px;
        color: var(--text-dim);
        min-width: 36px;
        text-align: right;
    }

    /* ---------- inspection zones ---------- */

    .rt-zone-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
    }

    @media (max-width: 700px) {
        .rt-zone-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }

    .rt-zone-card {
        border: 1px solid var(--border);
        background: var(--bg-panel);
        border-radius: 5px;
        padding: 28px 16px;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        transition: border-color 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
    }

    .rt-zone-card.zone-active {
        border-color: var(--cyan);
        background: var(--cyan-dim);
        box-shadow: 0 0 18px rgba(79, 224, 216, 0.25);
    }

    .rt-zone-icon {
        font-size: 40px;
        margin-bottom: 12px;
        line-height: 1;
    }

    .rt-zone-label {
        font-family: 'Chakra Petch', sans-serif;
        font-weight: 600;
        font-size: 14px;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--text);
    }

    .rt-zone-card.zone-active .rt-zone-label {
        color: var(--cyan);
    }

    /* ---------- image chat: bounded, independently scrollable ---------- */

    .rt-chat-scroll {
        max-height: 420px;
        overflow-y: auto;
        border: 1px solid var(--border);
        background: var(--bg-panel);
        border-radius: 3px;
        padding: 12px 14px;
        margin-bottom: 10px;
    }

    .rt-chat-scroll::-webkit-scrollbar {
        width: 6px;
    }

    .rt-chat-scroll::-webkit-scrollbar-thumb {
        background: var(--border-active);
        border-radius: 3px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SMALL RENDER HELPERS
# ============================================================
#
# IMPORTANT: Streamlit's markdown renderer treats any line indented
# 4+ spaces as a fenced code block, which silently breaks raw HTML
# that was written with pretty indentation inside an f-string. Every
# HTML fragment below goes through render_html(), which strips
# leading whitespace from each line before handing it to
# st.markdown(..., unsafe_allow_html=True) — this guarantees the HTML
# is always parsed as HTML, never as a code block, no matter how the
# source is indented.

def render_html(html: str):
    cleaned = "\n".join(line.lstrip() for line in html.strip("\n").splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)


def stat_card(col, label, value):
    with col:
        render_html(
            f"""
            <div class="rt-stat">
                <div class="rt-stat-label">{label}</div>
                <div class="rt-stat-value">{value}</div>
            </div>
            """
        )


def eyebrow(text):
    render_html(f'<div class="rt-eyebrow">{text}</div>')


# ------------------------------------------------------------------
# Fleet — live data
#
# graph/workflow.py creates `fleet = DroneFleet()` once, at import
# time, as a module-level singleton — every node (fleet_agent,
# drone_executor) operates on that exact same object via closure.
# That means `fleet.get_fleet_status()` always reflects the real,
# current battery/status/position of every drone (D1, D2, D3), not
# just the one assigned to the active mission. This is a read-only
# call into existing backend state — no backend files are modified.
#
# Real MockDrone statuses (simulator/drone.py): "available", "flying",
# "returning", "landed", "busy". The card border is highlighted based
# on whether a drone is the one currently assigned to the mission,
# not on its raw status word — a drone can be "flying" without being
# the assigned one only in theory, but this keeps the highlight tied
# to what the operator actually cares about.
# ------------------------------------------------------------------

def get_fleet(state):
    assigned = state.get("assigned_drone")
    telemetry = fleet.get_fleet_status()

    rows = []
    for drone in telemetry:
        rows.append(
            {
                "id": drone.get("drone_id", "UNKNOWN"),
                "status": drone.get("status", "available"),
                "battery": drone.get("battery"),
                "location": drone.get("position", "base"),
                "assigned": drone.get("drone_id") == assigned,
            }
        )

    return rows


_FLEET_STATUS_STYLES = {
    "flying": ("IN FLIGHT", "var(--green)", "var(--green-dim)"),
    "returning": ("RETURNING", "var(--amber)", "var(--amber-dim)"),
    "landed": ("LANDED", "var(--amber)", "var(--amber-dim)"),
    "available": ("AVAILABLE", "var(--cyan)", "var(--cyan-dim)"),
    "busy": ("BUSY", "var(--red)", "var(--red-dim)"),
    "charging": ("CHARGING", "var(--amber)", "var(--amber-dim)"),
}

# Friendly callsigns for display only — backend drone IDs (D1/D2/D3)
# stay exactly as-is everywhere in the agents/graph, so nothing about
# fleet selection, safety checks, or memory records changes.
DRONE_CALLSIGNS = {
    "D1": "Falcon",
    "D2": "Raven",
    "D3": "Kestrel",
}


def drone_display_name(drone_id):
    callsign = DRONE_CALLSIGNS.get(drone_id)
    return f"{callsign} · {drone_id}" if callsign else drone_id


def render_fleet(state):
    fleet_rows = get_fleet(state)

    if not fleet_rows:
        return

    cols = st.columns(len(fleet_rows))

    for col, drone in zip(cols, fleet_rows):
        with col:
            status = str(drone.get("status", "available")).lower()
            label, color, bg = _FLEET_STATUS_STYLES.get(status, _FLEET_STATUS_STYLES["available"])
            is_assigned = bool(drone.get("assigned"))

            battery = drone.get("battery")
            battery = 0 if battery is None else max(0, min(100, battery))

            if battery >= 60:
                batt_color = "var(--green)"
            elif battery >= 30:
                batt_color = "var(--amber)"
            else:
                batt_color = "var(--red)"

            dot = (
                '<span class="dot dot-pulse" style="background: var(--green); margin-right:2px;"></span>'
                if is_assigned
                else ""
            )

            display_name = drone_display_name(drone.get("id", "UNKNOWN"))

            render_html(
                f"""
                <div class="rt-fleet-card {'fleet-active' if is_assigned else ''}">
                    <div>
                        <div class="rt-fleet-top">
                            <div class="rt-fleet-name">{display_name}</div>
                            <div class="rt-fleet-badge" style="color: {color}; background: {bg}; border: 1px solid {color};">{dot}{label}</div>
                        </div>
                        <div class="rt-fleet-meta">📍 {drone.get('location', 'base')}</div>
                    </div>
                    <div class="rt-fleet-battery-row">
                        <div class="rt-fleet-battery-track">
                            <div class="rt-fleet-battery-fill" style="width: {battery}%; background: {batt_color};"></div>
                        </div>
                        <div class="rt-fleet-battery-pct">{battery}%</div>
                    </div>
                </div>
                """
            )

            # Only offer charging while the drone is at base, not
            # mid-mission (busy/flying/returning don't get a button).
            can_charge = (
                status not in ("flying", "returning", "busy")
                and drone.get("location", "base") == "base"
                and (battery < 100 or status == "charging")
            )

            if can_charge:
                is_charging = status == "charging"

                if st.button(
                    "⚡ Stop Charging" if is_charging else "⚡ Charge",
                    key=f"charge_{drone.get('id')}",
                    use_container_width=True,
                ):
                    target = fleet.get_drone(drone.get("id"))
                    if target:
                        if is_charging:
                            target.stop_charging()
                        else:
                            target.start_charging()
                    st.rerun()


INSPECTION_ZONES = [
    ("🚧", "North Gate", "north_gate"),
    ("🌾", "Ground Area", "ground_area"),
    ("🚪", "Main Gate", "main_gate"),
    ("🏭", "Warehouse", "warehouse"),
]


def render_inspection_zones(current_location=None):
    cards = "".join(
        f"""
        <div class="rt-zone-card {'zone-active' if slug == current_location else ''}">
            <div class="rt-zone-icon">{icon}</div>
            <div class="rt-zone-label">{label}</div>
        </div>
        """
        for icon, label, slug in INSPECTION_ZONES
    )
    render_html(f'<div class="rt-zone-grid">{cards}</div>')


def recall_stuck_drones():
    """
    Force-recalls every drone in the fleet that isn't in a safe
    at-rest state ("flying" or "returning"), regardless of which
    browser session/tab last assigned it.

    Why this scans the whole fleet instead of just the current
    session's tracked drone: `fleet` (imported from graph.workflow)
    is a single process-wide object shared by every browser session,
    but `st.session_state.mission_state` is per-session. If a tab was
    refreshed or closed mid-mission, or the app hit an unhandled
    error before this fix existed, that session's memory of which
    drone it assigned is gone — but the drone itself is still sitting
    there "flying" forever, because nothing is left to tell it to
    come home. Sweeping the whole fleet fixes that regardless of how
    it got stuck.
    """
    for telemetry in fleet.get_fleet_status():
        if telemetry.get("status") in ("flying", "returning"):
            drone = fleet.get_drone(telemetry["drone_id"])
            if drone:
                drone.force_recall()


# Every mission timestamp is displayed in this timezone, regardless
# of what timezone the server itself runs in (Streamlit Cloud servers
# are typically UTC, which is what made these times look "wrong").
DISPLAY_TIMEZONE = ZoneInfo("Asia/Kolkata")


def format_mission_label(timestamp_str):
    """Turns a stored timestamp into 'Mission <date> · <time>' in IST."""
    try:
        dt = datetime.fromisoformat(timestamp_str)

        if dt.tzinfo is None:
            # Older records (saved before timestamps were made
            # timezone-aware) and the server's own naive local clock
            # are UTC in practice on this hosting platform — treat a
            # naive timestamp as UTC before converting for display.
            dt = dt.replace(tzinfo=timezone.utc)

        dt_local = dt.astimezone(DISPLAY_TIMEZONE)
        return f"Mission {dt_local.strftime('%b %d, %Y · %I:%M %p')}"
    except (TypeError, ValueError):
        return "Mission"


def render_sidebar_mission_history():
    """
    Recent missions started by THIS browser session only — home
    screen and active mission alike — with a delete button per entry.
    Reads straight from missions.json on every rerun (via
    memory_agent), so a new mission finishing or a delete click shows
    up instantly without any extra wiring. Missions from any other
    session (a different browser/tab/operator using the same deployed
    app) never appear here.
    """
    session_id = st.session_state.session_id
    missions = memory_agent.memory.search_by_session(session_id, limit=10)

    if not missions:
        return

    render_html('<div class="rt-eyebrow" style="margin-top: 22px;">Previous Missions</div>')

    for mission_item in reversed(missions):
        mission_id = mission_item.get("mission_id", "")
        label = format_mission_label(mission_item.get("timestamp", ""))

        with st.expander(label):
            st.write("**Location:**", mission_item.get("location"))
            st.write("**Drone:**", mission_item.get("drone_id"))
            st.write("**Detection:**", mission_item.get("detection"))
            st.write("**Risk:**", mission_item.get("risk_level"))
            st.write("**Confidence:**", mission_item.get("confidence"))
            st.write("**Human Decision:**", mission_item.get("human_decision"))

            if st.button("🗑  Delete", key=f"delete_mission_{mission_id}", use_container_width=True):
                memory_agent.delete_mission(mission_id, session_id=session_id)
                st.rerun()


def alert_panel(title, body, tone="cyan"):
    colors = {
        "cyan": ("var(--cyan)", "var(--cyan-dim)"),
        "amber": ("var(--amber)", "var(--amber-dim)"),
        "red": ("var(--red)", "var(--red-dim)"),
        "green": ("var(--green)", "var(--green-dim)"),
    }
    border, bg = colors.get(tone, colors["cyan"])
    render_html(
        f"""
        <div class="rt-alert" style="border-left-color: {border}; background: {bg}; color: var(--text);">
            <span class="rt-alert-title" style="color: {border};">{title}</span>
            {body}
        </div>
        """
    )


def extract_interrupt(result):
    """
    Pulls the payload passed to interrupt(...) out of a graph.invoke()
    result. Handles both an Interrupt namedtuple/object with a .value
    attribute (the normal LangGraph shape) and a plain dict, so it
    keeps working across LangGraph versions without guessing.
    Returns (interrupt_type, payload_dict) or (None, {}) if there is
    no pending interrupt.
    """
    interrupts = result.get("__interrupt__")

    if not interrupts:
        return None, {}

    first = interrupts[0]
    payload = getattr(first, "value", None)

    if payload is None and isinstance(first, dict):
        payload = first.get("value", first)

    if payload is None:
        payload = first

    if not isinstance(payload, dict):
        payload = {}

    return payload.get("type"), payload


def render_image_chat(image_path):
    """
    "Ask About This Photo" — a small side chatbox next to a captured
    image. Calls VisionAnalyzer.ask_about_image() directly (the same
    module-level vision_analyzer the graph uses), completely outside
    the LangGraph workflow — this is read-only human curiosity, it
    never touches mission state or resumes the graph.
    """
    render_html('<div class="rt-eyebrow" style="margin-top:0;">Ask About This Photo</div>')

    history = st.session_state.image_chat_history.get(image_path, [])

    if history:
        chat_html = "".join(
            f"""
            <div style="margin-bottom:10px;">
                <div style="font-size:11.5px; color: var(--cyan); letter-spacing:0.03em; margin-bottom:3px;">
                    Q: {qa['question']}
                </div>
                <div style="font-size:12.5px; color: var(--text); line-height:1.5;">
                    {qa['answer']}
                </div>
            </div>
            """
            for qa in history
        )
        # Bounded + independently scrollable, so a long Q&A history
        # never pushes the input/button below the image column — it
        # scrolls within its own box instead of growing the page.
        render_html(f'<div class="rt-chat-scroll">{chat_html}</div>')

    # A stable, image-specific key so each photo keeps its own input
    # box and doesn't leak text between different captured images.
    widget_key = str(abs(hash(image_path)))

    # Streamlit text_inputs keep whatever the user typed across
    # reruns as long as their key stays the same. To make the box go
    # back to empty right after a question is asked, the key includes
    # a per-image counter that bumps on every submit — Streamlit then
    # treats it as a brand-new (empty) widget on the next render.
    counter_key = f"chat_counter_{widget_key}"
    if counter_key not in st.session_state:
        st.session_state[counter_key] = 0

    input_key = f"image_question_{widget_key}_{st.session_state[counter_key]}"

    def _submit_question():
        q = st.session_state.get(input_key, "").strip()
        if not q:
            return
        answer = vision_analyzer.ask_about_image(image_path, q)
        st.session_state.image_chat_history.setdefault(image_path, []).append(
            {"question": q, "answer": answer}
        )
        st.session_state[counter_key] += 1

    # on_change fires when the user presses Enter (or clicks away)
    # inside the text input, so Enter submits the question the same
    # way the button does.
    st.text_input(
        "Ask a question about this image",
        key=input_key,
        placeholder="e.g. What color is the vehicle? (press Enter to ask)",
        label_visibility="collapsed",
        on_change=_submit_question,
    )

    if st.button(
        "Ask",
        key=f"ask_button_{widget_key}_{st.session_state[counter_key]}",
        use_container_width=True,
    ):
        with st.spinner("Analyzing..."):
            _submit_question()
        st.rerun()


# ============================================================
# SESSION STATE
# ============================================================

if "mission_started" not in st.session_state:
    st.session_state.mission_started = False

if "mission_complete" not in st.session_state:
    st.session_state.mission_complete = False

if "mission_state" not in st.session_state:
    st.session_state.mission_state = {}

if "thread_id" not in st.session_state:
    st.session_state.thread_id = "aerosentinel-ui"

# A stable identifier for this browser session, set once and never
# regenerated (unlike thread_id, which changes every mission). Every
# mission this session starts is tagged with it, and the sidebar
# history / delete button only ever operate on missions carrying this
# exact session_id — so one operator's browser tab never sees or can
# delete another operator's missions on the same deployed app.
if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex

# Which HITL checkpoint (if any) is currently paused, and the payload
# the interrupting node passed to interrupt(). None when no checkpoint
# is pending.
#   "launch_approval_required"  -> before the drone flies
#   "photo_review_required"     -> after every capture (recapture/return)
if "interrupt_type" not in st.session_state:
    st.session_state.interrupt_type = None

if "interrupt_payload" not in st.session_state:
    st.session_state.interrupt_payload = {}

# Per-image Q&A history for the "Ask About This Photo" chatbox.
# Keyed by image_path so each captured photo keeps its own thread.
if "image_chat_history" not in st.session_state:
    st.session_state.image_chat_history = {}


# ============================================================
# HEADER
# ============================================================

if st.session_state.interrupt_type == "launch_approval_required":
    pill_html = '<div class="rt-status-pill tone-amber"><span class="dot dot-pulse" style="background: var(--amber);"></span>AWAITING LAUNCH APPROVAL</div>'
elif st.session_state.interrupt_type == "photo_review_required":
    pill_html = '<div class="rt-status-pill tone-amber"><span class="dot dot-pulse" style="background: var(--amber);"></span>AWAITING PHOTO REVIEW</div>'
elif st.session_state.mission_complete:
    pill_html = '<div class="rt-status-pill tone-green"><span class="dot" style="background: var(--green);"></span>MISSION COMPLETE</div>'
elif st.session_state.mission_started:
    pill_html = '<div class="rt-status-pill tone-cyan"><span class="dot dot-pulse" style="background: var(--cyan);"></span>MISSION ACTIVE</div>'
else:
    pill_html = '<div class="rt-status-pill tone-dim"><span class="dot" style="background: var(--text-dim);"></span>STANDBY</div>'

render_html(
    f"""
    <div class="rt-header">
        <div>
            <div class="rt-title">🛰️ AEROSENTINEL</div>
            <div class="rt-subtitle">AGENTIC DRONE SECURITY &amp; AUTONOMOUS MISSION SYSTEM</div>
        </div>
        {pill_html}
    </div>
    """
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("Mission Control")

    mission = st.text_area(
        "Mission Request",
        value="",
        placeholder="Inspect the ground area for intrusions",
        height=100,
    )

    start_button = st.button("▶  Start Mission", use_container_width=True)

    reset_button = st.button("↺  Reset", use_container_width=True)

    render_html(
        f"""
        <div style="margin-top: 22px; padding-top: 16px; border-top: 1px solid var(--border);
                    font-size: 11px; color: var(--text-dim); letter-spacing: 0.05em;">
            THREAD&nbsp;&nbsp;<span style="color: var(--text);">{st.session_state.thread_id}</span>
        </div>
        """
    )

    render_sidebar_mission_history()


# ============================================================
# RESET
# ============================================================

if reset_button:
    # Recall any drone stuck away from base — see recall_stuck_drones()
    # for why this sweeps the whole fleet instead of only the drone
    # this session happens to remember assigning.
    recall_stuck_drones()

    st.session_state.mission_started = False
    st.session_state.mission_complete = False
    st.session_state.mission_state = {}
    st.session_state.interrupt_type = None
    st.session_state.interrupt_payload = {}
    st.session_state.image_chat_history = {}
    st.session_state.thread_id = f"aerosentinel-{uuid.uuid4().hex}"
    st.rerun()


# ============================================================
# START MISSION
# ============================================================

if start_button and not mission.strip():
    st.sidebar.warning("Enter a mission request before starting.")

if start_button and mission.strip():
    # Same fleet-wide sweep as Reset — starting a fresh mission while
    # any drone is stuck mid-flight (from this session or an
    # abandoned one) should clean that up too.
    recall_stuck_drones()

    st.session_state.mission_started = True
    st.session_state.mission_complete = False
    st.session_state.interrupt_type = None
    st.session_state.interrupt_payload = {}
    st.session_state.image_chat_history = {}
    st.session_state.mission_state = {}
    st.session_state.thread_id = f"aerosentinel-{uuid.uuid4().hex}"

    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    initial_state = {
        "user_request": mission,
        "session_id": st.session_state.session_id,
    }

    try:
        with st.spinner("Agents are executing the mission..."):
            result = graph.invoke(initial_state, config=config)
    except Exception as e:
        st.session_state.mission_started = False
        st.error(f"Could not start the mission: {e}")
        st.stop()

    st.session_state.mission_state = result

    interrupt_type, interrupt_payload = extract_interrupt(result)

    if interrupt_type:
        st.session_state.interrupt_type = interrupt_type
        st.session_state.interrupt_payload = interrupt_payload
    else:
        st.session_state.mission_complete = True

    st.rerun()


# ============================================================
# GET CURRENT STATE
# ============================================================

state = st.session_state.mission_state


# ============================================================
# NO MISSION — IDLE STATE
# ============================================================

if not st.session_state.mission_started:

    render_html(
        """
        <div class="rt-panel" style="margin-top: 20px;">
            <div style="font-family: 'Chakra Petch', sans-serif; font-weight: 700;
                        font-size: 14px; letter-spacing: 0.08em; color: var(--cyan);
                        text-transform: uppercase; margin-bottom: 10px;">
                No Active Mission
            </div>
            <div style="color: var(--text-dim); font-size: 13px; line-height: 1.6;">
                Enter a mission in the <strong style="color: var(--text);">Mission Control</strong>
                panel and press <strong style="color: var(--cyan);">Start Mission</strong>
                to deploy the agent pipeline.
            </div>
        </div>
        """
    )

    eyebrow("Inspection Zones")

    render_inspection_zones()

    eyebrow("Fleet Status")

    render_fleet(state)

    eyebrow("System Architecture")

    render_html(
        '<div class="rt-flow">NATURAL LANGUAGE → PLAN + DRONE SELECT → LAUNCH APPROVAL → FLIGHT + VLM → PHOTO REVIEW</div>'
    )

    arch_rows = [
        ("🧠", "Commander", "Understands the mission"),
        ("📚", "RAG Agent", "Retrieves operational SOPs"),
        ("🧭", "Memory Agent", "Retrieves previous mission history"),
        ("🚁", "Fleet Agent", "Selects the best drone"),
        ("🛡️", "Safety Agent", "Performs pre-flight checks"),
        ("🚀", "Launch Approval", "Human approves the flight before takeoff"),
        ("🎯", "Drone Executor", "Executes simulated mission"),
        ("👁️", "VLM Agent", "Analyzes captured aerial imagery"),
        ("⚠️", "Photo Review", "Human chooses: recapture or return home"),
        ("💾", "Memory Store", "Stores mission outcome"),
    ]

    rows_html = "".join(
        f"""
        <div style="display:flex; align-items:center; gap:14px; padding:10px 4px;
                    border-bottom:1px solid var(--border);">
            <div style="font-size:16px; width:26px; text-align:center;">{icon}</div>
            <div style="font-family:'Chakra Petch', sans-serif; font-weight:600; font-size:12.5px;
                        letter-spacing:0.05em; text-transform:uppercase; width:170px; color: var(--text);">{name}</div>
            <div style="font-size:12.5px; color: var(--text-dim);">{desc}</div>
        </div>
        """
        for icon, name, desc in arch_rows
    )

    render_html(f'<div class="rt-panel">{rows_html}</div>')

    st.stop()


# ============================================================
# MISSION OVERVIEW
# ============================================================

eyebrow("Mission Overview")

col1, col2, col3 = st.columns(3)

stat_card(col1, "Mission Type", state.get("mission_type", "Processing…"))
stat_card(col2, "Location", state.get("location", "Processing…"))
stat_card(col3, "Priority", state.get("priority", "Processing…"))

render_html("<div style='height: 12px;'></div>")

render_inspection_zones(current_location=state.get("location"))


# ============================================================
# AGENT PIPELINE
# ============================================================

eyebrow("Agent Pipeline")

pipeline = [
    ("🧠", "Commander", bool(state.get("mission_type"))),
    ("📚", "RAG Agent", bool(state.get("rag_context"))),
    ("🧭", "Memory Agent", bool(state.get("mission_history") is not None)),
    ("🚁", "Fleet Agent", bool(state.get("assigned_drone"))),
    # safety_status can also be set by Fleet Agent itself (when no
    # drone is available, it skips Safety Agent entirely) — only
    # count this as "Safety Agent ran" when a drone was actually
    # assigned first, since that's the only path that reaches it.
    ("🛡️", "Safety Agent", bool(state.get("assigned_drone")) and bool(state.get("safety_status"))),
    ("🚀", "Launch Approval", bool(state.get("launch_decision"))),
    ("🎯", "Drone Executor", bool(state.get("image_path"))),
    ("👁️", "VLM Agent", bool(state.get("vision_result"))),
    ("⚠️", "Photo Review", bool(state.get("human_decision"))),
]

nodes_html = "".join(
    f"""
    <div class="rt-node {'node-on' if completed else ''}">
        <div class="rt-node-icon">{icon}</div>
        <div class="rt-node-label">{name}</div>
    </div>
    """
    for icon, name, completed in pipeline
)

render_html(f'<div class="rt-chain">{nodes_html}</div>')


# ============================================================
# DRONE STATUS
# ============================================================

eyebrow("Drone Mission")

drone_col1, drone_col2, drone_col3 = st.columns(3)

stat_card(drone_col1, "Assigned Drone", state.get("assigned_drone", "N/A"))

battery = state.get("drone_battery")
stat_card(drone_col2, "Battery", f"{battery}%" if battery is not None else "N/A")

stat_card(drone_col3, "Safety", state.get("safety_status", "N/A"))

render_html("<div style='height: 16px;'></div>")

eyebrow("Fleet Status")

render_fleet(state)


# ============================================================
# RAG KNOWLEDGE
# ============================================================

rag_context = state.get("rag_context", [])

if rag_context:

    eyebrow("Retrieved SOP Knowledge")

    for result in rag_context:
        with st.expander(f"📄  {result.get('source', 'Unknown Source')}"):
            st.write(result.get("content", ""))


# ============================================================
# CAPTURED IMAGE
# ============================================================

image_path = state.get("image_path")

if image_path:

    eyebrow("Captured Aerial Image")

    image_col1, image_col2 = st.columns([2, 1])

    with image_col1:
        try:
            st.image(
                image_path,
                caption=f"Captured at {state.get('location', 'unknown')}",
                use_container_width=True,
            )
        except Exception as e:
            alert_panel("Display Error", f"Unable to display image: {e}", tone="red")

    with image_col2:
        render_image_chat(image_path)


# ============================================================
# VLM RESULTS
# ============================================================

vision = state.get("vision_result")

if vision:

    eyebrow("VLM Analysis")

    v1, v2, v3, v4 = st.columns(4)

    stat_card(v1, "Person", "YES" if vision.get("person_detected") else "NO")
    stat_card(v2, "Vehicle", "YES" if vision.get("vehicle_detected") else "NO")
    stat_card(v3, "Risk", str(vision.get("risk_level", "UNKNOWN")).upper())

    confidence = vision.get("confidence", 0)
    conf_display = f"{confidence * 100:.0f}%" if isinstance(confidence, (int, float)) else confidence
    stat_card(v4, "Confidence", conf_display)

    render_html("<div style='height: 14px;'></div>")

    alert_panel(
        "Detection",
        vision.get("description", "No description available."),
        tone="cyan",
    )


# ============================================================
# HUMAN-IN-THE-LOOP CHECKPOINTS
# ============================================================

def resume_graph(decision, reason):
    """
    Resumes the paused graph with the operator's decision, then
    figures out whether a new checkpoint came up (e.g. photo_review
    looping back to itself after a recapture) or the mission is done.
    """
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    try:
        with st.spinner("Processing decision..."):
            result = graph.invoke(
                Command(resume={"decision": decision, "reason": reason}),
                config=config,
            )
    except Exception:
        # The checkpoint for this mission is gone — almost always
        # because the app process restarted (Streamlit Cloud can do
        # this at any time) between the launch/photo-review pause and
        # this click. There's no state left to resume, so recover
        # cleanly instead of showing a raw traceback: recall whatever
        # drone this session thought was flying, then hand back a
        # clear explanation and force a fresh start.
        in_progress_drone_id = st.session_state.mission_state.get("assigned_drone")
        if in_progress_drone_id:
            drone_to_recall = fleet.get_drone(in_progress_drone_id)
            if drone_to_recall:
                drone_to_recall.force_recall()

        st.session_state.mission_started = False
        st.session_state.mission_complete = False
        st.session_state.mission_state = {}
        st.session_state.interrupt_type = None
        st.session_state.interrupt_payload = {}
        st.session_state.image_chat_history = {}
        st.session_state.thread_id = f"aerosentinel-{uuid.uuid4().hex}"

        st.error(
            "This mission's paused session could not be found — the app "
            "likely restarted while it was waiting for your decision. "
            "The drone has been recalled. Please start a new mission."
        )
        st.stop()

    st.session_state.mission_state = result

    interrupt_type, interrupt_payload = extract_interrupt(result)

    if interrupt_type:
        st.session_state.interrupt_type = interrupt_type
        st.session_state.interrupt_payload = interrupt_payload
    else:
        st.session_state.interrupt_type = None
        st.session_state.interrupt_payload = {}
        st.session_state.mission_complete = True

    st.rerun()


# ---------- Checkpoint 1: Launch Approval (before takeoff) ----------

if st.session_state.interrupt_type == "launch_approval_required":

    payload = st.session_state.interrupt_payload

    eyebrow("Launch Approval Required")

    alert_panel(
        "Action Needed",
        payload.get(
            "message",
            "A drone has been selected and cleared pre-flight checks. "
            "Approve launch to begin the mission.",
        ),
        tone="amber",
    )

    render_html("<div style='height: 10px;'></div>")

    lc1, lc2, lc3 = st.columns(3)
    stat_card(lc1, "Drone", payload.get("assigned_drone", "N/A"))
    battery = payload.get("drone_battery")
    stat_card(lc2, "Battery", f"{battery}%" if battery is not None else "N/A")
    stat_card(lc3, "Location", payload.get("location", "N/A"))

    render_html("<div style='height: 10px;'></div>")

    launch_col1, launch_col2 = st.columns(2)

    with launch_col1:
        approve_launch = st.button("✅  APPROVE LAUNCH", use_container_width=True)

    with launch_col2:
        reject_launch = st.button("❌  KEEP GROUNDED", use_container_width=True)

    if approve_launch:
        resume_graph("approve", "Launch approved by operator.")

    if reject_launch:
        resume_graph("reject", "Launch withheld by operator.")


# ---------- Checkpoint 2: Photo Review (after every capture) ----------

if st.session_state.interrupt_type == "photo_review_required":

    payload = st.session_state.interrupt_payload

    eyebrow("Photo Review Required")

    alert_panel(
        "Action Needed",
        payload.get(
            "message",
            "Imagery captured and analyzed. Choose the next action.",
        ),
        tone="amber",
    )

    render_html("<div style='height: 10px;'></div>")

    recapture_count = payload.get("recapture_count", 0)
    total_photos = payload.get("total_photos", 1)
    photos_taken_so_far = recapture_count + 1

    render_html(
        f"""
        <div style="font-size: 11px; color: var(--text-dim); letter-spacing: 0.05em; margin: 10px 0;">
            Viewing photo {photos_taken_so_far} of {total_photos} at this location
            &nbsp;•&nbsp; Photos remaining: {max(0, total_photos - photos_taken_so_far)}
        </div>
        """
    )

    review_col1, review_col2 = st.columns(2)

    recapture_disabled = photos_taken_so_far >= total_photos

    with review_col1:
        take_more = st.button(
            "📷  TAKE MORE PHOTOS",
            use_container_width=True,
            disabled=recapture_disabled,
            help="No more photos available at this location." if recapture_disabled else None,
        )

    with review_col2:
        return_home = st.button("🏠  RETURN HOME", use_container_width=True)

    if take_more:
        resume_graph("recapture", "Requested another photo.")

    if return_home:
        resume_graph("return", "Returning drone home.")


# ============================================================
# FINAL REPORT
# ============================================================

if st.session_state.mission_complete:

    eyebrow("Final Mission Report")

    final_report = state.get("final_report")

    if final_report:

        if "INCIDENT CONFIRMED" in final_report:
            alert_panel("Incident Confirmed", final_report, tone="green")
        elif "MISSION COMPLETE" in final_report:
            alert_panel("Mission Complete", final_report, tone="cyan")
        elif "MISSION NOT LAUNCHED" in final_report:
            alert_panel("Mission Not Launched", final_report, tone="amber")
        elif "MISSION REJECTED" in final_report:
            alert_panel("Mission Rejected", final_report, tone="red")
        else:
            alert_panel("Mission Report", final_report, tone="red")


# ============================================================
# FOOTER
# ============================================================

render_html("<div style='height: 30px;'></div>")
render_html('<hr style="margin: 0 0 14px 0;">')

render_html(
    """
    <div style="font-size: 11px; color: var(--text-dim); letter-spacing: 0.08em;
                text-transform: uppercase; text-align: center;">
        AeroSentinel · Agentic AI Drone Security Prototype · Simulated Drone Environment
    </div>
    """
)