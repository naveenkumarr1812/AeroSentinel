from rag.rag_engine import AeroSentinelRAG


class RAGAgent:

    def __init__(self):
        self.rag = AeroSentinelRAG()

    def retrieve_mission_knowledge(
        self,
        mission: str,
        location: str,
    ):

        query = (
            f"Mission: {mission}. "
            f"Location: {location}. "
            "What safety rules, operational procedures, "
            "battery and power requirements, security rules, "
            "and emergency procedures apply to this mission?"
        )

        # There are only 4 SOP documents in the knowledge base
        # (battery, emergency, mission, perimeter). With top_k=3, one
        # of them — usually battery_sop, since the query didn't
        # mention battery/power before — never made it into the
        # retrieved set and so never showed up in the UI. Retrieving
        # all 4 guarantees every SOP is always considered; this is a
        # small, fixed-size knowledge base, not a large corpus where
        # top-k truncation is actually needed.
        results = self.rag.retrieve(
            query=query,
            top_k=4,
        )

        print("\nRAG AGENT")

        for result in results:

            print(
                f"\nSource: {result['source']}"
            )

            print(
                result["content"]
            )

        return results