from simulator.drone import MockDrone


class DroneFleet:

    def __init__(self):
        self.drones = {
            "D1": MockDrone(
                drone_id="D1",
                battery=32,
            ),
            "D2": MockDrone(
                drone_id="D2",
                battery=87,
            ),
            "D3": MockDrone(
                drone_id="D3",
                battery=65,
                status="busy",
            ),
        }

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