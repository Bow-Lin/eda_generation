from __future__ import annotations

import argparse
from pathlib import Path

from nodes.verification_agent import VerificationAgentNode, VerificationAgentParams


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run VerificationAgentNode once (iverilog/vvp) to check RTL functionality.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Project root (host path) that matches the container mount. Artifacts under <project_root>/build/verify.",
    )
    parser.add_argument(
        "--rtl-flist",
        default="rtl.f",
        help="RTL file list (relative to project_root or absolute).",
    )
    parser.add_argument(
        "--tb-flist",
        default="tb.f",
        help="Testbench file list (relative to project_root or absolute). Can include .sv files.",
    )
    parser.add_argument(
        "--tb-top",
        default="tb_top",
        help="Testbench top module name for iverilog -s.",
    )
    parser.add_argument(
        "--work-subdir",
        default="smoketest",
        help="Working directory under project_root for running iverilog/vvp.",
    )
    parser.add_argument(
        "--require-review-passed",
        action="store_true",
        help="If set, skip verify when review_feedback.passed is False or missing.",
    )
    parser.add_argument(
        "--iverilog-bin",
        default="iverilog",
        help="iverilog executable.",
    )
    parser.add_argument(
        "--vvp-bin",
        default="vvp",
        help="vvp executable.",
    )
    parser.add_argument(
        "--sv",
        action="store_true",
        help="Enable SystemVerilog flags (-g2012).",
    )
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    if not project_root.exists():
        raise SystemExit(f"project_root does not exist: {project_root}")

    compile_extra = ["-Wall"]
    if args.sv:
        compile_extra.insert(0, "-g2012")  # enable SystemVerilog

    params = VerificationAgentParams(
        project_root=str(project_root),
        rtl_flist=args.rtl_flist,
        tb_flist=args.tb_flist,
        tb_top=args.tb_top,
        work_subdir=args.work_subdir,
        out_dir="build/verify",
        sim_exe="simv",
        iverilog_bin=args.iverilog_bin,
        vvp_bin=args.vvp_bin,
        compile_extra_args=tuple(compile_extra),
        require_review_passed=args.require_review_passed,
    )

    node = VerificationAgentNode(params=params)

    shared = {
        "rtl_flist": args.rtl_flist,
        "top_rtl": None,  # not used here
        # Optional: include review_feedback if you want gating
        # "review_feedback": {"passed": True},
    }

    prep = node.prep(shared)
    exec_res = node.exec(prep)
    route = node.post(shared, prep, exec_res)

    fb = shared.get("verify_feedback", {})

    print(f"[route] {route}")
    print(f"[passed] {fb.get('passed')}")
    print(f"[compile_passed] {fb.get('compile_passed')}")
    print(f"[compile_errors] {len(fb.get('compile_errors', []))}")
    print(f"[failed_cases] {len(fb.get('failed_cases', []))}")
    print(f"[artifacts] {fb.get('artifacts')}")
    print("\n=== raw log tail ===")
    for line in fb.get("raw_log_tail", []):
        print(line)


if __name__ == "__main__":
    main()
