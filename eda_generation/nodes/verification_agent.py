from __future__ import annotations

import re
import subprocess
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pocketflow import Node


@dataclass
class VerificationAgentParams:
    project_root: str = "/home/project/xxproject"

    rtl_flist: str = "rtl.f"     # relative to project_root
    tb_flist: str = "tb.f"       # relative to project_root
    tb_top: str = "tb_top"       # testbench top module

    work_subdir: str = "smoketest"        # run iverilog/vvp under <project_root>/<work_subdir>
    out_dir: str = "build/verify"         # store artifacts under project_root/out_dir
    sim_exe: str = "simv"

    iverilog_bin: str = "iverilog"
    vvp_bin: str = "vvp"

    # Include SystemVerilog by default because most TBs use SV syntax.
    compile_extra_args: Tuple[str, ...] = ("-g2012", "-Wall")

    context_radius_lines: int = 2
    max_errors: int = 200
    max_failed_cases: int = 200
    raw_tail_lines: int = 200

    # Gate: only run verify when review passed
    require_review_passed: bool = True
    max_fail_attempts: int = 3
    max_rounds: int = 3


class VerificationAgentNode(Node):
    """
    Verification Agent (iverilog/vvp):
      - Compile RTL + TB
      - Run simulation
      - Parse failing cases from log
      - Produce shared["verify_feedback"]
    """

    def __init__(self, *, params: VerificationAgentParams):
        super().__init__()
        self._p = params
        self._root = Path(params.project_root).resolve()

    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        if self._p.require_review_passed:
            rf = shared.get("review_feedback")
            if isinstance(rf, dict) and rf.get("passed") is False:
                # Skip verification if review failed
                return {"skip": True, "reason": "review_failed"}
            if rf is None:
                # No review feedback present: still allow running if caller wants; but default gate requires it
                return {"skip": True, "reason": "missing_review_feedback"}

        out_dir = (self._root / self._p.out_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        workdir = (self._root / self._p.work_subdir).resolve()
        workdir.mkdir(parents=True, exist_ok=True)

        rtl_f = (self._root / self._p.rtl_flist).resolve()
        tb_f = (self._root / self._p.tb_flist).resolve()
        if not rtl_f.exists():
            raise FileNotFoundError(f"RTL flist not found: {rtl_f}")
        if not tb_f.exists():
            raise FileNotFoundError(f"TB flist not found: {tb_f}")

        simv_path = out_dir / self._p.sim_exe
        compile_log = out_dir / "sim_compile.log"
        run_log = out_dir / "sim_run.log"
        compile_error_log = out_dir / "compile_error.log"
        mismatch_case_log = out_dir / "mismatch_case.log"

        return {
            "skip": False,
            "workdir": str(workdir),
            "rtl_flist_abs": str(rtl_f),
            "tb_flist_abs": str(tb_f),
            "simv_path": str(simv_path),
            "compile_log": str(compile_log),
            "run_log": str(run_log),
            "compile_error_log": str(compile_error_log),
            "mismatch_case_log": str(mismatch_case_log),
        }

    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        if prep_res.get("skip"):
            return {"skipped": True, "reason": prep_res.get("reason")}

        # 1) compile
        print(f"[verify] compiling with iverilog (tb_top={self._p.tb_top}) ...")
        compile_cmd = [
            self._p.iverilog_bin,
            "-o",
            prep_res["simv_path"],
            "-s",
            self._p.tb_top,
            "-f",
            prep_res["rtl_flist_abs"],
            "-f",
            prep_res["tb_flist_abs"],
            *self._p.compile_extra_args,
        ]
        compile_out, compile_rc = self._run_cmd(compile_cmd, cwd=prep_res["workdir"])
        Path(prep_res["compile_log"]).write_text(compile_out, encoding="utf-8", errors="ignore")
        print(f"[verify] compile done rc={compile_rc}")

        if compile_rc != 0:
            # No run stage
            return {
                "skipped": False,
                "compile_rc": compile_rc,
                "compile_out": compile_out,
                "run_rc": None,
                "run_out": "",
            }

        # 2) run
        print("[verify] running vvp ...")
        run_cmd = [self._p.vvp_bin, prep_res["simv_path"]]
        run_out, run_rc = self._run_cmd(run_cmd, cwd=prep_res["workdir"])
        Path(prep_res["run_log"]).write_text(run_out, encoding="utf-8", errors="ignore")
        print(f"[verify] run done rc={run_rc}")

        return {
            "skipped": False,
            "compile_rc": compile_rc,
            "compile_out": compile_out,
            "run_rc": run_rc,
            "run_out": run_out,
        }

    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> Dict[str, Any]:
        if exec_res.get("skipped"):
            shared["verify_feedback"] = {
                "phase": "verify",
                "tool": "iverilog",
                "passed": False,
                "skipped": True,
                "reason": exec_res.get("reason"),
                "compile_passed": False,
                "compile_errors": [],
                "failed_cases": [],
                "artifacts": {},
                "raw_log_tail": [],
            }
            shared.setdefault("flow_status", {})["last_stage"] = "verify"
            shared.setdefault("verify_status", {})
            shared["verify_status"] = {
                "stage": "verify",
                "route": "verify_fail",
                "passed": False,
                "compile_passed": False,
                "compile_error_count": 0,
                "failed_case_count": 0,
                "attempts": int(shared.get("flow_status", {}).get("verify_attempts", 0)),
                "reason": exec_res.get("reason") or "skipped",
            }
            return "verify_fail"

        compile_out = exec_res.get("compile_out", "")
        run_out = exec_res.get("run_out", "")

        compile_errors = self._parse_compile_errors(compile_out)
        compile_passed = (exec_res.get("compile_rc", 1) == 0) and (len(compile_errors) == 0)

        failed_cases = []
        if compile_passed:
            failed_cases = self._parse_failed_cases(run_out)

        passed = compile_passed and (exec_res.get("run_rc", 1) == 0) and (len(failed_cases) == 0)

        feedback = {
            "phase": "verify",
            "tool": "iverilog",
            "passed": passed,
            "skipped": False,
            "compile_passed": compile_passed,
            "compile_errors": compile_errors[: self._p.max_errors],
            "failed_cases": failed_cases[: self._p.max_failed_cases],
            "artifacts": {
                "simv": prep_res.get("simv_path"),
                "compile_log": prep_res.get("compile_log"),
                "run_log": prep_res.get("run_log"),
                "compile_error_log": prep_res.get("compile_error_log"),
                "mismatch_case_log": prep_res.get("mismatch_case_log"),
            },
            "raw_log_tail": (run_out.splitlines()[-self._p.raw_tail_lines :] if run_out else compile_out.splitlines()[-self._p.raw_tail_lines :]),
        }

        shared["verify_feedback"] = feedback

        flow_status = shared.setdefault("flow_status", {})

        attempts = int(flow_status.get("verify_attempts", 0))
        if passed:
            attempts = 0
        else:
            attempts += 1

        route = "verify_ok" if passed else "verify_fail"
        reason = "verify_ok"

        if not passed and attempts >= self._p.max_fail_attempts:
            route = "abort"
            reason = "verify_fail_limit_reached"
        elif not passed:
            reason = "verify_fail"

        round_cnt = int(flow_status.get("round", 0))
        if self._p.max_rounds and round_cnt > self._p.max_rounds:
            route = "abort"
            reason = "max_rounds_reached"

        flow_status["verify_attempts"] = attempts
        flow_status["last_reason"] = reason
        flow_status["last_stage"] = "verify"

        shared["verify_status"] = {
            "stage": "verify",
            "route": route,
            "passed": passed,
            "compile_passed": compile_passed,
            "compile_error_count": len(feedback.get("compile_errors", [])),
            "failed_case_count": len(feedback.get("failed_cases", [])),
            "attempts": attempts,
            "reason": reason,
        }

        # Concise print
        spec = (shared.get("spec") or "").strip().replace("\n", " ")
        spec_short = (spec[:80] + "...") if len(spec) > 80 else spec
        print(
            f"[verify] round={shared.get('flow_status', {}).get('round')} spec=\"{spec_short}\" "
            f"passed={passed} compile_passed={compile_passed} "
            f"compile_errors={len(feedback.get('compile_errors', []))} "
            f"failed_cases={len(feedback.get('failed_cases', []))}"
        )

        # Persist debug info
        try:
            debug_dir = (self._root / self._p.out_dir).resolve()
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_path = debug_dir / "debug.log"
            with debug_path.open("a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "stage": "verify",
                            "round": shared.get("flow_status", {}).get("round"),
                            "spec": spec,
                            "passed": passed,
                            "route": route,
                            "compile_passed": compile_passed,
                            "compile_errors": feedback.get("compile_errors", []),
                            "failed_cases": feedback.get("failed_cases", []),
                            "artifacts": feedback.get("artifacts"),
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                f.write("\n")
        except Exception:
            pass

        # Persist concise error summaries for quick inspection.
        try:
            if (not compile_passed) and prep_res.get("compile_error_log"):
                err_lines: List[str] = []
                if compile_errors:
                    for e in compile_errors[: self._p.max_errors]:
                        loc = f"{e.get('file')}:{e.get('line')}" if e.get("file") else ""
                        msg = e.get("message") or ""
                        err_lines.append(f"{loc} {msg}".strip())
                else:
                    err_lines = compile_out.splitlines()
                Path(prep_res["compile_error_log"]).write_text("\n".join(err_lines), encoding="utf-8")

            if failed_cases and prep_res.get("mismatch_case_log"):
                mm_lines: List[str] = []
                for c in failed_cases[: self._p.max_failed_cases]:
                    name = c.get("case") or "<unknown>"
                    msg = c.get("message") or c.get("raw") or ""
                    mm_lines.append(f"{name}: {msg}")
                # If nothing was parsed but run_out had content, fall back to run_out.
                if not mm_lines and run_out:
                    mm_lines = run_out.splitlines()
                Path(prep_res["mismatch_case_log"]).write_text("\n".join(mm_lines), encoding="utf-8")
        except Exception:
            pass

        return route

    # ------------------------- Parsing -------------------------

    def _parse_compile_errors(self, compile_out: str) -> List[Dict[str, Any]]:
        """
        Typical iverilog errors:
          path/to/file.v:123: error: <message>
          path/to/file.v:45: syntax error
        """
        errs: List[Dict[str, Any]] = []
        for line in compile_out.splitlines():
            s = line.strip()
            if not s:
                continue

            # file:line: error: msg
            m = re.match(r"^(?P<file>.*?):(?P<line>\d+):\s*(?P<kind>error|ERROR)\s*:\s*(?P<msg>.*)$", s)
            if m:
                f = m.group("file")
                ln = int(m.group("line"))
                msg = m.group("msg")
                errs.append(
                    {
                        "severity": "Error",
                        "file": f,
                        "line": ln,
                        "message": msg,
                        "context": self._read_context(f, ln, self._p.context_radius_lines),
                    }
                )
                continue

            # file:line: syntax error
            m2 = re.match(r"^(?P<file>.*?):(?P<line>\d+):\s*(?P<msg>syntax error.*)$", s, flags=re.IGNORECASE)
            if m2:
                f = m2.group("file")
                ln = int(m2.group("line"))
                msg = m2.group("msg")
                errs.append(
                    {
                        "severity": "Error",
                        "file": f,
                        "line": ln,
                        "message": msg,
                        "context": self._read_context(f, ln, self._p.context_radius_lines),
                    }
                )
                continue

            # keep other lines that look severe
            if "error" in s.lower():
                errs.append({"severity": "Error", "file": "", "line": None, "message": s, "context": []})

        return errs

    def _parse_failed_cases(self, run_out: str) -> List[Dict[str, Any]]:
        """
        Compatible patterns:
          - "CASE <name> FAIL: ..."
          - "CASE <name> PASS"
          - "ASSERT FAIL: ..."
          - generic: "FAIL:" / "ERROR:" lines
          - Standardized summary lines like "Mismatches: X in Y samples"
        """
        failed: List[Dict[str, Any]] = []

        # If we have a standardized mismatch summary, use it directly.
        mm_cnt = self._extract_mismatch_count(run_out)
        if mm_cnt is not None:
            if mm_cnt == 0:
                return []
            failed.append(
                {
                    "case": "mismatch_total",
                    "message": f"Mismatches reported: {mm_cnt}",
                    "signals": [],
                    "expected_behavior": None,
                    "raw": f"mismatch_total={mm_cnt}",
                }
            )

            # Also capture individual sample mismatches if present.
            sample_pat = re.compile(r"Sample\\s+(?P<idx>\\d+)\\s+mismatch\\s*:\\s*(?P<msg>.*)$", re.IGNORECASE)
            for line in run_out.splitlines():
                m = sample_pat.search(line)
                if not m:
                    continue
                idx = m.group("idx")
                msg = m.group("msg").strip()
                failed.append(
                    {
                        "case": f"sample_{idx}",
                        "message": msg,
                        "signals": self._extract_signals(line),
                        "expected_behavior": self._extract_expected_behavior(line),
                        "raw": line.strip(),
                    }
                )
            return failed

        # CASE xxx FAIL:
        case_fail = re.compile(r"CASE\s+(?P<name>\S+)\s+FAIL\s*:\s*(?P<msg>.*)$", re.IGNORECASE)
        # ASSERT FAIL:
        assert_fail = re.compile(r"ASSERT\s+FAIL\s*:\s*(?P<msg>.*)$", re.IGNORECASE)

        for line in run_out.splitlines():
            s = line.strip()
            if not s:
                continue

            # Ignore lines that explicitly indicate zero mismatches.
            if "no mismatches" in s.lower() or re.search(r"mismatch(es)?\s*:\s*0", s, re.IGNORECASE):
                continue

            m = case_fail.search(s)
            if m:
                failed.append(
                    {
                        "case": m.group("name"),
                        "message": m.group("msg"),
                        "signals": self._extract_signals(s),
                        "expected_behavior": self._extract_expected_behavior(s),
                        "raw": s,
                    }
                )
                continue

            m2 = assert_fail.search(s)
            if m2:
                failed.append(
                    {
                        "case": None,
                        "message": m2.group("msg"),
                        "signals": self._extract_signals(s),
                        "expected_behavior": self._extract_expected_behavior(s),
                        "raw": s,
                    }
                )
                continue

            # fallback: lines that smell like failure
            if any(k in s.lower() for k in (" fail", "fail:", "error:", "mismatch", "expected", "got=")):
                failed.append(
                    {
                        "case": None,
                        "message": s,
                        "signals": self._extract_signals(s),
                        "expected_behavior": self._extract_expected_behavior(s),
                        "raw": s,
                    }
                )

        # de-dup exact raw lines
        uniq = []
        seen = set()
        for it in failed:
            key = it.get("raw", it.get("message", ""))
            if key in seen:
                continue
            seen.add(key)
            uniq.append(it)
        return uniq

    def _extract_mismatch_count(self, run_out: str) -> Optional[int]:
        """
        Parse standardized mismatch summary lines. Examples:
          "Mismatches: 0 in 20 samples"
          "Hint: Total mismatched samples is 0 out of 20 samples"
        Returns an int when found, otherwise None.
        """
        pats = [
            re.compile(r"Mismatches?\s*:\s*(\d+)", re.IGNORECASE),
            re.compile(r"Total\s+mismatched\s+samples\s+is\s+(\d+)", re.IGNORECASE),
        ]
        for pat in pats:
            m = pat.search(run_out)
            if m:
                try:
                    return int(m.group(1))
                except Exception:
                    continue
        return None

    def _extract_signals(self, text: str) -> List[str]:
        # Heuristic: capture identifiers near known markers
        # Examples: "shift_ena should be 0" => shift_ena
        sigs = set()

        for m in re.finditer(r"\b([a-zA-Z_]\w*)\b", text):
            tok = m.group(1)
            # skip common words
            if tok.lower() in {"case", "fail", "pass", "assert", "exp", "got", "should", "be", "after", "cycles", "at", "t"}:
                continue
            # filter overly short tokens
            if len(tok) <= 1:
                continue
            sigs.add(tok)

        # keep order-ish by appearance
        ordered: List[str] = []
        for m in re.finditer(r"\b([a-zA-Z_]\w*)\b", text):
            tok = m.group(1)
            if tok in sigs and tok not in ordered:
                ordered.append(tok)

        return ordered[:8]

    def _extract_expected_behavior(self, text: str) -> Optional[str]:
        # Heuristic: if line contains "should ..." or "expected ..."
        m = re.search(r"(should\s+.*)$", text, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
        m2 = re.search(r"(expected\s+.*)$", text, flags=re.IGNORECASE)
        if m2:
            return m2.group(1).strip()
        return None

    # ------------------------- File context -------------------------

    def _read_context(self, file_path: str, line: int, radius: int) -> List[str]:
        p = Path(file_path)
        if not p.is_absolute():
            p = (self._root / p).resolve()
        if not p.exists():
            return []

        lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        idx = max(1, line) - 1
        lo = max(0, idx - radius)
        hi = min(len(lines), idx + radius + 1)
        out = []
        for i in range(lo, hi):
            out.append(f"{i+1}: {lines[i]}")
        return out

    # ------------------------- Command runner -------------------------

    def _run_cmd(self, cmd: List[str], *, cwd: Optional[str] = None) -> tuple[str, int]:
        p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return p.stdout, p.returncode
