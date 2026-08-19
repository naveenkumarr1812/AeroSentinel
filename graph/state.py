from typing import Any, TypedDict


class MissionState(TypedDict, total=False):

    # User request
    user_request: str

    # Mission understanding
    mission_type: str
    location: str
    priority: str

    # RAG
    rag_context: list[dict[str, Any]]

    # Memory
    mission_history: list[dict[str, Any]]

    # Drone
    assigned_drone: str
    drone_battery: int

    # Pre-flight safety
    safety_status: str
    safety_reason: str

    # Launch approval (human-in-the-loop BEFORE the drone flies)
    launch_decision: str
    launch_reason: str

    # Camera
    image_path: str

    # How many numbered photos exist at this location's image folder
    # (e.g. images/ground_area/ has 4 -> total_photos = 4)
    total_photos: int

    # 0-based index of the most recently captured photo. Also doubles
    # as "how many recaptures have happened" since the first capture
    # is index 0.
    recapture_count: int

    # True if the most recent recapture attempt itself failed (e.g. an
    # image file went missing mid-mission) — routes straight to a
    # safe return instead of silently re-analyzing a stale photo.
    recapture_failed: bool

    # Vision (most recent capture only)
    vision_result: dict[str, Any]
    incident_detected: bool
    risk_level: str

    # Every capture this mission, in order, each with its own vision
    # result — used to build the multi-photo final summary.
    capture_log: list[dict[str, Any]]

    # Photo review (human-in-the-loop AFTER each capture: recapture / return)
    human_decision: str
    human_reason: str

    # Final result
    final_report: str