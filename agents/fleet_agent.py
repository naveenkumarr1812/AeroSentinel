from simulator.fleet import DroneFleet


class FleetAgent:

    def __init__(self, fleet: DroneFleet):
        self.fleet = fleet

    def select_drone(self):

        available = self.fleet.get_available_drones()

        if not available:
            return {
                "success": False,
                "message": "No drones are currently available."
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