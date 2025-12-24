from pathlib import Path
import json

from flow import build_flow, FlowParams
from utils.clients.iflow_client import IFlowClient


if __name__ == "__main__":
    llm = IFlowClient()  # 需要 IFLOW_API_KEY
    flow = build_flow(
        llm_client=llm,
        params=FlowParams(
            project_root="/home/eda/project/exp",
            rtl_flist="rtl.f",
            review_rtl_flist="rtl_review.f",   # review 只需 DUT
            verify_rtl_flist="rtl_verify.f",   # verify 需 DUT + RefModule
            top_rtl="TopModule",
            tb_flist="tb.f",
            tb_top="tb",
            max_rounds=3,
        ),
    )
    shared = {
        "spec": """
I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - output zero

The module should always outputs a LOW.
""",  # 按需替换
    }
    flow.run(shared)

    fs = shared.get("flow_status", {})
    rev = shared.get("review_feedback", {})
    ver = shared.get("verify_feedback", {})

    spec = shared.get("spec", "")
    round_no = fs.get("round")

    print(f"[summary] round={round_no} spec={spec!r}")
    print(f"[summary] review_passed={rev.get('passed')} verify_passed={ver.get('passed')}")
    print(
        f"[summary] review_issues={len(rev.get('issues', []))} "
        f"failed_cases={len(ver.get('failed_cases', []))} "
        f"compile_errors={len(ver.get('compile_errors', []))}"
    )

    # 写入完整调试信息
    debug_path = Path("/home/eda/project/exp/build/debug.log")
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    debug_path.write_text(
        json.dumps(
            {
                "flow_status": fs,
                "review_feedback": rev,
                "verify_feedback": ver,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
