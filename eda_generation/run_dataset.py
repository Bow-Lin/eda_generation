from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import List, Optional, Tuple

from flow import build_flow, FlowParams
from utils.clients.iflow_client import IFlowClient


def _find_first(base_dir: Path, patterns: List[str]) -> Optional[Path]:
    for pat in patterns:
        cand = base_dir / pat
        if cand.exists():
            return cand
    return None


def _resolve_case_files(dataset_root: Path, case: str) -> Tuple[Path, Path, Path]:
    prompt = _find_first(dataset_root, [f"{case}_prompt", f"{case}_prompt.txt"])
    ref = _find_first(dataset_root, [f"{case}_ref.sv", f"{case}_ref.v", f"{case}_ref"])
    tb = _find_first(dataset_root, [f"{case}_test.sv", f"{case}_test.v", f"{case}_test"])

    missing = []
    if not prompt:
        missing.append("prompt")
    if not ref:
        missing.append("ref")
    if not tb:
        missing.append("test")
    if missing:
        raise FileNotFoundError(f"Case {case}: missing files: {', '.join(missing)}")

    return prompt, ref, tb


def _write_flist(path: Path, lines: List[str]) -> None:
    content = "\n".join(lines) + "\n"
    path.write_text(content, encoding="utf-8")


def run_case(
    *,
    case: str,
    dataset_root: Path,
    project_root: Path,
    results_root: Path,
    tb_top: str,
) -> None:
    prompt_path, ref_src, tb_src = _resolve_case_files(dataset_root, case)

    spec = prompt_path.read_text(encoding="utf-8")

    project_root.mkdir(parents=True, exist_ok=True)
    results_root.mkdir(parents=True, exist_ok=True)

    # Prepare working copies inside project_root (overwrite each case)
    dut_path = project_root / "TopModule.v"
    ref_path = project_root / ("RefModule" + ref_src.suffix)
    tb_path = project_root / ("tb" + tb_src.suffix)

    dut_path.write_text("", encoding="utf-8")  # reset/ensure exists
    shutil.copyfile(ref_src, ref_path)
    shutil.copyfile(tb_src, tb_path)

    # Flist per case (overwrite)
    rtl_review = project_root / "rtl_review.f"
    rtl_verify = project_root / "rtl_verify.f"
    tb_f = project_root / "tb.f"

    _write_flist(rtl_review, [dut_path.name])
    _write_flist(rtl_verify, [dut_path.name, ref_path.name])
    _write_flist(tb_f, [tb_path.name])

    flow = build_flow(
        llm_client=IFlowClient(),
        params=FlowParams(
            project_root=str(project_root),
            rtl_flist=str(rtl_review.name),
            review_rtl_flist=str(rtl_review.name),
            verify_rtl_flist=str(rtl_verify.name),
            tb_flist=str(tb_f.name),
            tb_top=tb_top,
            top_rtl="TopModule",
            max_rounds=3,
        ),
    )

    shared = {
        "spec": spec,
        "project_root": str(project_root),
    }
    flow.run(shared)

    # Save generated DUT (last attempt) to results_root
    if dut_path.exists():
        out_path = results_root / f"{case}{dut_path.suffix}"
        shutil.copyfile(dut_path, out_path)

    # Optional: also keep raw LLM output/notes per case for debugging
    raw = shared.get("code_agent_output_raw", "")
    if raw:
        (results_root / f"{case}.raw.json").write_text(raw, encoding="utf-8")

    notes = shared.get("code_agent_notes", "")
    if notes:
        (results_root / f"{case}.notes.txt").write_text(notes, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run dataset cases through the RTL generation/review/verify flow.")
    parser.add_argument("--dataset-root", default="/mnt/hdd/datasets/verilog-eval/dataset_spec-to-rtl", help="Dataset root containing problems.txt and per-case prompt/ref/test files.")
    parser.add_argument("--problems", default=None, help="Path to problems.txt (default: <dataset-root>/problems.txt)")
    parser.add_argument("--project-root", default="/home/eda/project/exp", help="Working project root (will be overwritten per case).")
    parser.add_argument("--results-root", default="/home/eda/project/exp/gen_result", help="Directory to store generated DUT per case.")
    parser.add_argument("--tb-top", default="tb", help="Testbench top module name for iverilog.")
    args = parser.parse_args()

    dataset_root = Path(args.dataset_root).expanduser().resolve()
    problems_path = Path(args.problems).expanduser().resolve() if args.problems else dataset_root / "problems.txt"
    project_root = Path(args.project_root).expanduser().resolve()
    results_root = Path(args.results_root).expanduser().resolve()

    cases = [line.strip() for line in problems_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not cases:
        raise SystemExit("No cases found in problems.txt")

    for idx, case in enumerate(cases, 1):
        print(f"===== [{idx}/{len(cases)}] case={case} =====")
        try:
            run_case(
                case=case,
                dataset_root=dataset_root,
                project_root=project_root,
                results_root=results_root,
                tb_top=args.tb_top,
            )
        except Exception as e:
            print(f"[error] case={case}: {e}")
            continue


if __name__ == "__main__":
    main()
