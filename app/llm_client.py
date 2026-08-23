"""
Connects the firewall to a real chatbot. Supports GEMINI_API_KEY
(free tier, no credit card) or ANTHROPIC_API_KEY (paid). Falls back
to a canned demo-mode reply if neither is set.
"""
import os
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


def _call_gemini(prompt: str) -> str:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={_gemini_key}"
    )
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    resp = requests.post(url, json=body, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def _call_anthropic(prompt: str) -> str:
    response = _anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def get_llm_reply(prompt: str) -> str:
    if _gemini_key:
        try:
            return _call_gemini(prompt)
        except Exception as e:
            return f"[Gemini call failed: {e}]"

    if _anthropic_client is not None:
        try:
            return _call_anthropic(prompt)
        except Exception as e:
            return f"[Claude call failed: {e}]"

    return (
        "(demo mode -- no GEMINI_API_KEY or ANTHROPIC_API_KEY set, so this is "
        "a canned reply) Your message passed the firewall and would normally "
        "be sent to the real AI model here. Set the GEMINI_API_KEY environment "
        "variable (free, no credit card) to connect a real model."
    )
