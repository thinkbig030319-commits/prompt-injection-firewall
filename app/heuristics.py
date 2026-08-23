"""
Layer 1: Fast, free heuristic detection for prompt injection.
"""
import re
from dataclasses import dataclass, field


@dataclass
class HeuristicResult:
    score: float
    triggered_rules: list = field(default_factory=list)


RULES = [
    ("override_instructions", re.compile(
        r"\b(ignore|disregard|forget)\b.{0,40}\b(previous|prior|above|"
        r"earlier|all)\b.{0,20}\b(instructions?|rules?|guidelines?|"
        r"directives?|context)\b", re.IGNORECASE), 0.9),
    ("reveal_system_prompt", re.compile(
        r"\b(reveal|show|print|repeat|output|leak|disclose)\b.{0,30}"
        r"\b(system prompt|hidden instructions?|configuration|initial "
        r"prompt|your instructions?)\b", re.IGNORECASE), 0.85),
    ("persona_hijack", re.compile(
        r"\byou are now\b|\bact as an? (ai|assistant) (with|without)\b|"
        r"\bpretend (you are|to be)\b|\bDAN\b|\bdeveloper mode\b|"
        r"\bunrestricted (ai|mode)\b|\bno (content )?filters?\b", re.IGNORECASE), 0.75),
    ("role_injection_tags", re.compile(
        r"<\s*system\s*>|\[\s*system\s*\]|\bSYSTEM:\s|\bASSISTANT:\s|"
        r"###\s*(system|instruction)", re.IGNORECASE), 0.6),
    ("override_keywords", re.compile(
        r"\boverride\b.{0,20}\b(safety|restriction|filter|rule|"
        r"instruction)s?\b|\badmin (override|mode|code)\b|\bmaintenance "
        r"mode\b|\bjailbreak\b", re.IGNORECASE), 0.7),
    ("encoded_payload", re.compile(r"\b[A-Za-z0-9+/]{24,}={0,2}\b"), 0.3),
]


def check_heuristics(text: str) -> HeuristicResult:
    triggered = []
    max_score = 0.0
    for name, pattern, weight in RULES:
        if pattern.search(text):
            triggered.append(name)
            max_score = max(max_score, weight)
    return HeuristicResult(score=max_score, triggered_rules=triggered)
