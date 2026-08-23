import json
from pathlib import Path

from simulator.drone import MockDrone


# Where fleet state (battery, status, position, in-progress charging)
# is persisted between runs. Written to disk after every state change
# so a process restart (Streamlit Cloud idle sleep/wake, a redeploy,
# a crash) restores drones to where they actually were instead of
# resetting everyone back to these hardcoded starting numbers.
_STATE_FILE = Path("simulator") / "fleet_state.json"

_DEFAULTS = {
    "D1": {"battery": 32, "position": "base", "status": "available"},
    "D2": {"battery": 87, "position": "base", "status": "available"},
    "D3": {"battery": 65, "position": "base", "status": "busy"},
}


class DroneFleet:

    def __init__(self):
        saved = self._load_state()

        self.drones = {}

        for drone_id, defaults in _DEFAULTS.items():
            data = saved.get(drone_id) if saved else None
            data = data or defaults

            self.drones[drone_id] = MockDrone(
                drone_id=drone_id,
                battery=data.get("battery", defaults["battery"]),
                position=data.get("position", defaults["position"]),
                status=data.get("status", defaults["status"]),
                charging_since=data.get("charging_since"),
                charge_start_battery=data.get("charge_start_battery"),
                on_change=self.save_state,
            )

    # ========================================================
    # PERSISTENCE
    # ========================================================

    def _load_state(self):
        if not _STATE_FILE.exists():
            return None

        try:
            return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def save_state(self):
        data = {
            drone_id: {
                "battery": drone.battery,
                "position": drone.position,
                "status": drone.status,
                "charging_since": drone._charging_since,
                "charge_start_battery": drone._charge_start_battery,
            }
            for drone_id, drone in self.drones.items()
        }

        try:
            _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            _STATE_FILE.write_text(
                json.dumps(data, indent=2),
                encoding="utf-8",
            )
        except OSError as e:
            print(f"\nFLEET: failed to persist fleet state ({e})")

    # ========================================================
    # QUERIES
    # ========================================================

    def get_drone(self, drone_id: str):
        return self.drones.get(drone_id)

    def get_fleet_status(self):
        return [
            drone.telemetry()
            for drone in self.drones.values()
        ]

    def get_available_drones(self):
        return [
            drone
            for drone in self.drones.values()
            if drone.status == "available"
        ]