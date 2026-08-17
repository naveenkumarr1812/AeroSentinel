import os
import base64
import json
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


def _mime_type_for(image_path: str) -> str:
    ext = Path(image_path).suffix.lower()
    return _MIME_TYPES.get(ext, "image/png")


class VisionAnalyzer:

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not set in the .env file."
            )

        self.client = Groq(api_key=api_key)

    def analyze_image(self, image_path: str):

        # ---------------------------------------
        # 1. Read image
        # ---------------------------------------
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(
                image_file.read()
            ).decode("utf-8")

        mime_type = _mime_type_for(image_path)

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
        response = self.client.chat.completions.create(
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
                                    f"data:{mime_type};base64,"
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

            return {
                "error": "VLM returned invalid JSON.",
                "raw_response": result,
            }

    def ask_about_image(self, image_path: str, question: str) -> str:
        """
        Freeform natural-language Q&A about a specific captured
        image. Unlike analyze_image() (which always forces the fixed
        detection JSON schema), this answers whatever the operator
        actually asks — e.g. "what color is the vehicle?" or "how
        many people do you see?" — as plain text.

        This is a read-only side-channel for human curiosity: it does
        not touch mission state or the LangGraph workflow at all.
        """
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(
                image_file.read()
            ).decode("utf-8")

        mime_type = _mime_type_for(image_path)

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

        response = self.client.chat.completions.create(
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
                                    f"data:{mime_type};base64,"
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

        return response.choices[0].message.content.strip()