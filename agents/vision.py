import io
import base64
import json

from dotenv import load_dotenv
from PIL import Image

from agents.groq_client import GroqClientPool


load_dotenv()


# Real photos (especially large PNGs from stock/AI sources) can easily
# exceed Groq's inline image payload limit, even though the tiny
# placeholder images used during early development never did. Every
# image sent to the VLM is downsized and re-encoded as a compressed
# JPEG first, regardless of its original size or format.
MAX_DIMENSION = 1024
JPEG_QUALITY = 82


def _load_image_as_base64(image_path: str) -> str:
    with Image.open(image_path) as img:
        img = img.convert("RGB")

        width, height = img.size
        largest_side = max(width, height)

        if largest_side > MAX_DIMENSION:
            scale = MAX_DIMENSION / largest_side
            img = img.resize(
                (max(1, int(width * scale)), max(1, int(height * scale))),
                Image.LANCZOS,
            )

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        image_bytes = buffer.getvalue()

    return base64.b64encode(image_bytes).decode("utf-8")


class VisionAnalyzer:

    def __init__(self):
        self.client = GroqClientPool()

    def analyze_image(self, image_path: str):

        def _fallback(reason: str):
            # A safe, complete result shape so every downstream .get()
            # call in the graph (risk_level, confidence, description,
            # etc.) still works even when the VLM call itself failed —
            # nothing crashes, the mission just proceeds with an
            # "unknown" analysis instead of no analysis at all.
            return {
                "error": reason,
                "person_detected": False,
                "vehicle_detected": False,
                "intrusion_detected": False,
                "risk_level": "unknown",
                "confidence": 0,
                "description": f"Vision analysis unavailable: {reason}",
            }

        # ---------------------------------------
        # 1. Read + compress image
        # ---------------------------------------
        try:
            image_data = _load_image_as_base64(image_path)
        except Exception as e:
            return _fallback(f"Could not read image file: {e}")

        # ---------------------------------------
        # 2. Prompt for VLM
        # ---------------------------------------
        prompt = """
You are the vision system of AeroSentinel,
an autonomous drone security platform.

Analyze the provided aerial/security image.

Your task is to identify:

1. Whether a person is visible.
2. Whether a vehicle is visible.
3. Whether a possible security intrusion is present.
4. The risk level.
5. Your confidence from 0 to 1.
6. A short description of the scene.

IMPORTANT:

Return ONLY valid JSON.

Do not return:
- Markdown
- Code fences
- Explanations outside JSON
- Thinking/reasoning
- <think> tags

Return exactly this structure:

{
    "person_detected": true,
    "vehicle_detected": false,
    "intrusion_detected": true,
    "risk_level": "medium",
    "confidence": 0.89,
    "description": "Person detected near the restricted perimeter."
}

Allowed risk levels:

"none"
"low"
"medium"
"high"
"""

        # ---------------------------------------
        # 3. Call VLM
        # ---------------------------------------
        try:
            response = self.client.create_chat_completion(
                model="qwen/qwen3.6-27b",

                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": (
                                        f"data:image/jpeg;base64,"
                                        f"{image_data}"
                                    )
                                },
                            },
                        ],
                    }
                ],

                temperature=0,

                max_completion_tokens=300,

                # Disable reasoning for machine-readable output
                reasoning_effort="none",

                # Force JSON response
                response_format={
                    "type": "json_object"
                },
            )
        except Exception as e:
            # Network failure, auth failure, rate limit, oversized
            # request, etc. — report it instead of crashing the graph.
            return _fallback(f"VLM request failed: {e}")

        # ---------------------------------------
        # 4. Extract VLM response
        # ---------------------------------------
        result = response.choices[0].message.content

        # ---------------------------------------
        # 5. Parse JSON
        # ---------------------------------------
        try:

            parsed_result = json.loads(result)

            return parsed_result

        except json.JSONDecodeError:

            return _fallback("VLM returned invalid JSON.")

    def ask_about_image(self, image_path: str, question: str) -> str:
        """
        Freeform natural-language Q&A about a specific captured
        image. Unlike analyze_image() (which always forces the fixed
        detection JSON schema), this answers whatever the operator
        actually asks — e.g. "what color is the vehicle?" or "how
        many people do you see?" — as plain text.

        This is a read-only side-channel for human curiosity: it does
        not touch mission state or the LangGraph workflow at all. Any
        failure here is returned as a plain-text message instead of
        raised, so a bad question or a transient API hiccup can't
        crash the whole app from inside the chat box.
        """
        try:
            image_data = _load_image_as_base64(image_path)
        except Exception as e:
            return f"Sorry, I couldn't read that image: {e}"

        prompt = f"""
You are the vision system of AeroSentinel, an autonomous drone
security platform. A security operator is reviewing a photo captured
during a mission and has a question about it.

Answer the question clearly and concisely, based only on what is
actually visible in the image. If you cannot tell something from the
image, say so honestly instead of guessing.

Operator's question:
{question}
"""

        try:
            response = self.client.create_chat_completion(
                model="qwen/qwen3.6-27b",

                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": (
                                        f"data:image/jpeg;base64,"
                                        f"{image_data}"
                                    )
                                },
                            },
                        ],
                    }
                ],

                temperature=0.3,
                max_completion_tokens=300,
                reasoning_effort="none",
            )
        except Exception as e:
            return f"Sorry, I couldn't analyze that image right now: {e}"

        return response.choices[0].message.content.strip()