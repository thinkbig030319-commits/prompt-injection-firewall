# PromptGuard — Prompt Injection Detection & Defense Firewall

A firewall that sits in front of an LLM application and detects, flags,
or blocks likely **prompt injection** attempts — with a real protected
chat interface, a live dashboard, and persistent logging.

## How it works

Every prompt passes through **three** detection layers, then a combined scorer:

```
prompt → [Layer 1: heuristic rules]          → heuristic_score
       → [Layer 2: TF-IDF + LogisticRegr.]   → ml_score
       → [Layer 3: semantic similarity]      → semantic_score
       → combined risk_score → verdict (allow / flag / block)
```

**Layer 1 — Heuristics** (`app/heuristics.py`) — fast regex rules for well-known attack patterns.

**Layer 2 — ML classifier** (`app/train.py`) — TF-IDF + Logistic Regression trained on labeled examples.

**Layer 3 — Semantic similarity** (`app/semantic.py`) — TF-IDF cosine similarity against known attack intents, catching reworded attacks. *(A production version would use neural sentence embeddings — see Limitations.)*

**Combiner** (`app/pipeline.py`) — strongest signal as base risk, plus a boost scaling with how many layers agree. Thresholds: `allow` (< 0.40) / `flag` (0.40-0.75) / `block` (>= 0.75).

**Output validation** (`app/output_validator.py`) — checks the AI's reply too, for defense in depth.

## What's new since the MVP

| Feature | Where |
|---|---|
| Semantic detection layer | `app/semantic.py` |
| Real chat, protected end-to-end (Gemini free tier or Claude) | `app/llm_client.py`, `/chat`, `demo/chat.html` |
| Persistent logging (SQLite) | `app/database.py` |
| Live dashboard (React, no build step) | `demo/dashboard.html` |
| Output validation | `app/output_validator.py` |
| Optional Docker deployment | `Dockerfile` |

## Running it

```bash
pip install -r requirements.txt
python3 data/generate_dataset.py
python3 app/train.py
uvicorn app.main:app --reload --port 8000
```

Then open:
- **http://localhost:8000** — check individual prompts
- **http://localhost:8000/chat.html** — chat through the firewall live
- **http://localhost:8000/dashboard.html** — live log of every decision

To connect a real AI model in the chat page, set `GEMINI_API_KEY`
(free, no credit card — get one at https://aistudio.google.com/app/apikey)
or `ANTHROPIC_API_KEY` (paid) before starting the server. Without either,
`/chat` still works end-to-end with a canned demo reply.

## Results

`python3 -m app.evaluate` benchmarks the full pipeline against a
held-out generalization set (prompts with different phrasing than the
training data): **10/12 (83.3%)** correct, with all 6 attacks caught
after adding the semantic layer. 2 false positives remain on benign
prompts using imperative phrasing — an honest, documented limitation
of a 90-example training set.

## Limitations & Future Work

- **Small training set (90 examples).** Enough to prove the architecture, not enough for production accuracy.
- **Semantic layer uses TF-IDF, not neural embeddings** — a deliberate scope trade-off to avoid a large model download/PyTorch dependency.
- **No DistilBERT / deep transformer classifier.**
- **No adversarial robustness testing yet** (unicode obfuscation, translation-based bypasses).
- **No PDF/RAG-based indirect injection protection.**
- **Dashboard has no auth** — fine for a local demo, would need access control before real deployment.

## Why this matters

This project demonstrates practical, working familiarity with the
prompt injection threat model, a layered detection architecture, an
actual protected chat pipeline, persistent logging/monitoring, and
clear-eyed awareness of the current implementation's real limits.
