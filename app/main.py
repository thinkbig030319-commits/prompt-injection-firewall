"""
FastAPI app exposing the firewall, a protected chat endpoint, and a
logs API for the dashboard.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.pipeline import evaluate_prompt
from app.llm_client import get_llm_reply
from app.output_validator import validate_output
from app import database

app = FastAPI(
    title="Prompt Injection Detection & Defense Firewall",
    description="Detects and blocks likely prompt-injection attempts before they reach an LLM.",
    version="0.2.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DEMO_DIR = os.path.join(os.path.dirname(__file__), "..", "demo")


@app.on_event("startup")
def startup():
    database.init_db()


class CheckRequest(BaseModel):
    prompt: str


class CheckResponse(BaseModel):
    risk_score: float
    verdict: str
    heuristic_score: float
    ml_score: float
    semantic_score: float
    reasons: list[str]


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    blocked: bool
    verdict: str
    risk_score: float
    reasons: list[str]
    reply: str | None = None
    output_flagged: bool = False


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/check", response_model=CheckResponse)
def check_prompt(req: CheckRequest):
    result = evaluate_prompt(req.prompt)
    database.log_check(req.prompt, result, source="check")
    return CheckResponse(
        risk_score=result.risk_score, verdict=result.verdict,
        heuristic_score=result.heuristic_score, ml_score=result.ml_score,
        semantic_score=result.semantic_score, reasons=result.reasons,
    )


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    result = evaluate_prompt(req.prompt)
    database.log_check(req.prompt, result, source="chat")

    if result.verdict == "block":
        return ChatResponse(
            blocked=True, verdict=result.verdict, risk_score=result.risk_score,
            reasons=result.reasons, reply=None,
        )

    reply = get_llm_reply(req.prompt)
    output_check = validate_output(reply)

    return ChatResponse(
        blocked=False, verdict=result.verdict, risk_score=result.risk_score,
        reasons=result.reasons, reply=reply, output_flagged=not output_check.safe,
    )


@app.get("/logs")
def logs(limit: int = 50):
    return {"stats": database.get_stats(), "recent": database.get_recent_checks(limit=limit)}


@app.get("/")
def demo_index():
    return FileResponse(os.path.join(DEMO_DIR, "index.html"))


@app.get("/chat.html")
def chat_page():
    return FileResponse(os.path.join(DEMO_DIR, "chat.html"))


@app.get("/dashboard.html")
def dashboard_page():
    return FileResponse(os.path.join(DEMO_DIR, "dashboard.html"))
