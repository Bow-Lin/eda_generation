from __future__ import annotations

import argparse
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from nodes.code_agent import CodeAgentNode, CodeAgentParams
from pocketflow import Flow, Node
from nodes.tb_agent import TbAgentNode, TbAgentParams
from nodes.verification_agent import VerificationAgentNode, VerificationAgentParams
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


class _FinishNode(Node):
    def prep(self, shared):
        return shared or {}

    def exec(self, shared):
        shared.setdefault("flow_status", {})
        shared["flow_status"]["done"] = True
        shared["flow_status"]["last_stage"] = "finish"
        shared["flow_status"].setdefault("last_reason", "finished")
        return "done"


class _CodeAgentNodeWithAttempt(CodeAgentNode):
    def __init__(self, *, llm_client: IFlowClient, params: CodeAgentParams, max_attempts: int):
        super().__init__(llm_client=llm_client, params=params)
        self._max_attempts = max_attempts

    def prep(self, shared: dict) -> dict:
        prep_res = super().prep(shared)
        round_no = int(shared.get("flow_status", {}).get("round", 0))
        case = shared.get("case", "")
        print(f"[gen-tb] attempt={round_no}/{self._max_attempts} case={case}")
        return prep_res


def _rel_to_project(project_root: Path, target: Path) -> str:
    return Path(os.path.relpath(target, start=project_root)).as_posix()


def _build_gen_flow(
    *,
    llm_client: IFlowClient,
    project_root: Path,
    tb_top: str,
    rtl_flist: str,
    tb_flist: str,
    verify_out_dir: str,
    max_attempts: int,
) -> Flow:
    code_agent = _CodeAgentNodeWithAttempt(
        llm_client=llm_client,
        params=CodeAgentParams(project_root=str(project_root)),
        max_attempts=max_attempts,
    )
    tb_agent = TbAgentNode(
        llm_client=llm_client,
        params=TbAgentParams(project_root=str(project_root), tb_dir="tb"),
    )
    verify_agent = VerificationAgentNode(
        params=VerificationAgentParams(
            project_root=str(project_root),
            rtl_flist=rtl_flist,
            tb_flist=tb_flist,
            tb_top=tb_top,
            work_subdir=".",
            out_dir=verify_out_dir,
            require_review_passed=False,
            max_fail_attempts=max_attempts,
            max_rounds=max_attempts,
        )
    )
    finish = _FinishNode()

    code_agent - "next" >> tb_agent
    tb_agent - "next" >> verify_agent

    verify_agent - "verify_ok" >> finish
    verify_agent - "verify_fail" >> code_agent
    verify_agent - "abort" >> finish

    return Flow(start=code_agent)


def _run_verify(node: VerificationAgentNode, shared: dict) -> None:
    prep_res = node.prep(shared)
    exec_res = node.exec(prep_res)
    node.post(shared, prep_res, exec_res)


def run_case(
    *,
    case: str,
    dataset_root: Path,
    project_root: Path,
    logs_root_base: Path,
    results_root: Path,
    tb_top: str,
    max_attempts: int,
    run_id: str,
) -> None:
    prompt_path, ref_src, tb_src = _resolve_case_files(dataset_root, case)
    spec = prompt_path.read_text(encoding="utf-8")

    project_root.mkdir(parents=True, exist_ok=True)
    results_root.mkdir(parents=True, exist_ok=True)
    logs_root = logs_root_base / run_id / case if run_id else logs_root_base / case
    logs_root.mkdir(parents=True, exist_ok=True)

    dut_path = project_root / "TopModule.v"
    ref_path = project_root / ("RefModule" + ref_src.suffix)
    dataset_tb_path = project_root / ("tb" + tb_src.suffix)

    dut_path.write_text("", encoding="utf-8")
    shutil.copyfile(ref_src, ref_path)
    shutil.copyfile(tb_src, dataset_tb_path)

    gen_tb_rel = Path("tb") / f"{tb_top}.sv"
    gen_tb_path = project_root / gen_tb_rel
    gen_tb_path.parent.mkdir(parents=True, exist_ok=True)

    gen_rtl_flist = project_root / "rtl_gen.f"
    gen_tb_flist = project_root / "tb_gen.f"
    dataset_rtl_flist = project_root / "rtl_dataset.f"
    dataset_tb_flist = project_root / "tb_dataset.f"

    _write_flist(gen_rtl_flist, [dut_path.name])
    _write_flist(gen_tb_flist, [gen_tb_rel.as_posix()])
    _write_flist(dataset_rtl_flist, [dut_path.name, ref_path.name])
    _write_flist(dataset_tb_flist, [dataset_tb_path.name])

    llm_client = IFlowClient()

    gen_flow = _build_gen_flow(
        llm_client=llm_client,
        project_root=project_root,
        tb_top=tb_top,
        rtl_flist=str(gen_rtl_flist.name),
        tb_flist=str(gen_tb_flist.name),
        verify_out_dir=_rel_to_project(project_root, logs_root / "verify_gen"),
        max_attempts=max_attempts,
    )
    verify_dataset = VerificationAgentNode(
        params=VerificationAgentParams(
            project_root=str(project_root),
            rtl_flist=str(dataset_rtl_flist.name),
            tb_flist=str(dataset_tb_flist.name),
            tb_top=tb_top,
            work_subdir=".",
            out_dir=_rel_to_project(project_root, logs_root / "verify_dataset"),
            require_review_passed=False,
            max_fail_attempts=1,
            max_rounds=max_attempts,
        )
    )

    shared = {
        "spec": spec,
        "project_root": str(project_root),
        "top_rtl": "TopModule",
        "tb_top": tb_top,
        "case": case,
    }

    gen_flow.run(shared)
    gen_passed = bool(shared.get("verify_feedback", {}).get("passed"))
    if gen_passed:
        print(f"[gen-tb] case={case} passed on generated TB")
    else:
        print(f"[gen-tb] case={case} failed after {max_attempts} attempts; continue to dataset run")

    dataset_shared = {
        "spec": spec,
        "flow_status": {"round": shared.get("flow_status", {}).get("round", 0)},
    }
    _run_verify(verify_dataset, dataset_shared)

    dataset_passed = bool(dataset_shared.get("verify_feedback", {}).get("passed"))
    print(f"[dataset] case={case} passed={dataset_passed}")

    if dut_path.exists():
        out_path = results_root / f"{case}{dut_path.suffix}"
        shutil.copyfile(dut_path, out_path)

    raw = shared.get("code_agent_output_raw", "")
    if raw:
        (logs_root / f"{case}.raw.json").write_text(raw, encoding="utf-8")

    notes = shared.get("code_agent_notes", "")
    if notes:
        (logs_root / f"{case}.notes.txt").write_text(notes, encoding="utf-8")

    tb_raw = shared.get("tb_agent_output_raw", "")
    if tb_raw:
        (logs_root / f"{case}.tb.raw.json").write_text(tb_raw, encoding="utf-8")

    tb_notes = shared.get("tb_agent_notes", "")
    if tb_notes:
        (logs_root / f"{case}.tb.notes.txt").write_text(tb_notes, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate RTL+TB, verify with generated TB (retry), then run dataset TB.",
    )
    parser.add_argument(
        "--dataset-root",
        default="/mnt/hdd/datasets/verilog-eval/dataset_spec-to-rtl",
        help="Dataset root containing problems.txt and per-case prompt/ref/test files.",
    )
    parser.add_argument(
        "--problems",
        default=None,
        help="Path to problems.txt (default: <dataset-root>/problems.txt)",
    )
    parser.add_argument(
        "--project-root",
        default="/home/eda/project/exp",
        help="Working project root (will be overwritten per case).",
    )
    parser.add_argument(
        "--exp-root",
        default=None,
        help="Experiment root; when set, project/logs/gen_result are created under this directory.",
    )
    parser.add_argument(
        "--results-root",
        default="/home/eda/project/exp/gen_result",
        help="Directory to store generated DUT per case.",
    )
    parser.add_argument(
        "--tb-top",
        default="tb",
        help="Testbench top module name for iverilog.",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=5,
        help="Max retries on generated TB before running dataset TB.",
    )
    args = parser.parse_args()

    dataset_root = Path(args.dataset_root).expanduser().resolve()
    problems_path = Path(args.problems).expanduser().resolve() if args.problems else dataset_root / "problems.txt"
    if args.exp_root:
        exp_root = Path(args.exp_root).expanduser().resolve()
        project_root = exp_root / "project"
        results_root = exp_root / "gen_result"
        logs_root_base = exp_root / "logs"
        run_id = ""
    else:
        project_root = Path(args.project_root).expanduser().resolve()
        results_root = Path(args.results_root).expanduser().resolve()
        logs_root_base = project_root / "logs"
        run_id = datetime.now().strftime("%Y%m%d%H%M%S")

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
                logs_root_base=logs_root_base,
                results_root=results_root,
                tb_top=args.tb_top,
                max_attempts=args.max_attempts,
                run_id=run_id,
            )
        except Exception as e:
            print(f"[error] case={case}: {e}")
            continue


if __name__ == "__main__":
    main()
