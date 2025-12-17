from eda_generation.flow import build_flow, FlowParams
from utils.clients.iflow_client import IFlowClient

if __name__ == "__main__":
    llm = IFlowClient()  # 需要 IFLOW_API_KEY
    flow = build_flow(llm_client=llm, params=FlowParams(
        project_root="/home/eda/project/exp",
        rtl_flist="rtl.f",
        top_rtl="TopModule",
        tb_flist="tb.f",
        tb_top="tb",
        max_rounds=3,
    ))
    shared = {
        "spec": "让 TopModule 输出 1'b1",  # 故意让行为与 RefModule 不同，触发第三步失败
    }
    flow.run(shared)
    print(shared.get("flow_status"))
    print(shared.get("review_feedback", {}))
    print(shared.get("verify_feedback", {}))
