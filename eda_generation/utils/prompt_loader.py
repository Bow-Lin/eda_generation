from __future__ import annotations

from pathlib import Path


_PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"


def load_prompt_template(name: str) -> str:
    path = _PROMPT_DIR / name
    return path.read_text(encoding="utf-8")
