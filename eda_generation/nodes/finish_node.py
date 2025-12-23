from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from pocketflow import Node


class FinishNode(Node):
    """Terminal node to mark flow completion and allow cleanup/summary."""

    def prep(self, shared):
        # ensure shared is a dict to avoid NoneType errors when flow ends unexpectedly
        return shared or {}

    def exec(self, shared: Dict[str, Any]) -> str:
        shared.setdefault("flow_status", {})
        shared["flow_status"]["done"] = True
        shared["flow_status"]["last_stage"] = "finish"
        shared["flow_status"].setdefault("last_reason", "finished")
        return "done"
    
    def post(self, shared: Dict[str, Any], prep_res: Any, exec_res: str) -> Dict[str, Any]:
        # Persist final shared snapshot once per flow for postmortem comparison.
        try:
            project_root = shared.get("project_root")
            root = Path(project_root).resolve() if project_root else Path(".").resolve()
            build_dir = (root / "build").resolve()
            build_dir.mkdir(parents=True, exist_ok=True)
            snap = {
                "stage": "finish",
                "round": shared.get("flow_status", {}).get("round"),
                "shared": shared,
            }
            with (build_dir / "shared.log").open("a", encoding="utf-8") as f:
                f.write(json.dumps(snap, ensure_ascii=False, indent=2))
                f.write("\n")
        except Exception:
            pass
        return shared
