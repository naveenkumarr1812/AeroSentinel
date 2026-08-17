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
            "security rules, and emergency procedures "
            "apply to this mission?"
        )

        results = self.rag.retrieve(
            query=query,
            top_k=3,
        )

        print("\n📚 RAG AGENT")

        for result in results:

            print(
                f"\nSource: {result['source']}"
            )

            print(
                result["content"]
            )

        return results