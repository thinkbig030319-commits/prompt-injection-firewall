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
    # Google's available model names change frequently. Try a short list
    # of common candidates in order, and use whichever one actually works
    # for this API key -- this makes the app resilient to Google
    # deprecating or renaming models without warning.
    candidates = ["gemini-flash-latest", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-pro-latest"]
    last_error = None
    for model_name in candidates:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model_name}:generateContent?key={_gemini_key}"
        )
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            resp = requests.post(url, json=body, timeout=30)
            if resp.status_code == 404:
                last_error = f"{model_name} not available (404)"
                continue  # try the next candidate
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except requests.exceptions.HTTPError as e:
            last_error = str(e)
            if resp.status_code != 503:
                continue  # non-overload errors: try next candidate too
        except Exception as e:
            last_error = str(e)
            continue
    raise RuntimeError(f"All Gemini model candidates failed. Last error: {last_error}")


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