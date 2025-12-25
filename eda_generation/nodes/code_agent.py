from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pocketflow import Node
from utils.clients.iflow_client import IFlowClient


@dataclass
class CodeAgentParams:
    project_root: str
    rtl_dir: str = "rtl"
    allowed_exts: Tuple[str, ...] = (".v", ".sv")
    temperature: float = 0.2
    max_files: int = 32
    output_mode: str = "json_files"
    forbid_tb_edit: bool = True
    strict_json_only: bool = True
    # When using Qwen structured output, set response_format to enforce JSON (see
    # https://help.aliyun.com/zh/model-studio/qwen-structured-output). Use a
    # factory to avoid sharing mutable defaults.
    response_format: Optional[Dict[str, Any]] = field(default_factory=lambda: {"type": "json_object"})


class CodeAgentNode(Node):
    """
    Code Agent Node:
    - Round 1: generate RTL from spec (GEN mode).
    - Round 2+: patch existing RTL using feedback (PATCH mode), and include the current RTL in prompt.
    """

    def __init__(self, *, llm_client: Optional[IFlowClient] = None, params: CodeAgentParams):
        super().__init__()
        self._llm_client = llm_client or IFlowClient()
        self._p = params
        self._root = Path(params.project_root).resolve()

    # ------------------------- PocketFlow hooks -------------------------

    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        flow_status = shared.setdefault("flow_status", {})
        flow_status["round"] = int(flow_status.get("round", 0)) + 1
        flow_status["last_stage"] = "code"
        round_no = int(flow_status["round"])

        spec = (shared.get("spec") or shared.get("user_query") or "").strip()
        if not spec:
            raise ValueError("shared['spec'] (or shared['user_query']) is required for CodeAgentNode.")

        rtl_files = shared.get("rtl_files")
        if rtl_files is None:
            rtl_files = self._auto_discover_rtl_files()

        # Ensure last-round generated/edited RTL is included in context (critical for PATCH mode)
        updated = shared.get("updated_rtl_files") or []
        for p in reversed(updated):
            if p and (p not in rtl_files):
                rtl_files.insert(0, p)

        review_fb = shared.get("review_feedback")
        verify_fb = shared.get("verify_feedback")

        rtl_context = self._read_files_with_context(rtl_files, max_files=self._p.max_files)
        feedback_text = self._format_feedback(review_fb, verify_fb)

        mode = "gen" if round_no == 1 else "patch"
        prompt = self._build_prompt(
            spec=spec,
            rtl_context=rtl_context,
            feedback_text=feedback_text,
            rtl_files=rtl_files,
            mode=mode,
        )

        return {
            "spec": spec,
            "rtl_files": rtl_files,
            "prompt": prompt,
            "has_feedback": bool(feedback_text.strip()),
            "round": round_no,
            "mode": mode,
        }

    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        print(f"[code] invoking LLM (temp={self._p.temperature}) ...")
        llm_kwargs: Dict[str, Any] = {}
        if self._p.response_format:
            llm_kwargs["response_format"] = self._p.response_format

        try:
            raw = self._llm_client.chat_completion(
                prep_res["prompt"],
                temperature=self._p.temperature,
                stream=False,
                **llm_kwargs,
            )
        except Exception as e:
            if self._p.response_format:
                print(f"[code] structured output call failed ({e}); retrying without response_format ...")
                raw = self._llm_client.chat_completion(
                    prep_res["prompt"],
                    temperature=self._p.temperature,
                    stream=False,
                )
            else:
                raise

        print(f"[code] LLM completed, raw length={len(raw)}")
        return {"raw": raw}

    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> Dict[str, Any]:
        raw = exec_res["raw"]
        shared["code_agent_output_raw"] = raw

        parsed = self._parse_llm_json(raw, strict=self._p.strict_json_only)
        files = parsed.get("files", [])
        notes = (parsed.get("notes") or "").strip()

        updated_paths: List[str] = []
        for f in files:
            rel = "TopModule.v"
            content = str(f.get("content") or "")
            if not rel:
                continue
            self._validate_target_path(rel)
            if self._p.forbid_tb_edit and self._looks_like_tb(rel):
                raise ValueError(f"TB edits are forbidden by params, but LLM attempted to edit: {rel}")
            print(f"[code] writing file: {rel} (len={len(content)})")
            self._write_text(rel, content)
            updated_paths.append(rel)

        shared["code_agent_notes"] = notes
        shared["updated_rtl_files"] = updated_paths

        shared["last_edit_summary"] = self._make_edit_summary(
            has_feedback=prep_res.get("has_feedback", False),
            updated_paths=updated_paths,
            notes=notes,
        )

        flow_status = shared.get("flow_status", {})
        round_no = flow_status.get("round")
        spec = (shared.get("spec") or "").strip()

        # Persist debug info to build/debug.log (include llm_prompt)
        try:
            debug_dir = (self._root / "build").resolve()
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_path = debug_dir / "debug.log"
            with debug_path.open("a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "stage": "code",
                            "round": round_no,
                            "mode": prep_res.get("mode"),
                            "spec": spec,
                            "updated_files": updated_paths,
                            "notes": notes,
                            "last_edit_summary": shared.get("last_edit_summary"),
                            "llm_prompt": prep_res.get("prompt", ""),
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                f.write("\n")
        except Exception:
            pass

        spec_short = spec.replace("\n", " ")
        spec_short = (spec_short[:80] + "...") if len(spec_short) > 80 else spec_short
        print(
            f"[code] round={round_no} mode={prep_res.get('mode')} spec=\"{spec_short}\" "
            f"files={len(updated_paths)} has_feedback={prep_res.get('has_feedback')}"
        )

        shared["code_status"] = {
            "stage": "code",
            "route": "next",
            "updated_rtl_files": updated_paths,
            "notes": notes,
        }
        return "next"

    # ------------------------- Prompting -------------------------

    def _build_prompt(
        self,
        *,
        spec: str,
        rtl_context: str,
        feedback_text: str,
        rtl_files: List[str],
        mode: str,
    ) -> str:
        rules = [
            "You are a senior RTL engineer.",
            "Goal: produce synthesizable Verilog/SystemVerilog that passes the given testbench.",
            "Do NOT modify testbench files.",
            "Keep module interface stable.",
            'Return ONLY valid JSON: {"files":[{"path":"...","content":"..."}],"notes":"..."} (no markdown).',
        ]
        if self._p.strict_json_only:
            rules.append("If you cannot comply with JSON-only output, still return JSON-only output.")

        existing_hint = "\n".join([f"- {p}" for p in rtl_files]) if rtl_files else "(none)"
        rtl_ctx = rtl_context.strip() or "(none)"
        fb = feedback_text.strip() or "(none)"

        if mode == "patch":
            return f"""\
SYSTEM RULES:
{chr(10).join(f"- {r}" for r in rules)}

TASK MODE:
- PATCH (do not rewrite from scratch). Make the smallest change that fixes the failures.

SPEC (source of truth):
{spec}

CURRENT RTL (authoritative; patch this code):
{rtl_ctx}

VERIFICATION FEEDBACK (what failed):
{fb}

PATCH GUIDANCE:
- Use the feedback to localize changes.
- If Hint lines show only some outputs mismatch, DO NOT change outputs that already have "no mismatches".
- Focus ONLY on the mismatched outputs/signals and keep other outputs identical.
- Ensure each output has a single driver (avoid double assigns / multiple always blocks driving same net).
- Pure combinational logic only (assign or always_comb), no latches.

OUTPUT REQUIREMENTS:
- Output ONLY JSON.
- Include ONLY the RTL files that you changed.
- Provide full file content for each changed file.
"""
        # GEN mode (Round 1)
        return f"""\
SYSTEM RULES:
{chr(10).join(f"- {r}" for r in rules)}

TASK MODE:
- GENERATE (write the required RTL from scratch based on SPEC). Keep it minimal and synthesizable.

SPEC:
{spec}

EXISTING RTL FILES (relative paths):
{existing_hint}

EXISTING RTL CONTENT (read-only context):
{rtl_ctx}

FEEDBACK FROM PREVIOUS ROUND:
{fb}

OUTPUT REQUIREMENTS:
- Output ONLY JSON.
- Include ONLY the RTL files that need to be created/updated.
- Each file's "content" must be a complete file (not a diff).
"""

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
            return "- No issues found.\n"
        issues = fb.get("issues") or []
        lines: List[str] = []
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

        lines: List[str] = []
        if fb.get("compile_passed") is False:
            for e in (fb.get("compile_errors") or [])[:50]:
                lines.append(f"- COMPILE_ERROR: {e.get('file')}:{e.get('line')} {e.get('message')}")

        for case in (fb.get("failed_cases") or [])[:50]:
            cname = case.get("case") or "<unknown>"
            lines.append(f"- FAIL_CASE: {cname} {case.get('message')}")

        tail = fb.get("raw_log_tail") or []
        if isinstance(tail, list) and tail:
            if fb.get("compile_passed") is False:
                # compile failed: raw_log_tail is compile tail -> include last N lines
                for s in tail[-20:]:
                    ss = str(s).strip()
                    if ss:
                        lines.append(f"- {ss}")
            else:
                # compile passed: include only Hint/Mismatches lines
                hint_lines = [
                    s for s in tail if str(s).strip().startswith(("Hint:", "Mismatches:"))
                ]
                for s in hint_lines[-30:]:
                    lines.append(f"- {str(s).strip()}")

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
