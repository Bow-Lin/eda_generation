from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from pocketflow import Node


@dataclass
class ReviewAgentParams:
    project_root: str = "/home/project/xxproject"

    container_name: str = "spyglass-centos7"
    docker_bin: str = "docker"

    work_subdir: str = "."          # run SpyGlass under <project_root>/<work_subdir>
    rtl_flist: str = "rtl.f"                # relative to project_root (or absolute)
    top_rtl: str = "top"

    goal: str = "lint/lint_rtl"

    out_dir: str = "build/review"           # relative to project_root
    tcl_name: str = "run_sg_review.tcl"
    errors_name: str = "review_errors.txt"
    warnings_name: str = "review_warnings.txt"
    raw_log_name: str = "review_spyglass.log"

    context_radius_lines: int = 2
    max_issues: int = 200
    raw_tail_lines: int = 120
    max_fail_attempts: int = 3
    max_rounds: int = 3


class ReviewAgentNode(Node):
    """
    Review Agent (SpyGlass in Docker):
      1) Run SpyGlass lint on RTL
      2) Parse reports/logs
      3) Write shared["review_feedback"]
    """

    def __init__(self, *, params: ReviewAgentParams):
        super().__init__()
        self._p = params
        self._root = Path(params.project_root).resolve()

    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        rtl_flist = shared.get("rtl_flist", self._p.rtl_flist)
        top_rtl = shared.get("top_rtl", self._p.top_rtl)

        out_dir = self._root / self._p.out_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        tcl_path = out_dir / self._p.tcl_name
        errors_path = out_dir / self._p.errors_name
        warnings_path = out_dir / self._p.warnings_name
        raw_log_path = out_dir / self._p.raw_log_name

        rtl_flist_abs = str((self._root / rtl_flist).resolve()) if not Path(rtl_flist).is_absolute() else rtl_flist

        tcl_text = self._build_tcl(
            rtl_flist_abs=rtl_flist_abs,
            top_rtl=top_rtl,
            goal=self._p.goal,
            errors_abs=str(errors_path),
            warnings_abs=str(warnings_path),
        )

        return {
            "rtl_flist_abs": rtl_flist_abs,
            "top_rtl": top_rtl,
            "tcl_path": str(tcl_path),
            "tcl_text": tcl_text,
            "errors_path": str(errors_path),
            "warnings_path": str(warnings_path),
            "raw_log_path": str(raw_log_path),
            "container_workdir": str((self._root / self._p.work_subdir).resolve()),
        }

    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        Path(prep_res["tcl_path"]).write_text(prep_res["tcl_text"], encoding="utf-8")

        print(f"[review] starting docker start + spyglass (tcl={prep_res['tcl_path']})...")
        start_out, start_rc = self._run_cmd([self._p.docker_bin, "start", self._p.container_name])

        # Because host path == container path under /home/project mount, we can pass absolute tcl path directly.
        tcl_abs = prep_res["tcl_path"]
        workdir_abs = prep_res["container_workdir"]

        cmd = [
            self._p.docker_bin,
            "exec",
            "-w",
            workdir_abs,
            self._p.container_name,
            "bash",
            "-lc",
            f"spyglass -shell -tcl {tcl_abs}",
        ]
        out, rc = self._run_cmd(cmd)
        print(f"[review] spyglass finished rc={rc}")

        raw = []
        raw.append("=== docker start ===")
        raw.append(start_out.strip())
        raw.append("=== spyglass run ===")
        raw.append(out.strip())
        raw_log = "\n".join([x for x in raw if x])

        Path(prep_res["raw_log_path"]).write_text(raw_log, encoding="utf-8", errors="ignore")

        return {"raw_log": raw_log, "returncode": rc, "start_rc": start_rc}

    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> Dict[str, Any]:
        err_text = self._read_text(prep_res["errors_path"])
        warn_text = self._read_text(prep_res["warnings_path"])

        issues: List[Dict[str, Any]] = []
        issues.extend(self._parse_report(err_text))
        issues.extend(self._parse_report(warn_text))

        if not issues:
            issues = self._parse_log(exec_res.get("raw_log", ""))

        for it in issues:
            f = it.get("file")
            ln = it.get("line")
            if f and isinstance(ln, int) and ln > 0:
                it["context"] = self._read_context(f, ln, self._p.context_radius_lines)

        has_error = any(str(x.get("severity", "")).lower() in ("fatal", "error") for x in issues)
        passed = (not has_error) and (exec_res.get("returncode", 0) == 0)

        if exec_res.get("returncode", 0) != 0 and not has_error:
            issues.insert(
                0,
                {
                    "severity": "Error",
                    "file": "",
                    "line": None,
                    "message": f"SpyGlass command returned non-zero exit code: {exec_res.get('returncode')}",
                    "rule_id": None,
                    "context": [],
                },
            )

        feedback = {
            "phase": "review",
            "tool": "spyglass(docker)",
            "passed": passed,
            "issues": issues[: self._p.max_issues],
            "artifacts": {
                "tcl": prep_res["tcl_path"],
                "errors": prep_res["errors_path"],
                "warnings": prep_res["warnings_path"],
                "raw_log": prep_res["raw_log_path"],
            },
            "raw_log_tail": exec_res.get("raw_log", "").splitlines()[-self._p.raw_tail_lines :],
        }

        shared["review_feedback"] = feedback
        flow_status = shared.setdefault("flow_status", {})

        attempts = int(flow_status.get("review_attempts", 0))
        if passed:
            attempts = 0
        else:
            attempts += 1

        route = "syntax_ok" if passed else "syntax_fail"
        reason = "syntax_ok"

        if not passed and attempts >= self._p.max_fail_attempts:
            route = "abort"
            reason = "review_fail_limit_reached"
        elif not passed:
            reason = "syntax_fail"

        round_cnt = int(flow_status.get("round", 0))
        if self._p.max_rounds and round_cnt > self._p.max_rounds:
            route = "abort"
            reason = "max_rounds_reached"

        flow_status["review_attempts"] = attempts
        flow_status["last_reason"] = reason
        flow_status["last_stage"] = "review"

        shared["review_status"] = {
            "stage": "review",
            "route": route,
            "passed": passed,
            "error_count": sum(1 for x in issues if str(x.get("severity", "")).lower() in ("fatal", "error")),
            "warning_count": sum(1 for x in issues if str(x.get("severity", "")).lower() == "warning"),
            "attempts": attempts,
            "reason": reason,
        }

        return route

    def _build_tcl(
        self,
        *,
        rtl_flist_abs: str,
        top_rtl: str,
        goal: str,
        errors_abs: str,
        warnings_abs: str,  # unused (kept for signature compatibility)
    ) -> str:
        # We only care about Error/Fatal. Parse SpyGlass moresimple.rpt blocks.
        all_rpt_abs = f"{errors_abs}.moresimple.rpt"

        return "\n".join(
            [
                "new_project review_proj -force",
                f'set fp [open "{rtl_flist_abs}" r]',
                "set flist_raw [read $fp]",
                "close $fp",
                "set files {}",
                'foreach line [split $flist_raw "\\n"] {',
                "    set s [string trim $line]",
                '    if {$s eq ""} { continue }',
                '    if {[string first "#" $s] == 0} { continue }',
                "    lappend files $s",
                "}",
                "read_file -type verilog $files",
                f'set_option top "{top_rtl}"',
                f"current_goal {goal}",
                "run_goal",

                # Locate moresimple report in consolidated_reports
                f'set __TOP "{top_rtl}"',
                'set __GOAL [string map {"/" "_"} "' + goal + '"]',
                'set __RPT_DIR [file normalize [format "./review_proj/consolidated_reports/%s_%s" $__TOP $__GOAL]]',
                'set __RPT [file join $__RPT_DIR "moresimple.rpt"]',

                f'set __ERR "{errors_abs}"',
                f'set __COPY "{all_rpt_abs}"',

                # Hard fail if report missing
                'if {![file exists $__RPT]} { error [format "Expected report not found: %s" $__RPT] }',

                # Optional: keep a copy of the report next to error output for debugging
                'file copy -force $__RPT $__COPY',

                # Write only Error/Fatal message blocks to $__ERR
                "proc __flush_err_block {block sev err_f} {",
                "    set s [string tolower $sev]",
                '    if {$s eq "error" || $s eq "fatal"} {',
                "        puts $err_f $block",
                "    }",
                "}",

                "proc __extract_errors_from_moresimple {src err_dst} {",
                "    set in [open $src r]",
                "    set err_f [open $err_dst w]",
                "    set cur \"\"",
                "    set cur_sev \"\"",
                "    while {[gets $in line] >= 0} {",
                "        # Each message record starts with [ID] (e.g., [D], [7], [0])",
                "        if {[regexp {^\\[[^]]+\\]} $line]} {",
                "            if {$cur ne \"\"} { __flush_err_block $cur $cur_sev $err_f }",
                "            set cur $line",
                "            append cur \"\\n\"",
                "            # Severity is on the first line; file path may be wrapped later",
                "            if {[regexp {\\s(Fatal|Error|Warning|Info)\\s+\\S+} $line -> sev]} {",
                "                set cur_sev $sev",
                "            } else {",
                "                set cur_sev \"\"",
                "            }",
                "        } else {",
                "            if {$cur ne \"\"} {",
                "                append cur $line",
                "                append cur \"\\n\"",
                "            }",
                "        }",
                "    }",
                "    if {$cur ne \"\"} { __flush_err_block $cur $cur_sev $err_f }",
                "    close $in",
                "    close $err_f",
                "}",

                "__extract_errors_from_moresimple $__RPT $__ERR",

                "exit -force",
                "",
            ]
        )


    def _parse_report(self, text: str) -> List[Dict[str, Any]]:
        if not text.strip():
            return []

        issues: List[Dict[str, Any]] = []

        patterns = [
            # Error: msg (file:line)
            re.compile(r"^(?P<sev>Error|Fatal|Warning)\s*:\s*(?P<msg>.*?)\s*\((?P<file>.*?):(?P<line>\d+)\)\s*$"),
            # file:line: Error: msg
            re.compile(r"^(?P<file>.*?):(?P<line>\d+)\s*:\s*(?P<sev>Error|Fatal|Warning)\s*:\s*(?P<msg>.*)$"),
            # Error: msg - file:line
            re.compile(r"^(?P<sev>Error|Fatal|Warning)\s*:\s*(?P<msg>.*?)\s*-\s*(?P<file>.*?):(?P<line>\d+)\s*$"),
        ]

        for raw in text.splitlines():
            s = raw.strip()
            if not s:
                continue

            matched = False
            for pat in patterns:
                m = pat.match(s)
                if not m:
                    continue
                d = m.groupdict()
                issues.append(
                    {
                        "severity": d.get("sev", "Error"),
                        "file": d.get("file", ""),
                        "line": int(d["line"]) if d.get("line") else None,
                        "message": d.get("msg", s),
                        "rule_id": None,
                        "context": [],
                    }
                )
                matched = True
                break

            if not matched and s.lower().startswith(("error", "fatal", "warning")):
                issues.append(
                    {
                        "severity": "Error",
                        "file": "",
                        "line": None,
                        "message": s,
                        "rule_id": None,
                        "context": [],
                    }
                )

        return issues

    def _parse_log(self, raw_log: str) -> List[Dict[str, Any]]:
        if not raw_log.strip():
            return []
        issues: List[Dict[str, Any]] = []

        pat = re.compile(
            r"(?P<sev>Error|Fatal|Warning).*?(?P<file>[^ \t:()]+?\.(v|sv)):(?P<line>\d+)",
            re.IGNORECASE,
        )
        for line in raw_log.splitlines():
            m = pat.search(line)
            if not m:
                continue
            issues.append(
                {
                    "severity": m.group("sev").capitalize(),
                    "file": m.group("file"),
                    "line": int(m.group("line")),
                    "message": line.strip(),
                    "rule_id": None,
                    "context": [],
                }
            )
        return issues

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

        out: List[str] = []
        for i in range(lo, hi):
            out.append(f"{i+1}: {lines[i]}")
        return out

    def _read_text(self, abs_path: str) -> str:
        p = Path(abs_path)
        if not p.exists():
            return ""
        return p.read_text(encoding="utf-8", errors="ignore")

    def _run_cmd(self, cmd: List[str]) -> tuple[str, int]:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return p.stdout, p.returncode
