from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple

from pocketflow import Node


class LLMClient(Protocol):
    def generate(self, prompt: str, *, temperature: float = 0.2) -> str: ...


@dataclass
class CodeAgentParams:
    project_root: str
    rtl_dir: str = "rtl"
    allowed_exts: Tuple[str, ...] = (".v", ".sv")  # You said Verilog TB, but RTL may still include .sv in some repos.
    temperature: float = 0.2
    max_files: int = 32
    context_radius_lines: int = 2
    output_mode: str = "json_files"  # reserved for future: "unidiff"
    forbid_tb_edit: bool = True
    strict_json_only: bool = True


class CodeAgentNode(Node):
    """
    Code Agent:
      - Generates RTL from spec when no RTL exists, or
      - Patches RTL based on Review/Verification feedback.

    Expected shared inputs (suggested keys):
      - spec: str (user requirement / natural language)
      - rtl_files: List[str] (relative paths)
      - review_feedback: dict (from Review Agent)
      - verify_feedback: dict (from Verification Agent)

    Outputs to shared:
      - code_agent_output_raw: str (LLM raw)
      - code_agent_notes: str
      - updated_rtl_files: List[str]
      - last_edit_summary: str
    """

    def __init__(self, *, llm_client: LLMClient, params: CodeAgentParams):
        super().__init__()
        self._llm = llm_client
        self._p = params
        self._root = Path(params.project_root).resolve()

    # ------------------------- PocketFlow hooks -------------------------

    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        spec = (shared.get("spec") or shared.get("user_query") or "").strip()
        if not spec:
            raise ValueError("shared['spec'] (or shared['user_query']) is required for CodeAgentNode.")

        rtl_files = shared.get("rtl_files")
        if rtl_files is None:
            rtl_files = self._auto_discover_rtl_files()

        review_fb = shared.get("review_feedback")
        verify_fb = shared.get("verify_feedback")

        rtl_context = self._read_files_with_context(rtl_files, max_files=self._p.max_files)
        feedback_text = self._format_feedback(review_fb, verify_fb)

        prompt = self._build_prompt(
            spec=spec,
            rtl_context=rtl_context,
            feedback_text=feedback_text,
            rtl_files=rtl_files,
        )

        return {
            "spec": spec,
            "rtl_files": rtl_files,
            "prompt": prompt,
            "has_feedback": bool(feedback_text.strip()),
        }

    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        raw = self._llm.generate(prep_res["prompt"], temperature=self._p.temperature)
        return {"raw": raw}

    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> Dict[str, Any]:
        raw = exec_res["raw"]
        shared["code_agent_output_raw"] = raw

        parsed = self._parse_llm_json(raw, strict=self._p.strict_json_only)
        files = parsed.get("files", [])
        notes = (parsed.get("notes") or "").strip()

        updated_paths: List[str] = []
        for f in files:
            rel = str(f.get("path") or "").strip()
            content = str(f.get("content") or "")
            if not rel:
                continue
            self._validate_target_path(rel)
            if self._p.forbid_tb_edit and self._looks_like_tb(rel):
                raise ValueError(f"TB edits are forbidden by params, but LLM attempted to edit: {rel}")
            self._write_text(rel, content)
            updated_paths.append(rel)

        shared["code_agent_notes"] = notes
        shared["updated_rtl_files"] = updated_paths

        shared["last_edit_summary"] = self._make_edit_summary(
            has_feedback=prep_res["has_feedback"],
            updated_paths=updated_paths,
            notes=notes,
        )
        return shared

    # ------------------------- Prompting -------------------------

    def _build_prompt(self, *, spec: str, rtl_context: str, feedback_text: str, rtl_files: List[str]) -> str:
        rules = [
            "You are a senior RTL engineer.",
            "Goal: produce correct synthesizable Verilog RTL that satisfies the spec and passes the provided checks.",
            "Do NOT modify testbench files.",
            "Keep module interfaces stable unless spec explicitly requires changes.",
            "Return ONLY valid JSON (no markdown, no code fences).",
            'JSON schema: {"files":[{"path":"relative/path.v","content":"full file content"}], "notes":"short explanation"}',
        ]
        if self._p.strict_json_only:
            rules.append("If you cannot comply with JSON-only output, still return JSON-only output.")

        mode_hint = "PATCH existing RTL according to feedback." if feedback_text.strip() else "GENERATE RTL from spec."
        existing_hint = "\n".join([f"- {p}" for p in rtl_files]) if rtl_files else "(none)"

        prompt = f"""\
SYSTEM RULES:
{chr(10).join(f"- {r}" for r in rules)}

TASK MODE:
- {mode_hint}

SPEC:
{spec}

EXISTING RTL FILES (relative paths):
{existing_hint}

EXISTING RTL CONTENT (read-only context):
{rtl_context}

FEEDBACK (from review/verification; if empty, ignore):
{feedback_text}

OUTPUT REQUIREMENTS:
- Output ONLY JSON.
- Include ONLY the RTL files that need to be created/updated.
- Each file's "content" must be a complete file (not a diff).
"""
        return prompt

    # ------------------------- Feedback formatting -------------------------

    def _format_feedback(self, review_fb: Any, verify_fb: Any) -> str:
        parts: List[str] = []

        if isinstance(review_fb, dict):
            parts.append("REVIEW_FEEDBACK(spyglass):")
            parts.append(self._summarize_review_feedback(review_fb))

        if isinstance(verify_fb, dict):
            parts.append("VERIFY_FEEDBACK(iverilog):")
            parts.append(self._summarize_verify_feedback(verify_fb))

        return "\n".join([p for p in parts if p.strip()])

    def _summarize_review_feedback(self, fb: Dict[str, Any]) -> str:
        if fb.get("passed") is True:
            return "- No syntax/lint errors.\n"
        issues = fb.get("issues") or []
        lines = []
        for it in issues[:50]:
            sev = it.get("severity")
            f = it.get("file")
            ln = it.get("line")
            msg = it.get("message")
            lines.append(f"- {sev}: {f}:{ln} {msg}")
            ctx = it.get("context") or []
            for c in ctx[:8]:
                lines.append(f"    {c}")
        return "\n".join(lines) + ("\n" if lines else "")

    def _summarize_verify_feedback(self, fb: Dict[str, Any]) -> str:
        if fb.get("passed") is True:
            return "- All test cases passed.\n"
        lines = []
        if fb.get("compile_passed") is False:
            for e in (fb.get("compile_errors") or [])[:50]:
                lines.append(f"- COMPILE_ERROR: {e.get('file')}:{e.get('line')} {e.get('message')}")
        for case in (fb.get("failed_cases") or [])[:50]:
            cname = case.get("case") or "<unknown>"
            lines.append(f"- FAIL_CASE: {cname} {case.get('message')}")
        return "\n".join(lines) + ("\n" if lines else "")

    # ------------------------- File IO -------------------------

    def _auto_discover_rtl_files(self) -> List[str]:
        rtl_root = (self._root / self._p.rtl_dir).resolve()
        if not rtl_root.exists():
            return []
        out: List[str] = []
        for p in rtl_root.rglob("*"):
            if p.is_file() and p.suffix in self._p.allowed_exts:
                out.append(str(p.relative_to(self._root)).replace("\\", "/"))
        out.sort()
        return out

    def _read_files_with_context(self, rel_paths: List[str], *, max_files: int) -> str:
        chunks: List[str] = []
        for rel in rel_paths[:max_files]:
            try:
                abs_path = (self._root / rel).resolve()
                if not abs_path.exists():
                    continue
                if abs_path.suffix not in self._p.allowed_exts:
                    continue
                text = abs_path.read_text(encoding="utf-8", errors="ignore")
                chunks.append(f"### FILE: {rel}\n{text}\n")
            except Exception:
                continue
        return "\n".join(chunks).strip()

    def _write_text(self, rel_path: str, content: str) -> None:
        abs_path = (self._root / rel_path).resolve()
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content, encoding="utf-8")

    def _validate_target_path(self, rel_path: str) -> None:
        if rel_path.startswith(("/", "\\")) or ".." in Path(rel_path).parts:
            raise ValueError(f"Unsafe path traversal: {rel_path}")
        abs_path = (self._root / rel_path).resolve()
        if self._root not in abs_path.parents and abs_path != self._root:
            raise ValueError(f"Path escapes project root: {rel_path}")
        if Path(rel_path).suffix not in self._p.allowed_exts:
            raise ValueError(f"Disallowed file extension for RTL write: {rel_path}")

    def _looks_like_tb(self, rel_path: str) -> bool:
        p = rel_path.lower()
        return ("tb" in p) or ("/test/" in p) or ("/tests/" in p) or p.endswith("_tb.v") or p.endswith("_tb.sv")

    # ------------------------- LLM output parsing -------------------------

    def _parse_llm_json(self, raw: str, *, strict: bool) -> Dict[str, Any]:
        text = raw.strip()

        if strict:
            return json.loads(text)

        # lenient: try to extract first {...} block
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not m:
            raise ValueError("LLM output is not JSON and no JSON object found.")
        return json.loads(m.group(0))

    # ------------------------- Summaries -------------------------

    def _make_edit_summary(self, *, has_feedback: bool, updated_paths: List[str], notes: str) -> str:
        mode = "fix" if has_feedback else "gen"
        files = ", ".join(updated_paths) if updated_paths else "(no files updated)"
        n = notes if notes else "(no notes)"
        return f"[code_agent:{mode}] updated: {files}; notes: {n}"
