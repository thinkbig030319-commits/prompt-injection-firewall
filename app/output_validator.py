"""
Defense in depth: checks the LLM's *reply* for signs of a leaked
system prompt or jailbreak compliance, even on allowed prompts.
"""
import re
from dataclasses import dataclass, field

LEAK_PATTERNS = [
    (re.compile(r"my (system prompt|instructions) (are|is)[:\s]", re.IGNORECASE), "system_prompt_leak"),
    (re.compile(r"i am (an ai|a language model) (with no|without any) (restrictions|filters|rules)", re.IGNORECASE), "jailbreak_compliance"),
    (re.compile(r"as an unrestricted (ai|assistant)", re.IGNORECASE), "jailbreak_compliance"),
    (re.compile(r"<\s*system\s*>", re.IGNORECASE), "role_tag_leak"),
]


@dataclass
class OutputValidationResult:
    safe: bool
    reasons: list = field(default_factory=list)


def validate_output(text: str) -> OutputValidationResult:
    reasons = []
    for pattern, name in LEAK_PATTERNS:
        if pattern.search(text):
            reasons.append(name)
    return OutputValidationResult(safe=len(reasons) == 0, reasons=reasons)
