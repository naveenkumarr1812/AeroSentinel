class SafetyAgent:

    MIN_BATTERY = 30
    MAX_ALTITUDE = 120

    def check_mission(
        self,
        battery: int,
        location: str,
        altitude: int = 10,
        rag_context: list[dict] | None = None,
    ):

        # ----------------------------------------------------
        # Display that safety is using retrieved knowledge
        # ----------------------------------------------------

        print("\nSAFETY AGENT ANALYSIS")

        if rag_context:

            print(
                "Safety decision grounded in "
                f"{len(rag_context)} retrieved SOPs."
            )

        else:

            print(
                "Warning: No RAG context available."
            )

        # ----------------------------------------------------
        # Battery safety
        # ----------------------------------------------------

        if battery < self.MIN_BATTERY:

            return {
                "approved": False,
                "status": "REJECTED",
                "reason": (
                    f"Battery is {battery}%. "
                    f"Mission requires at least "
                    f"{self.MIN_BATTERY}%."
                ),
            }

        # ----------------------------------------------------
        # Altitude safety
        # ----------------------------------------------------

        if altitude > self.MAX_ALTITUDE:

            return {
                "approved": False,
                "status": "REJECTED",
                "reason": (
                    f"Altitude {altitude}m exceeds "
                    f"maximum allowed altitude "
                    f"of {self.MAX_ALTITUDE}m."
                ),
            }

        # ----------------------------------------------------
        # Geofence
        # ----------------------------------------------------

        allowed_locations = {
            "north_gate",
            "ground_area",
            "main_gate",
            "warehouse",
        }

        if location not in allowed_locations:

            return {
                "approved": False,
                "status": "REJECTED",
                "reason": (
                    f"{location} is outside "
                    "the configured geofence."
                ),
            }

        # ----------------------------------------------------
        # Mission approved
        # ----------------------------------------------------

        return {
            "approved": True,
            "status": "APPROVED",
            "reason": (
                "Mission passed safety checks "
                "and is consistent with the "
                "retrieved operational SOPs."
            ),
        }