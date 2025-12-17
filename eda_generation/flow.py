from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from pocketflow import Flow

from nodes.code_agent import CodeAgentNode, CodeAgentParams
from nodes.review_agent import ReviewAgentNode, ReviewAgentParams
from nodes.verification_agent import VerificationAgentNode, VerificationAgentParams
from nodes.finish_node import FinishNode

@dataclass
class FlowParams:
    project_root: str = "/home/project/xxproject"
    rtl_flist: str = "rtl.f"
    top_rtl: str = "top"
    tb_flist: str = "tb.f"
    tb_top: str = "tb_top"
    max_rounds: int = 3


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

    finish = FinishNode()

    # Edges
    code_agent - "next" >> review_agent

    review_agent - "syntax_ok" >> verify_agent
    review_agent - "syntax_fail" >> code_agent
    review_agent - "abort" >> finish

    verify_agent - "verify_ok" >> finish
    verify_agent - "verify_fail" >> code_agent
    verify_agent - "abort" >> finish

    flow = Flow(start=code_agent)

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
