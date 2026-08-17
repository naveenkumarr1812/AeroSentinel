from pathlib import Path


# Checked in this order for every numbered photo — png first since
# that's the project's actual format, jpg/jpeg kept as a fallback so
# mixed folders still work.
_SUPPORTED_EXTENSIONS = [".png", ".jpg", ".jpeg"]


def _find_photo(folder: Path, number: int):
    for ext in _SUPPORTED_EXTENSIONS:
        candidate = folder / f"{number}{ext}"
        if candidate.exists():
            return candidate
    return None


class MockDrone:
    def __init__(
        self,
        drone_id: str,
        battery: int,
        position: str = "base",
        status: str = "available",
    ):
        self.drone_id = drone_id
        self.battery = battery
        self.position = position
        self.status = status
        self.altitude = 0

    def takeoff(self, altitude: int = 10):
        if self.status not in ["available", "landed"]:
            return {
                "success": False,
                "message": f"{self.drone_id} is not available for takeoff."
            }

        if self.battery < 20:
            return {
                "success": False,
                "message": f"{self.drone_id} has insufficient battery."
            }

        self.status = "flying"
        self.altitude = altitude
        self.battery -= 2

        return {
            "success": True,
            "message": f"{self.drone_id} took off to {altitude}m.",
            "drone_id": self.drone_id,
            "altitude": self.altitude,
            "battery": self.battery,
        }

    def goto(self, location: str):
        if self.status != "flying":
            return {
                "success": False,
                "message": f"{self.drone_id} must be flying before navigation."
            }

        self.position = location
        self.battery -= 5

        return {
            "success": True,
            "message": f"{self.drone_id} reached {location}.",
            "drone_id": self.drone_id,
            "position": self.position,
            "battery": self.battery,
        }

    def capture_image(self, location: str, index: int = 0):
        """
        Captures the (index+1)-th photo at `location`.

        Expects a folder of sequentially numbered images:
            images/<location>/1.png
            images/<location>/2.png
            images/<location>/3.png
            ...
        (.jpg / .jpeg also work — see _SUPPORTED_EXTENSIONS above.)

        `index` is 0-based (index=0 -> "1.*", index=1 -> "2.*", ...)
        so the very first capture of a mission and every subsequent
        "take more photos" request just walk forward through the
        folder. Also reports how many numbered photos exist in total,
        so the workflow knows when to stop offering recaptures.
        """
        folder = Path("images") / location

        if not folder.exists() or not folder.is_dir():
            return {
                "success": False,
                "message": f"No simulated camera folder found for {location} (expected images/{location}/)."
            }

        # Count how many sequentially-numbered photos exist (1.*,
        # 2.*, ...) so callers can tell when they've run out.
        total = 0
        n = 1
        while _find_photo(folder, n) is not None:
            total += 1
            n += 1

        if total == 0:
            return {
                "success": False,
                "message": (
                    f"No numbered photos (1.png, 2.png, ...) found in "
                    f"images/{location}/."
                )
            }

        image_path = _find_photo(folder, index + 1)

        if image_path is None:
            return {
                "success": False,
                "message": (
                    f"No photo {index + 1} available at {location} "
                    f"(only {total} photo(s) exist)."
                ),
            }

        return {
            "success": True,
            "message": f"Image captured at {location} (photo {index + 1} of {total}).",
            "drone_id": self.drone_id,
            "image_path": str(image_path),
            "photo_index": index,
            "total_photos": total,
        }

    def return_home(self):
        self.position = "base"
        self.battery -= 5
        self.status = "returning"

        return {
            "success": True,
            "message": f"{self.drone_id} is returning home.",
            "drone_id": self.drone_id,
            "battery": self.battery,
        }

    def land(self):
        self.altitude = 0

        # A landed drone is back on the ground and ready for its next
        # mission, not permanently retired. Setting status back to
        # "available" (battery permitting) restores the intended
        # available -> flying -> returning -> available lifecycle,
        # instead of leaving drones stuck at "landed" forever.
        if self.battery >= 20:
            self.status = "available"
        else:
            self.status = "charging"

        return {
            "success": True,
            "message": f"{self.drone_id} landed successfully.",
            "drone_id": self.drone_id,
            "position": self.position,
            "battery": self.battery,
        }

    def telemetry(self):
        return {
            "drone_id": self.drone_id,
            "battery": self.battery,
            "position": self.position,
            "altitude": self.altitude,
            "status": self.status,
        }