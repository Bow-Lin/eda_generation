from __future__ import annotations

import argparse
from pathlib import Path

from nodes.review_agent import ReviewAgentNode, ReviewAgentParams


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run ReviewAgentNode once (SpyGlass lint) to check RTL syntax/lint issues.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Project root (host path) that matches the container mount. Reports are written under <project_root>/build/review.",
    )
    parser.add_argument(
        "--rtl-flist",
        default="rtl.f",
        help="RTL file list (absolute or relative to project_root) visible inside the container.",
    )
    parser.add_argument(
        "--top-rtl",
        default="top",
        help="Top module name for SpyGlass.",
    )
    parser.add_argument(
        "--work-subdir",
        default="smoketest",
        help="Working directory inside project_root (and inside container).",
    )
    parser.add_argument(
        "--container-name",
        default="spyglass-centos7",
        help="Docker container name running SpyGlass.",
    )
    parser.add_argument(
        "--docker-bin",
        default="docker",
        help="Docker executable to invoke.",
    )
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    if not project_root.exists():
        raise SystemExit(f"project_root does not exist: {project_root}")

    params = ReviewAgentParams(
        project_root=str(project_root),
        rtl_flist=args.rtl_flist,
        top_rtl=args.top_rtl,
        work_subdir=args.work_subdir,
        container_name=args.container_name,
        docker_bin=args.docker_bin,
    )

    node = ReviewAgentNode(params=params)

    shared = {
        "rtl_flist": args.rtl_flist,
        "top_rtl": args.top_rtl,
    }

    prep_res = node.prep(shared)
    exec_res = node.exec(prep_res)
    route = node.post(shared, prep_res, exec_res)

    fb = shared.get("review_feedback", {})

    print(f"[route] {route}")
    print(f"[passed] {fb.get('passed')}")
    print(f"[issues] {len(fb.get('issues', []))}")
    print(f"[artifacts] {fb.get('artifacts')}")
    print("\n=== raw log tail ===")
    for line in fb.get("raw_log_tail", []):
        print(line)


if __name__ == "__main__":
    main()
