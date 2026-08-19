import time
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

    # Simulated time (seconds) for a full 0% -> 100% recharge.
    FULL_CHARGE_SECONDS = 30

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

        # Charging state — set when start_charging() is called.
        self._charging_since = None
        self._charge_start_battery = None

    def _sync_charging(self):
        """
        Recomputes battery/status from elapsed wall-clock time if this
        drone is currently charging. Called at the top of every method
        that reads or depends on battery/status, so charge progress is
        always accurate whenever it's checked (e.g. every time the UI
        reruns) — no background thread or timer loop needed.
        """
        if self.status != "charging" or self._charging_since is None:
            return

        elapsed = time.time() - self._charging_since
        gained = (elapsed / self.FULL_CHARGE_SECONDS) * 100
        new_battery = min(100, self._charge_start_battery + gained)
        self.battery = int(new_battery)

        if self.battery >= 100:
            self.battery = 100
            self.status = "available"
            self._charging_since = None
            self._charge_start_battery = None

    def start_charging(self):
        """
        Manually starts charging this drone. Only works while it's at
        base and not currently flying/returning — a real drone can't
        charge mid-air.
        """
        self._sync_charging()

        if self.position != "base":
            return {
                "success": False,
                "message": f"{self.drone_id} must be at base to charge."
            }

        if self.status in ("flying", "returning", "busy"):
            return {
                "success": False,
                "message": f"{self.drone_id} is not available to charge right now."
            }

        if self.battery >= 100:
            return {
                "success": False,
                "message": f"{self.drone_id} is already fully charged."
            }

        self.status = "charging"
        self._charging_since = time.time()
        self._charge_start_battery = self.battery

        return {
            "success": True,
            "message": f"{self.drone_id} is now charging.",
            "drone_id": self.drone_id,
            "battery": self.battery,
        }

    def stop_charging(self):
        """
        Cancels an in-progress charge — the drone keeps whatever
        battery it gained so far (applied via _sync_charging()) and
        goes back to a normal at-base state instead of continuing to
        charge. Lets the operator toggle the Charge button off.
        """
        self._sync_charging()

        if self.status != "charging":
            return {
                "success": False,
                "message": f"{self.drone_id} is not currently charging."
            }

        self._charging_since = None
        self._charge_start_battery = None
        self.status = "available" if self.battery >= 20 else "landed"

        return {
            "success": True,
            "message": f"{self.drone_id} stopped charging.",
            "drone_id": self.drone_id,
            "battery": self.battery,
        }

    def takeoff(self, altitude: int = 10):
        self._sync_charging()

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
        """
        folder = Path("images") / location

        if not folder.exists() or not folder.is_dir():
            return {
                "success": False,
                "message": f"No simulated camera folder found for {location} (expected images/{location}/)."
            }

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
        # mission if it has enough charge — otherwise it's grounded
        # until the operator explicitly starts charging it (see
        # start_charging()). This is a manual step now rather than
        # automatic, per the operator-controlled charging workflow.
        if self.battery >= 20:
            self.status = "available"
        else:
            self.status = "landed"

        return {
            "success": True,
            "message": f"{self.drone_id} landed successfully.",
            "drone_id": self.drone_id,
            "position": self.position,
            "battery": self.battery,
        }

    def telemetry(self):
        self._sync_charging()

        return {
            "drone_id": self.drone_id,
            "battery": self.battery,
            "position": self.position,
            "altitude": self.altitude,
            "status": self.status,
        }