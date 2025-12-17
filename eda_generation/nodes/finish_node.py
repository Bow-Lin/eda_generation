from __future__ import annotations

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
        pass
