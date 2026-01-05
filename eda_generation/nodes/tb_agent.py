from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pocketflow import Node
from utils.clients.iflow_client import IFlowClient
from utils.prompt_loader import load_prompt_template


@dataclass
class TbAgentParams:
    project_root: str
    tb_dir: str = "tb"
    rtl_dir: str = "rtl"
    allowed_exts: Tuple[str, ...] = (".v", ".sv")
    temperature: float = 0.2
    max_files: int = 32
    output_mode: str = "json_files"
    forbid_rtl_edit: bool = True
    strict_json_only: bool = True
    include_rtl_context: bool = True
    response_format: Optional[Dict[str, Any]] = field(default_factory=lambda: {"type": "json_object"})


class TbAgentNode(Node):
    """
    Testbench Agent Node:
    - Generate a self-checking testbench from spec (GEN mode).
    - By default, only generates once and skips if TB already exists.
    """

    def __init__(self, *, llm_client: Optional[IFlowClient] = None, params: TbAgentParams):
        super().__init__()
        self._llm_client = llm_client or IFlowClient()
        self._p = params
        self._root = Path(params.project_root).resolve()

    # ------------------------- PocketFlow hooks -------------------------

    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        flow_status = shared.setdefault("flow_status", {})
        flow_status["last_stage"] = "tb"
        round_no = int(flow_status.get("round", 0))

        spec = (shared.get("spec") or shared.get("user_query") or "").strip()
        if not spec:
            raise ValueError("shared['spec'] (or shared['user_query']) is required for TbAgentNode.")

        tb_files = shared.get("tb_files")
        if tb_files is None:
            tb_files = self._auto_discover_tb_files()

        updated = shared.get("updated_tb_files") or []
        for p in reversed(updated):
            if p and (p not in tb_files):
                tb_files.insert(0, p)

        rtl_files = shared.get("rtl_files")
        if rtl_files is None:
            rtl_files = self._auto_discover_rtl_files()

        tb_context = self._read_files_with_context(tb_files, max_files=self._p.max_files)
        rtl_context = (
            self._read_files_with_context(rtl_files, max_files=self._p.max_files)
            if self._p.include_rtl_context
            else ""
        )

        verify_fb = shared.get("verify_feedback")
        force_regen = bool(shared.get("tb_regen_on_fail")) and isinstance(verify_fb, dict) and verify_fb.get("passed") is False
        should_skip = bool(tb_files) and (round_no > 1 or shared.get("tb_generated"))
        if force_regen:
            should_skip = False

        top_rtl = shared.get("top_rtl") or "TopModule"
        tb_top = shared.get("tb_top") or "tb"

        prompt = self._build_prompt(
            spec=spec,
            rtl_context=rtl_context,
            tb_context=tb_context,
            top_rtl=top_rtl,
            tb_top=tb_top,
        )

        return {
            "skip": should_skip,
            "spec": spec,
            "rtl_files": rtl_files,
            "tb_files": tb_files,
            "prompt": prompt,
            "round": round_no,
            "top_rtl": top_rtl,
            "tb_top": tb_top,
        }

    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        if prep_res.get("skip"):
            return {"skipped": True, "raw": ""}

        print(f"[tb] invoking LLM (temp={self._p.temperature}) ...")
        raw = self._call_llm(prep_res["prompt"])

        print(f"[tb] LLM completed, raw length={len(raw)}")
        return {"skipped": False, "raw": raw}

    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> Dict[str, Any]:
        if exec_res.get("skipped"):
            shared["tb_status"] = {
                "stage": "tb",
                "route": "next",
                "skipped": True,
                "reason": "tb_exists_or_round_gt_1",
            }
            shared["tb_generated"] = True
            return "next"

        raw = exec_res["raw"]
        shared["tb_agent_output_raw"] = raw

        parsed = None
        attempt = 0
        while True:
            try:
                parsed = self._parse_llm_json(raw, strict=self._p.strict_json_only)
                notes_val = parsed.get("notes")
                if notes_val is not None and not isinstance(notes_val, str):
                    raise ValueError("LLM JSON 'notes' must be a string.")
                files_val = parsed.get("files", [])
                if not isinstance(files_val, list):
                    raise ValueError("LLM JSON 'files' must be a list.")
                break
            except Exception as e:
                attempt += 1
                if attempt > 1:
                    raise
                print(f"[tb] parse failed ({e}); retrying LLM once ...")
                raw = self._call_llm(prep_res["prompt"])
                shared["tb_agent_output_raw"] = raw

        files = parsed.get("files", [])
        notes = (parsed.get("notes") or "").strip()

        updated_paths: List[str] = []
        for f in files:
            rel = str(f.get("path") or f"{self._p.tb_dir}/{prep_res['tb_top']}.sv")
            content = str(f.get("content") or "")
            if not rel:
                continue
            self._validate_target_path(rel)
            if self._p.forbid_rtl_edit and not self._looks_like_tb(rel):
                raise ValueError(f"TB agent attempted to edit a non-TB file: {rel}")
            print(f"[tb] writing file: {rel} (len={len(content)})")
            self._write_text(rel, content)
            updated_paths.append(rel)

        shared["tb_agent_notes"] = notes
        shared["updated_tb_files"] = updated_paths
        shared["tb_generated"] = True

        flow_status = shared.get("flow_status", {})
        round_no = flow_status.get("round")
        spec = (shared.get("spec") or "").strip()

        try:
            debug_dir = (self._root / "build").resolve()
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_path = debug_dir / "debug.log"
            with debug_path.open("a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "stage": "tb",
                            "round": round_no,
                            "spec": spec,
                            "updated_files": updated_paths,
                            "notes": notes,
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
        print(f"[tb] round={round_no} spec=\"{spec_short}\" files={len(updated_paths)}")

        shared["tb_status"] = {
            "stage": "tb",
            "route": "next",
            "updated_tb_files": updated_paths,
            "notes": notes,
        }
        return "next"

    def _call_llm(self, prompt: str) -> str:
        llm_kwargs: Dict[str, Any] = {}
        if self._p.response_format:
            llm_kwargs["response_format"] = self._p.response_format

        try:
            return self._llm_client.chat_completion(
                prompt,
                temperature=self._p.temperature,
                stream=False,
                **llm_kwargs,
            )
        except Exception as e:
            if self._p.response_format:
                print(f"[tb] structured output call failed ({e}); retrying without response_format ...")
                return self._llm_client.chat_completion(
                    prompt,
                    temperature=self._p.temperature,
                    stream=False,
                )
            raise

    # ------------------------- Prompting -------------------------

    def _build_prompt(
        self,
        *,
        spec: str,
        rtl_context: str,
        tb_context: str,
        top_rtl: str,
        tb_top: str,
    ) -> str:
        strict_rule = ""
        if self._p.strict_json_only:
            strict_rule = "- If you cannot comply with JSON-only output, still return JSON-only output."
        rtl_ctx = rtl_context.strip() or "(none)"
        tb_ctx = tb_context.strip() or "(none)"

        template = load_prompt_template("tb_agent.txt")
        return template.format(
            strict_rule=strict_rule,
            spec=spec,
            rtl_ctx=rtl_ctx,
            tb_ctx=tb_ctx,
            tb_top=tb_top,
            top_rtl=top_rtl,
        )

    # ------------------------- File IO -------------------------

    def _auto_discover_tb_files(self) -> List[str]:
        tb_root = (self._root / self._p.tb_dir).resolve()
        if not tb_root.exists():
            return []
        out: List[str] = []
        for p in tb_root.rglob("*"):
            if p.is_file() and p.suffix in self._p.allowed_exts:
                rel = str(p.relative_to(self._root)).replace("\\", "/")
                out.append(rel)
        out.sort()
        return out

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
            raise ValueError(f"Disallowed file extension for TB write: {rel_path}")

    def _looks_like_tb(self, rel_path: str) -> bool:
        p = rel_path.lower()
        if f"/{self._p.tb_dir.lower()}/" in p:
            return True
        return (
            "tb" in Path(rel_path).stem.lower()
            or p.endswith("_tb.v")
            or p.endswith("_tb.sv")
            or p.endswith(".tb.v")
            or p.endswith(".tb.sv")
        )

    # ------------------------- LLM output parsing -------------------------

    def _parse_llm_json(self, raw: str, *, strict: bool) -> Dict[str, Any]:
        text = raw.strip()
        if strict:
            return json.loads(text)

        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not m:
            raise ValueError("LLM output is not JSON and no JSON object found.")
        return json.loads(m.group(0))
