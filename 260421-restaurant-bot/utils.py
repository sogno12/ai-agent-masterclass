# utils.py
import streamlit as st
from agents import handoff, RunContextWrapper
from models import UserAccountContext, HandoffData

def handle_handoff(
    wrapper: RunContextWrapper[UserAccountContext],
    input_data: HandoffData,
):
    # 이전 답변에서 만든 세션 저장 방식 (사이드바 렌더링용)
    log_entry = {
        "to_agent": input_data.to_agent_name,
        "reason": input_data.reason,
        "issue_type": input_data.issue_type,
        "description": input_data.issue_description
    }
    
    if "handoff_logs" in st.session_state:
        st.session_state.handoff_logs.append(log_entry)

def make_handoff(agent):
    return handoff(
        agent=agent,
        on_handoff=handle_handoff,
        input_type=HandoffData,
        # input_filter=handoff_filters.remove_all_tools, # 필요시 주석 해제
    )