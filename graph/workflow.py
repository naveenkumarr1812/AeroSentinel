"""
AeroSentinel — LangGraph workflow

Two human-in-the-loop checkpoints:

  1. LAUNCH APPROVAL — after a drone is selected and cleared by the
     safety agent, but BEFORE it takes off. The operator approves or
     rejects the flight itself.

  2. PHOTO REVIEW — after every captured image is analyzed by the
     VLM. The operator either asks for another photo of the same
     location (walks forward through that location's numbered image
     folder, no re-launch) or sends the drone home, which ends the
     mission and writes a summary covering every photo taken.

Each mission location has a folder of numbered images:
    images/<location>/1.jpg
    images/<location>/2.jpg
    images/<location>/3.jpg
    ...
The first capture uses 1.jpg, each "take more photos" request moves
to the next number. "Take more photos" is automatically disabled once
every numbered photo in that location's folder has been used.

Flow:

    START
      -> commander -> rag -> memory -> fleet -> safety
      -> [safety_router]
           REJECTED -> finish -> END
           APPROVED -> launch_approval  (interrupt)
      -> [launch_router]
           reject -> launch_rejected -> END
           approve -> drone -> vision -> photo_review  (interrupt)
      -> [photo_review_router]
           recapture -> recapture -> vision -> photo_review  (interrupt, loops)
           return     -> return_home -> END

NOTE: emoji-free print statements throughout — the project's own
knowledge base documents a UnicodeEncodeError crash on Windows
consoles caused by emoji prints in the original node functions, so
none are used here.
"""

import sqlite3

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import interrupt

from graph.state import MissionState

from simulator.fleet import DroneFleet

from agents.commander import MissionCommander
from agents.rag_agent import RAGAgent
from agents.memory_agent import MemoryAgent
from agents.fleet_agent import FleetAgent
from agents.safety_agent import SafetyAgent
from agents.drone_executor import DroneExecutor
from agents.vision import VisionAnalyzer


# ============================================================
# SYSTEM COMPONENTS
#
# `fleet` is a module-level singleton — every node below shares the
# exact same DroneFleet instance, so its live telemetry (battery,
# status, position for D1/D2/D3) is always accurate regardless of
# which mission is running.
# ============================================================

fleet = DroneFleet()
commander = MissionCommander()
rag_agent = RAGAgent()
memory_agent = MemoryAgent()
fleet_agent = FleetAgent(fleet)
safety_agent = SafetyAgent()
drone_executor = DroneExecutor(fleet)
vision_analyzer = VisionAnalyzer()


# ============================================================
# NODE: COMMANDER
# ============================================================

def commander_node(state: MissionState):
    result = commander.understand_mission(state["user_request"])

    if result.get("error") or not result.get("location") or not result.get("mission_type"):
        return {
            "safety_status": "REJECTED",
            "safety_reason": (
                "Could not understand the mission request: "
                f"{result.get('error', 'no valid mission type/location returned')}."
            ),
        }

    return {
        "mission_type": result["mission_type"],
        "location": result["location"],
        "priority": result["priority"],
    }


def commander_router(state: MissionState):
    if state.get("mission_type") and state.get("location"):
        return "rag"
    return "finish"


# ============================================================
# NODE: RAG RETRIEVAL
# ============================================================

def rag_node(state: MissionState):
    # A transient embedding/ChromaDB hiccup shouldn't take down the
    # whole mission — the safety agent already handles a missing RAG
    # context gracefully (it just logs a warning and proceeds), so
    # falling back to an empty list here is safe.
    try:
        results = rag_agent.retrieve_mission_knowledge(
            mission=state["mission_type"],
            location=state["location"],
        )
    except Exception as e:
        print(f"\nRAG AGENT: retrieval failed, continuing without SOP context ({e})")
        results = []

    return {"rag_context": results}


# ============================================================
# NODE: MEMORY HISTORY
# ============================================================

def memory_node(state: MissionState):
    try:
        history = memory_agent.retrieve_history(
            location=state["location"],
            session_id=state.get("session_id"),
        )
    except Exception as e:
        print(f"\nMEMORY AGENT: history lookup failed, continuing without it ({e})")
        history = []

    return {"mission_history": history}


# ============================================================
# NODE: FLEET ALLOCATION
# ============================================================

def fleet_node(state: MissionState):
    result = fleet_agent.select_drone()

    if not result["success"]:
        return {
            "safety_status": "REJECTED",
            "safety_reason": result["message"],
        }

    drone = fleet.get_drone(result["drone_id"])

    return {
        "assigned_drone": result["drone_id"],
        "drone_battery": drone.battery,
    }


def fleet_router(state: MissionState):
    if state.get("assigned_drone"):
        return "safety"
    return "finish"


# ============================================================
# NODE: PRE-FLIGHT SAFETY
# ============================================================

def safety_node(state: MissionState):
    drone = fleet.get_drone(state["assigned_drone"])

    result = safety_agent.check_mission(
        battery=drone.battery,
        location=state["location"],
        altitude=10,
        rag_context=state.get("rag_context", []),
    )

    return {
        "safety_status": result["status"],
        "safety_reason": result["reason"],
    }


def safety_router(state: MissionState):
    if state.get("safety_status") == "APPROVED":
        return "launch_approval"
    return "finish"


# ============================================================
# NODE: LAUNCH APPROVAL  (human-in-the-loop #1 — before flight)
# ============================================================

def launch_approval_node(state: MissionState):
    decision = interrupt(
        {
            "type": "launch_approval_required",
            "message": (
                "A drone has been selected and cleared pre-flight "
                "checks. Approve launch to begin the mission."
            ),
            "mission_type": state.get("mission_type"),
            "location": state.get("location"),
            "priority": state.get("priority"),
            "assigned_drone": state.get("assigned_drone"),
            "drone_battery": state.get("drone_battery"),
            "safety_status": state.get("safety_status"),
            "safety_reason": state.get("safety_reason"),
            "rag_context": state.get("rag_context", []),
            "mission_history": state.get("mission_history", []),
        }
    )

    if isinstance(decision, dict):
        launch_decision = decision.get("decision", "reject")
        launch_reason = decision.get("reason", "")
    else:
        launch_decision = str(decision)
        launch_reason = ""

    return {
        "launch_decision": launch_decision,
        "launch_reason": launch_reason,
    }


def launch_router(state: MissionState):
    if state.get("launch_decision") == "approve":
        return "drone"
    return "launch_rejected"


# ============================================================
# NODE: LAUNCH REJECTED
# ============================================================

def launch_rejected_node(state: MissionState):
    report = (
        "\nMISSION NOT LAUNCHED\n\n"
        f"Drone: {state.get('assigned_drone', 'N/A')}\n"
        f"Location: {state.get('location', 'N/A')}\n"
        f"Reason: {state.get('launch_reason') or 'Launch was not approved by the operator.'}\n\n"
        "Action: Drone remained on standby. No flight was executed.\n"
    )

    return {"final_report": report}


# ============================================================
# NODE: DRONE EXECUTOR  (first flight — takeoff, navigate, capture)
# ============================================================

def drone_node(state: MissionState):
    result = drone_executor.execute_mission(
        drone_id=state["assigned_drone"],
        location=state["location"],
    )

    if not result["success"]:
        return {
            "safety_status": "REJECTED",
            "safety_reason": result["message"],
        }

    return {
        "image_path": result["image_path"],
        "total_photos": result.get("total_photos", 1),
    }


def drone_router(state: MissionState):
    if state.get("image_path"):
        return "vision"
    return "finish"


# ============================================================
# NODE: RECAPTURE  (another photo — no re-launch, drone stays flying)
# ============================================================

def recapture_node(state: MissionState):
    drone = fleet.get_drone(state["assigned_drone"])

    if not drone:
        return {"recapture_failed": True}

    next_index = state.get("recapture_count", 0) + 1

    result = drone.capture_image(state["location"], index=next_index)

    if not result["success"]:
        # photo_review_router already checks total_photos before
        # routing here, so this should be rare (e.g. an image file
        # was deleted mid-mission). Rather than silently re-analyzing
        # the previous photo again as if nothing happened, flag it so
        # the router below sends the drone straight home instead.
        return {"recapture_failed": True}

    return {
        "image_path": result["image_path"],
        "recapture_count": next_index,
        "recapture_failed": False,
    }


def recapture_router(state: MissionState):
    if state.get("recapture_failed"):
        return "return_home"
    return "vision"


# ============================================================
# NODE: VISION ANALYZER
# ============================================================

def vision_node(state: MissionState):
    result = vision_analyzer.analyze_image(state["image_path"])

    entry = {
        "photo_index": state.get("recapture_count", 0),
        "image_path": state["image_path"],
        "risk_level": result.get("risk_level", "unknown"),
        "confidence": result.get("confidence"),
        "description": result.get("description", ""),
        "person_detected": result.get("person_detected", False),
        "vehicle_detected": result.get("vehicle_detected", False),
    }

    capture_log = state.get("capture_log", []) + [entry]

    return {
        "vision_result": result,
        "incident_detected": result.get("intrusion_detected", False),
        "risk_level": result.get("risk_level", "unknown"),
        "capture_log": capture_log,
    }


# ============================================================
# NODE: PHOTO REVIEW  (human-in-the-loop #2 — after every capture)
# ============================================================

def photo_review_node(state: MissionState):
    decision = interrupt(
        {
            "type": "photo_review_required",
            "message": (
                "Imagery captured and analyzed. Choose the next action."
            ),
            "drone_id": state.get("assigned_drone"),
            "location": state.get("location"),
            "risk_level": state.get("risk_level", "unknown"),
            "vision_result": state.get("vision_result", {}),
            "recapture_count": state.get("recapture_count", 0),
            "total_photos": state.get("total_photos", 1),
            "capture_log": state.get("capture_log", []),
            "image_path": state.get("image_path"),
        }
    )

    if isinstance(decision, dict):
        human_decision = decision.get("decision", "return")
        human_reason = decision.get("reason", "")
    else:
        human_decision = str(decision)
        human_reason = ""

    return {
        "human_decision": human_decision,
        "human_reason": human_reason,
    }


def photo_review_router(state: MissionState):
    decision = state.get("human_decision")

    if decision == "recapture":
        next_index = state.get("recapture_count", 0) + 1
        total_photos = state.get("total_photos", 1)

        if next_index >= total_photos:
            # No more numbered photos in this location's folder —
            # force a safe return instead of failing the recapture.
            return "return_home"

        return "recapture"

    return "return_home"


# ============================================================
# NODE: RETURN HOME  (final node — mission complete either way)
# ============================================================

def return_home_node(state: MissionState):
    drone_id = state["assigned_drone"]
    capture_log = state.get("capture_log", [])

    # A mission-wide incident flag: true if ANY captured photo showed
    # a medium/high risk detection, not just the last one reviewed.
    any_incident = any(
        entry.get("risk_level") in ("medium", "high")
        for entry in capture_log
    ) or bool(state.get("incident_detected"))

    outcome = "incident_confirmed" if any_incident else "mission_completed"

    last_entry = capture_log[-1] if capture_log else {}

    memory_agent.save_mission(
        drone_id=drone_id,
        location=state["location"],
        mission_type=state.get("mission_type", "unknown"),
        detection=last_entry.get("description", "unknown"),
        confidence=last_entry.get("confidence", 0.0),
        risk_level=last_entry.get("risk_level", "unknown"),
        human_decision=state.get("human_decision", "return"),
        human_reason=state.get("human_reason", ""),
        outcome=outcome,
        session_id=state.get("session_id"),
    )

    drone_executor.return_home(drone_id)

    header = "SECURITY INCIDENT CONFIRMED" if any_incident else "MISSION COMPLETE"

    photo_lines = "\n".join(
        f"  Photo {entry.get('photo_index', i) + 1}: "
        f"risk={entry.get('risk_level', 'unknown')}, "
        f"confidence={entry.get('confidence', 'unknown')} "
        f"- {entry.get('description', '')}"
        for i, entry in enumerate(capture_log)
    )

    report = (
        f"\n{header}\n\n"
        f"Drone: {drone_id}\n"
        f"Location: {state.get('location', 'N/A')}\n"
        f"Photos captured: {len(capture_log)}\n\n"
        f"Photo-by-photo summary:\n{photo_lines}\n\n"
        f"Human Decision: {state.get('human_decision', 'unknown')}\n"
        f"Reason: {state.get('human_reason', '')}\n\n"
        "Action: Mission recorded to memory.\n"
        "Action: Drone returning home.\n"
    )

    return {"final_report": report}


# ============================================================
# NODE: PRE-FLIGHT FAILURE
# ============================================================

def finish_node(state: MissionState):
    report = (
        "\nMISSION REJECTED\n\n"
        f"Reason: {state.get('safety_reason', 'Unknown')}\n"
    )

    return {"final_report": report}


# ============================================================
# BUILD GRAPH
# ============================================================

builder = StateGraph(MissionState)

builder.add_node("commander", commander_node)
builder.add_node("rag", rag_node)
builder.add_node("memory", memory_node)
builder.add_node("fleet", fleet_node)
builder.add_node("safety", safety_node)
builder.add_node("launch_approval", launch_approval_node)
builder.add_node("launch_rejected", launch_rejected_node)
builder.add_node("drone", drone_node)
builder.add_node("recapture", recapture_node)
builder.add_node("vision", vision_node)
builder.add_node("photo_review", photo_review_node)
builder.add_node("return_home", return_home_node)
builder.add_node("finish", finish_node)

builder.add_edge(START, "commander")

builder.add_conditional_edges(
    "commander",
    commander_router,
    {
        "rag": "rag",
        "finish": "finish",
    },
)

builder.add_edge("rag", "memory")
builder.add_edge("memory", "fleet")

builder.add_conditional_edges(
    "fleet",
    fleet_router,
    {
        "safety": "safety",
        "finish": "finish",
    },
)

builder.add_conditional_edges(
    "safety",
    safety_router,
    {
        "launch_approval": "launch_approval",
        "finish": "finish",
    },
)

builder.add_conditional_edges(
    "launch_approval",
    launch_router,
    {
        "drone": "drone",
        "launch_rejected": "launch_rejected",
    },
)

builder.add_conditional_edges(
    "drone",
    drone_router,
    {
        "vision": "vision",
        "finish": "finish",
    },
)

builder.add_conditional_edges(
    "recapture",
    recapture_router,
    {
        "vision": "vision",
        "return_home": "return_home",
    },
)

builder.add_edge("vision", "photo_review")

builder.add_conditional_edges(
    "photo_review",
    photo_review_router,
    {
        "recapture": "recapture",
        "return_home": "return_home",
    },
)

builder.add_edge("launch_rejected", END)
builder.add_edge("return_home", END)
builder.add_edge("finish", END)

# SqliteSaver instead of MemorySaver: an in-memory checkpointer loses
# every paused mission (a launch or photo review still awaiting a
# human decision) the instant the Python process restarts — which
# hosting platforms like Streamlit Community Cloud can do at any
# time (idle recycling, redeploys). Writing checkpoints to a local
# SQLite file survives normal script reruns and process hiccups
# within the same running container. It does NOT survive a full
# redeploy/container rebuild wiping the filesystem — for that, an
# external database-backed checkpointer would be needed — but this
# covers the far more common case that just crashed above.
_conn = sqlite3.connect(
    "aerosentinel_checkpoints.sqlite",
    check_same_thread=False,
)
_checkpointer = SqliteSaver(_conn)

graph = builder.compile(checkpointer=_checkpointer)