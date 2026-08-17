from simulator.fleet import DroneFleet


class DroneExecutor:

    def __init__(self, fleet: DroneFleet):
        self.fleet = fleet

    def execute_mission(
        self,
        drone_id: str,
        location: str,
    ):

        drone = self.fleet.get_drone(drone_id)

        if not drone:
            return {
                "success": False,
                "message": f"Drone {drone_id} not found."
            }

        # Takeoff
        takeoff_result = drone.takeoff(10)

        if not takeoff_result["success"]:
            return takeoff_result

        # Navigation
        navigation_result = drone.goto(location)

        if not navigation_result["success"]:
            return navigation_result

        # Capture the first photo (index 0) at this location
        image_result = drone.capture_image(location, index=0)

        if not image_result["success"]:
            return image_result

        return {
            "success": True,
            "drone_id": drone_id,
            "image_path": image_result["image_path"],
            "photo_index": image_result.get("photo_index", 0),
            "total_photos": image_result.get("total_photos", 1),
            "message": (
                f"{drone_id} reached {location} "
                "and captured an image."
            ),
        }

    def return_home(self, drone_id: str):

        drone = self.fleet.get_drone(drone_id)

        if not drone:
            return {
                "success": False,
                "message": f"Drone {drone_id} not found."
            }

        result = drone.return_home()

        drone.land()

        return result