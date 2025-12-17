from __future__ import annotations

import argparse
from pathlib import Path

from nodes.code_agent import CodeAgentNode, CodeAgentParams
from utils.clients.iflow_client import IFlowClient


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run CodeAgentNode once to generate RTL from a spec (steps 2/3 are skipped).",
    )
    parser.add_argument(
        "--spec",
        default="TODO: replace this placeholder with your RTL spec",
        help="Natural language spec for the RTL to generate.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Project root where RTL files will be written (default: repo/eda_generation).",
    )
    parser.add_argument(
        "--rtl-dir",
        default="rtl",
        help="RTL directory for auto-discovery (matches CodeAgentParams.rtl_dir).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature for the LLM.",
    )
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    if not project_root.exists():
        raise SystemExit(f"project_root does not exist: {project_root}")

    params = CodeAgentParams(
        project_root=str(project_root),
        rtl_dir=args.rtl_dir,
        temperature=args.temperature,
    )

    llm_client = IFlowClient()  # Requires IFLOW_API_KEY in the environment.
    node = CodeAgentNode(llm_client=llm_client, params=params)

    spec = """
    I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - output zero

The module should always outputs a LOW.
    """
    shared = {"spec": spec}

    prep_res = node.prep(shared)
    exec_res = node.exec(prep_res)
    route = node.post(shared, prep_res, exec_res)

    print(f"[route] {route}")
    print(f"[notes] {shared.get('code_agent_notes', '')}")
    print(f"[updated_rtl_files] {shared.get('updated_rtl_files', [])}")
    print("\n=== raw LLM output ===")
    print(shared.get("code_agent_output_raw", ""))


if __name__ == "__main__":
    main()
