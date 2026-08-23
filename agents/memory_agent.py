import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class MissionMemory:

    def __init__(
        self,
        file_path: str = "memory/missions.json"
    ):

        self.file_path = Path(file_path)

        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not self.file_path.exists():

            self.file_path.write_text(
                "[]",
                encoding="utf-8"
            )

    # ========================================================
    # LOAD
    # ========================================================

    def _load(self):

        try:

            return json.loads(
                self.file_path.read_text(
                    encoding="utf-8"
                )
            )

        except (
            json.JSONDecodeError,
            FileNotFoundError
        ):

            return []

    # ========================================================
    # SAVE
    # ========================================================

    def _save(self, missions):

        self.file_path.write_text(
            json.dumps(
                missions,
                indent=4
            ),
            encoding="utf-8"
        )

    # ========================================================
    # RECORD MISSION
    # ========================================================

    def record_mission(
        self,
        drone_id: str,
        location: str,
        mission_type: str,
        detection: str,
        confidence: float,
        risk_level: str,
        human_decision: str,
        human_reason: str,
        outcome: str,
        session_id: str | None = None,
    ):

        missions = self._load()

        mission = {

            "mission_id": str(
                uuid4()
            ),

            # Stored explicitly in UTC (timezone-aware) rather than
            # naive datetime.now() — a naive timestamp is ambiguous
            # about which timezone it's actually in, which is exactly
            # what made these times "wrong" for display. UTC is
            # converted to the operator's local timezone at display
            # time instead (see format_mission_label() in app.py).
            "timestamp": datetime.now(timezone.utc).isoformat(),

            # Which browser session created this mission — everything
            # session-scoped (the sidebar history list, delete) reads
            # this field so one operator never sees another's data.
            # None for records saved before this field existed.
            "session_id": session_id,

            "drone_id": drone_id,

            "location": location,

            "mission_type": mission_type,

            "detection": detection,

            "confidence": confidence,

            "risk_level": risk_level,

            "human_decision": human_decision,

            "human_reason": human_reason,

            "outcome": outcome,
        }

        missions.append(
            mission
        )

        self._save(
            missions
        )

        return mission

    # ========================================================
    # DELETE MISSION
    # ========================================================

    def delete_mission(
        self,
        mission_id: str,
        session_id: str | None = None,
    ) -> bool:
        """
        Removes a single mission record by its mission_id. If
        session_id is given, only deletes the record when it also
        belongs to that session — so one session can't delete another
        session's mission even if it somehow knew the mission_id.
        Returns True if a record was found and removed, False
        otherwise.
        """
        missions = self._load()

        def _keep(mission):
            if mission.get("mission_id") != mission_id:
                return True
            if session_id is not None and mission.get("session_id") != session_id:
                return True
            return False

        filtered = [
            mission
            for mission in missions
            if _keep(mission)
        ]

        if len(filtered) == len(missions):
            return False

        self._save(filtered)

        return True

    # ========================================================
    # GET ALL MISSIONS
    # ========================================================

    def get_all_missions(self):

        return self._load()

    # ========================================================
    # SEARCH BY LOCATION
    # ========================================================

    def search_by_location(
        self,
        location: str,
        limit: int = 5
    ):

        missions = self._load()

        matching = [
            mission
            for mission in missions
            if mission.get("location") == location
        ]

        return matching[-limit:]

    # ========================================================
    # SEARCH BY DRONE
    # ========================================================

    def search_by_drone(
        self,
        drone_id: str,
        limit: int = 5
    ):

        missions = self._load()

        matching = [
            mission
            for mission in missions
            if mission.get("drone_id") == drone_id
        ]

        return matching[-limit:]

    # ========================================================
    # SEARCH BY SESSION
    # ========================================================

    def search_by_session(
        self,
        session_id: str,
        limit: int = 10,
    ):
        """All missions started by one browser session, most recent
        last (matching get_recent's ordering)."""

        missions = self._load()

        matching = [
            mission
            for mission in missions
            if mission.get("session_id") == session_id
        ]

        return matching[-limit:]

    def search_by_session_and_location(
        self,
        session_id: str,
        location: str,
        limit: int = 5,
    ):
        """
        Used by the memory agent when grounding a new mission — prior
        history at this location, scoped to the operator's own
        session only.
        """

        missions = self._load()

        matching = [
            mission
            for mission in missions
            if mission.get("session_id") == session_id
            and mission.get("location") == location
        ]

        return matching[-limit:]

    # ========================================================
    # RECENT MISSIONS
    # ========================================================

    def get_recent(
        self,
        limit: int = 5
    ):

        missions = self._load()

        return missions[-limit:]