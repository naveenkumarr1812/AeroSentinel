import json

from agents.groq_client import GroqClientPool


class MissionCommander:

    def __init__(self):
        self.client = GroqClientPool()

    def understand_mission(self, user_request: str):

        prompt = f"""
You are the Mission Commander of AeroSentinel,
an autonomous drone security system.

Convert the user's request into a structured drone mission.

User request:
{user_request}

Return ONLY JSON:

{{
    "mission_type": "intrusion_detection",
    "location": "ground_area",
    "priority": "medium"
}}

Allowed mission types:

"patrol"
"inspection"
"intrusion_detection"

Priority must be:

"low"
"medium"
"high"

Known locations:

The "location" value must be EXACTLY one of these slugs. Each one
corresponds to a folder of real camera images on disk, so do not
invent a new location or rename these:

"north_gate"    -> the north gate / north entrance
"ground_area"   -> the ground area / open yard / field
"main_gate"     -> the main gate / front entrance
"warehouse"     -> the warehouse / storage building

Examples:

"inspect the ground area" -> location: "ground_area"
"check the north gate" -> location: "north_gate"
"patrol the main entrance" -> location: "main_gate"
"look at the warehouse" -> location: "warehouse"
"is anyone near the front gate" -> location: "main_gate"
"""

        # Anything here — network failure, auth failure, rate limit
        # on every configured key, a malformed response despite
        # response_format — is reported back as a normal dict with an
        # "error" key instead of raising, so the graph node calling
        # this can route to a clean rejection instead of crashing the
        # whole app. GroqClientPool already retries across any extra
        # API keys before this except block is ever reached.
        try:
            response = self.client.create_chat_completion(
                model="qwen/qwen3.6-27b",

                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],

                temperature=0,
                max_completion_tokens=200,
                reasoning_effort="none",

                response_format={
                    "type": "json_object"
                },
            )

            result = response.choices[0].message.content

            parsed = json.loads(result)

            if not parsed.get("location") or not parsed.get("mission_type"):
                return {
                    "mission_type": None,
                    "location": None,
                    "priority": None,
                    "error": "Commander response was missing required fields.",
                }

            return parsed

        except json.JSONDecodeError as e:
            return {
                "mission_type": None,
                "location": None,
                "priority": None,
                "error": f"Commander returned invalid JSON: {e}",
            }

        except Exception as e:
            return {
                "mission_type": None,
                "location": None,
                "priority": None,
                "error": f"Commander request failed: {e}",
            }