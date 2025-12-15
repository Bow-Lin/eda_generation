from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from pocketflow import Flow, Node

from nodes.code_agent_node import CodeAgentNode, CodeAgentParams
from nodes.review_agent_node import ReviewAgentNode, ReviewAgentParams
from nodes.verification_agent_node import VerificationAgentNode, VerificationAgentParams


@dataclass
class FlowParams:
    project_root: str = "/home/project/xxproject"
    rtl_flist: str = "rtl.f"
    top_rtl: str = "top"
    tb_flist: str = "tb.f"
    tb_top: str = "tb_top"
    max_rounds: int = 20


class FinishNode(Node):
    def exec(self, shared: Dict[str, Any]) -> str:
        shared.setdefault("flow_status", {})
        shared["flow_status"]["done"] = True
        return "done"


class CodeStep(Node):
    def __init__(self, *, agent: CodeAgentNode, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent

    def exec(self, shared: Dict[str, Any]) -> str:
        shared.setdefault("flow_status", {})
        shared["flow_status"]["round"] = int(shared["flow_status"].get("round", 0)) + 1
        shared["flow_status"]["last_stage"] = "code"
        self.agent.run(shared)  # run single node logic; routing is handled by Flow
        return "next"


class ReviewStep(Node):
    def __init__(self, *, agent: ReviewAgentNode, params: FlowParams, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent
        self.p = params

    def exec(self, shared: Dict[str, Any]) -> str:
        shared.setdefault("flow_status", {})
        shared["flow_status"]["last_stage"] = "review"

        if int(shared["flow_status"].get("round", 0)) > self.p.max_rounds:
            shared["flow_status"]["last_reason"] = "max_rounds_reached"
            return "abort"

        self.agent.run(shared)

        passed = bool((shared.get("review_feedback") or {}).get("passed", False))
        if passed:
            shared["flow_status"]["last_reason"] = "syntax_ok"
            return "syntax_ok"

        shared["flow_status"]["last_reason"] = "syntax_fail"
        return "syntax_fail"


class VerifyStep(Node):
    def __init__(self, *, agent: VerificationAgentNode, params: FlowParams, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent
        self.p = params

    def exec(self, shared: Dict[str, Any]) -> str:
        shared.setdefault("flow_status", {})
        shared["flow_status"]["last_stage"] = "verify"

        if int(shared["flow_status"].get("round", 0)) > self.p.max_rounds:
            shared["flow_status"]["last_reason"] = "max_rounds_reached"
            return "abort"

        self.agent.run(shared)

        passed = bool((shared.get("verify_feedback") or {}).get("passed", False))
        if passed:
            shared["flow_status"]["last_reason"] = "verify_ok"
            return "verify_ok"

        shared["flow_status"]["last_reason"] = "verify_fail"
        return "verify_fail"


def build_flow(*, llm_client: Any, params: Optional[FlowParams] = None) -> Flow:
    p = params or FlowParams()

    shared_defaults = {
        "project_root": p.project_root,
        "rtl_flist": p.rtl_flist,
        "top_rtl": p.top_rtl,
        "tb_flist": p.tb_flist,
        "tb_top": p.tb_top,
    }

    code_agent = CodeAgentNode(
        llm_client=llm_client,
        params=CodeAgentParams(project_root=p.project_root),
    )

    review_agent = ReviewAgentNode(
        params=ReviewAgentParams(
            project_root=p.project_root,
            container_name="spyglass-centos7",
            work_subdir="smoketest",
            rtl_flist=p.rtl_flist,
            top_rtl=p.top_rtl,
        )
    )

    verify_agent = VerificationAgentNode(
        params=VerificationAgentParams(
            project_root=p.project_root,
            rtl_flist=p.rtl_flist,
            tb_flist=p.tb_flist,
            tb_top=p.tb_top,
            work_subdir="smoketest",
            require_review_passed=False,
        )
    )

    code = CodeStep(agent=code_agent)
    review = ReviewStep(agent=review_agent, params=p)
    verify = VerifyStep(agent=verify_agent, params=p)
    finish = FinishNode()

    # Edges
    code >> review

    review - "syntax_ok" >> verify
    review - "syntax_fail" >> code
    review - "abort" >> finish

    verify - "verify_ok" >> finish
    verify - "verify_fail" >> code
    verify - "abort" >> finish

    flow = Flow(start=code)

    # Optional: stash defaults for the caller to merge into shared
    flow.shared_defaults = shared_defaults  # type: ignore[attr-defined]
    return flow


if __name__ == "__main__":
    class DummyLLM:
        def generate(self, prompt: str, *, temperature: float = 0.2) -> str:
            raise RuntimeError("Replace DummyLLM with your real llm_client.")

    flow = build_flow(llm_client=DummyLLM())
    shared = {
        **getattr(flow, "shared_defaults", {}),
        "spec": "Describe your RTL requirement here.",
    }
    flow.run(shared)
    print(shared.get("flow_status"))
