from memory.mission_memory import MissionMemory


class MemoryAgent:

    def __init__(self):

        self.memory = MissionMemory()

    # ========================================================
    # RETRIEVE PREVIOUS EXPERIENCE
    # ========================================================

    def retrieve_history(
        self,
        location: str
    ):

        history = self.memory.search_by_location(
            location=location,
            limit=5
        )

        print("\nMEMORY AGENT")

        if not history:

            print(
                f"No previous missions found "
                f"at {location}."
            )

            return []

        print(
            f"Found {len(history)} previous "
            f"mission(s) at {location}."
        )

        for mission in history:

            print(
                f"\n[{mission['timestamp']}]"
            )

            print(
                f"Detection: "
                f"{mission['detection']}"
            )

            print(
                f"Confidence: "
                f"{mission['confidence']}"
            )

            print(
                f"Risk: "
                f"{mission['risk_level']}"
            )

            print(
                f"Human decision: "
                f"{mission['human_decision']}"
            )

        return history

    # ========================================================
    # SAVE EXPERIENCE
    # ========================================================

    def save_mission(
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

        mission = self.memory.record_mission(

            drone_id=drone_id,

            location=location,

            mission_type=mission_type,

            detection=detection,

            confidence=confidence,

            risk_level=risk_level,

            human_decision=human_decision,

            human_reason=human_reason,

            outcome=outcome,
        )

        print(
            "\nMISSION MEMORY UPDATED"
        )

        print(
            f"Mission ID: "
            f"{mission['mission_id']}"
        )

        return mission

    # ========================================================
    # DELETE EXPERIENCE
    # ========================================================

    def delete_mission(self, mission_id: str) -> bool:
        return self.memory.delete_mission(mission_id)