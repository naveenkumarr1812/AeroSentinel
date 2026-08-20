import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


def _load_api_keys():
    """
    Reads GROQ_API_KEY plus any number of numbered fallback keys
    (GROQ_API_KEY_2, GROQ_API_KEY_3, ...) from the .env file. Only
    keys that are actually set are included, so this works fine with
    just one key configured — the fallback keys are optional.
    """
    keys = []

    primary = os.getenv("GROQ_API_KEY")
    if primary:
        keys.append(primary)

    i = 2
    while True:
        key = os.getenv(f"GROQ_API_KEY_{i}")
        if not key:
            break
        keys.append(key)
        i += 1

    if not keys:
        raise ValueError(
            "No Groq API key found. Set GROQ_API_KEY in the .env file "
            "(and optionally GROQ_API_KEY_2, GROQ_API_KEY_3, ... for "
            "automatic fallback)."
        )

    return keys


class GroqClientPool:
    """
    Wraps one or more Groq API keys and transparently falls back to
    the next key if a call fails — a rate limit, an expired key, or a
    transient API error on key #1 no longer takes the whole app down;
    it just quietly retries with key #2 (and #3, ...) before finally
    giving up.

    Used by both MissionCommander and VisionAnalyzer so the fallback
    logic only has to live in one place.
    """

    def __init__(self):
        self._api_keys = _load_api_keys()
        self._clients = [Groq(api_key=key) for key in self._api_keys]

    @property
    def key_count(self) -> int:
        return len(self._clients)

    def create_chat_completion(self, **kwargs):
        last_error = None

        for index, client in enumerate(self._clients):
            try:
                return client.chat.completions.create(**kwargs)
            except Exception as e:
                last_error = e
                remaining = len(self._clients) - index - 1
                print(
                    f"\nGROQ: API key #{index + 1} failed ({e}). "
                    f"{f'Trying key #{index + 2} next...' if remaining else 'No more keys to try.'}"
                )

        # Every key failed — re-raise the last error so the caller's
        # own try/except (which returns a safe fallback result) can
        # handle it, rather than swallowing it silently here.
        raise last_error