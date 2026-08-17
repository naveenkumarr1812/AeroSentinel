import json
from datetime import datetime
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
    ):

        missions = self._load()

        mission = {

            "mission_id": str(
                uuid4()
            ),

            "timestamp": datetime.now().isoformat(),

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
    # RECENT MISSIONS
    # ========================================================

    def get_recent(
        self,
        limit: int = 5
    ):

        missions = self._load()

        return missions[-limit:]