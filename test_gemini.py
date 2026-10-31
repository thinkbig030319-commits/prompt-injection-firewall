"""Diagnostic: asks Google directly why Gemini is not answering.
Prints only status codes and Google's error text -- never the key."""
import os
import requests

key = os.environ.get("GEMINI_API_KEY")
if not key:
    print("NO KEY SET in this window. Run: $env:GEMINI_API_KEY=\"your-key\"")
    raise SystemExit

print("key length:", len(key), "| starts with:", key[:3])
BASE = "https://generativelanguage.googleapis.com/v1beta"


def err_text(r):
    try:
        return r.json().get("error", {}).get("message", "")[:300]
    except Exception:
        return "(no readable error body)"


try:
    r = requests.get(f"{BASE}/models", params={"key": key}, timeout=20)
    print("\n1) List models -> status", r.status_code)
    if r.status_code == 200:
        names = [m["name"] for m in r.json().get("models", [])
                 if "generateContent" in m.get("supportedGenerationMethods", [])]
        print("   Models your key can use (flash ones):")
        for n in names:
            if "flash" in n:
                print("    ", n)
    else:
        print("   Google says:", err_text(r))
except Exception as e:
    print("   network problem:", type(e).__name__)

print("\n2) Try generating text:")
for model in ["gemini-flash-latest", "gemini-flash-lite-latest"]:
    try:
        r = requests.post(
            f"{BASE}/models/{model}:generateContent",
            params={"key": key},
            json={"contents": [{"parts": [{"text": "Say hi in 3 words"}]}]},
            timeout=30,
        )
        if r.status_code == 200:
            txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            print(f"   {model} -> 200 OK, reply: {txt.strip()[:60]}")
        else:
            print(f"   {model} -> {r.status_code}: {err_text(r)}")
    except Exception as e:
        print(f"   {model} -> network problem: {type(e).__name__}")