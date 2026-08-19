from simulator.fleet import DroneFleet


# Friendly callsigns for the failure message only — selection logic
# still works purely off drone_id, nothing here affects which drone
# gets picked.
DRONE_CALLSIGNS = {
    "D1": "Falcon",
    "D2": "Raven",
    "D3": "Kestrel",
}

_STATUS_DESCRIPTIONS = {
    "charging": "is charging",
    "busy": "is busy in another mission or servicing",
    "flying": "is currently flying another mission",
    "returning": "is returning from a mission",
    "landed": "has landed but needs charging before it can fly again",
}


class FleetAgent:

    def __init__(self, fleet: DroneFleet):
        self.fleet = fleet

    def select_drone(self):

        available = self.fleet.get_available_drones()

        if not available:

            statuses = []

            for drone in self.fleet.get_fleet_status():
                name = DRONE_CALLSIGNS.get(drone["drone_id"], drone["drone_id"])
                description = _STATUS_DESCRIPTIONS.get(
                    drone["status"],
                    f"is {drone['status']}",
                )
                statuses.append(f"{name} · {drone['drone_id']} {description}")

            detail = ", ".join(statuses)

            return {
                "success": False,
                "message": (
                    f"No drones are currently available. ({detail})"
                )
            }

        # Select available drone with highest battery
        selected = max(
            available,
            key=lambda drone: drone.battery
        )

        return {
            "success": True,
            "drone_id": selected.drone_id,
            "battery": selected.battery,
            "message": (
                f"Selected {selected.drone_id} "
                f"with {selected.battery}% battery."
            ),
        }