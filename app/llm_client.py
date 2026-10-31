"""
Connects the firewall to a real chatbot. Supports GEMINI_API_KEY
(free tier, no credit card) or ANTHROPIC_API_KEY (paid). Falls back
to a clean message if the AI is unavailable, so the app never shows
raw errors (or API keys) to the user.
"""
import os
import time
import requests

_gemini_key = os.environ.get("GEMINI_API_KEY")
_anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

_anthropic_client = None
if _anthropic_key:
    try:
        import anthropic
        _anthropic_client = anthropic.Anthropic(api_key=_anthropic_key)
    except ImportError:
        _anthropic_client = None

# Only models that have a free tier. Order = preference.
# The lite model is listed first because it is the fast, reliable one.
GEMINI_MODELS = ["gemini-flash-lite-latest", "gemini-flash-latest"]

FALLBACK_REPLY = (
    "(The AI model is temporarily unavailable - most likely the free-tier "
    "request limit was reached. Please try again in a minute.) "
    "Your message DID pass the firewall: the verdict and risk score shown "
    "below come from PromptGuard's own detection logic and are not "
    "affected by the AI model being busy."
)


def _call_gemini(prompt: str) -> str:
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    for model in GEMINI_MODELS:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={_gemini_key}"
        )
        resp = None
        for attempt in range(2):  # retry once if Google is overloaded (503)
            try:
                resp = requests.post(url, json=body, timeout=20)
            except requests.exceptions.RequestException:
                resp = None  # timeout / network problem: try the next model
                break
            if resp.status_code == 503 and attempt == 0:
                time.sleep(2)
                continue
            break

        if resp is None:
            continue
        if resp.status_code == 429:
            # Quota exhausted: stop immediately. Trying more models would
            # only burn more quota.
            raise RuntimeError("rate limited (429)")
        if resp.status_code in (404, 503):
            continue  # model unavailable, try the next one
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini error {resp.status_code}")
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    raise RuntimeError("no Gemini model available")


def _call_anthropic(prompt: str) -> str:
    response = _anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in response.content if b.type == "text")


def get_llm_reply(prompt: str) -> str:
    if _gemini_key:
        try:
            return _call_gemini(prompt)
        except Exception:
            pass  # never show raw errors (they can contain the API key)

    if _anthropic_client is not None:
        try:
            return _call_anthropic(prompt)
        except Exception:
            pass

    if _gemini_key or _anthropic_client is not None:
        return FALLBACK_REPLY

    return (
        "(demo mode -- no GEMINI_API_KEY or ANTHROPIC_API_KEY set, so this is "
        "a canned reply) Your message passed the firewall and would normally "
        "be sent to the real AI model here."
    )