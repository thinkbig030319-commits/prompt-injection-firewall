"""
Persistent logging of every firewall decision using SQLite (stdlib).
"""
import hashlib
import os
import sqlite3
import time
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "promptguard.db")


def _hash_prompt(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                prompt_hash TEXT NOT NULL,
                prompt_preview TEXT NOT NULL,
                verdict TEXT NOT NULL,
                risk_score REAL NOT NULL,
                heuristic_score REAL NOT NULL,
                ml_score REAL NOT NULL,
                semantic_score REAL NOT NULL,
                reasons TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'check'
            )
        """)


def log_check(text: str, result, source: str = "check"):
    preview = text[:60] + ("..." if len(text) > 60 else "")
    with _connect() as conn:
        conn.execute(
            """INSERT INTO checks
               (timestamp, prompt_hash, prompt_preview, verdict, risk_score,
                heuristic_score, ml_score, semantic_score, reasons, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (time.time(), _hash_prompt(text), preview, result.verdict, result.risk_score,
             result.heuristic_score, result.ml_score, result.semantic_score,
             ", ".join(result.reasons), source),
        )


def get_recent_checks(limit: int = 50):
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM checks ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]


def get_stats():
    with _connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM checks").fetchone()[0]
        by_verdict = dict(conn.execute("SELECT verdict, COUNT(*) FROM checks GROUP BY verdict").fetchall())
        return {
            "total": total,
            "allow": by_verdict.get("allow", 0),
            "flag": by_verdict.get("flag", 0),
            "block": by_verdict.get("block", 0),
        }
