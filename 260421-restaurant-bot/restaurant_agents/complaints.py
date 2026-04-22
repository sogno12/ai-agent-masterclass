# restaurant_agents/complaints.py
import os
from agents import Agent, RunContextWrapper, function_tool
from models import UserAccountContext

from utils import make_handoff, add_tool_log

MODEL_NAME = os.getenv("OLLAMA_MODEL", "gemma4:e2b")

def dynamic_account_agent_instructions(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
):
    user_name = wrapper.context.user_name

    return f"""당신은 고객의 불만을 최종적으로 해결하는 **최고 고객 만족 매니저**입니다.
가장 중요한 규칙: 절대 다른 담당자에게 연결하겠다는 말(예: '매니저에게 연결해 드리겠습니다', '기다려 주세요' 등)을 텍스트로만 하지 마세요. 당신이 최종 담당자입니다.

고객이 불만이나 환불을 요구할 경우, 다음 절차를 엄격히 따르세요:
1. **짧고 진정성 있는 사과**: 고객의 불편에 공감하세요.
2. **즉각적인 도구(Tool) 호출**: 말로만 해결하려 하지 말고, **반드시 즉시** 아래 도구 중 하나를 호출하세요.
   - 환불 요구, 심한 폭언, 직원의 큰 실수: `request_manager_callback` 도구를 즉시 사용하세요.
   - 음식 맛 불만, 가벼운 서비스 지연: `issue_discount_coupon` 도구를 사용하여 보상하세요.
3. 도구를 실행한 경우, 실행 결과를 바탕으로 "조치가 완료되었습니다"라고 안내하며 대화를 확실히 마무리하세요.
4. 도구를 실행하지 않은 경우, 행할 수 있는 조치에 대해서 안내하세요."""

# 보상 관련 도구(Tools) 정의
@function_tool
def issue_discount_coupon(percentage: int = 50):
    """고객에게 할인 쿠폰을 발급합니다."""
    print(f"\n=======================================")
    print(f"🎁 [TOOL EXECUTED] 할인 쿠폰 발급기 작동! (할인율: {percentage}%)")
    print(f"=======================================\n")
    
    add_tool_log(
        agent_name="Complaints Agent",
        tool_name="issue_discount_coupon",
        detail=f"{percentage}% 할인 쿠폰 발급 완료"
    )
    return f"[시스템 알림: 고객에게 {percentage}% 할인 쿠폰 발급이 완료되었습니다.]"

@function_tool
def request_manager_callback(reason: str):
    """매니저에게 콜백을 요청합니다."""
    print(f"\n=======================================")
    print(f"🚨 [TOOL EXECUTED] 매니저 콜백 시스템 작동! (사유: {reason})")
    print(f"=======================================\n")

    add_tool_log(
        agent_name="Complaints Agent",
        tool_name="request_manager_callback",
        detail=f"사유: {reason}"
    )
    return f"[시스템 알림: '{reason}' 사유로 매니저 긴급 콜백이 접수되었습니다.]"

complaints_agent = Agent(
    name="Complaints Agent",
    model=MODEL_NAME,
    instructions=dynamic_account_agent_instructions,
    tools=[issue_discount_coupon, request_manager_callback]
)

from restaurant_agents.menu import menu_agent
from restaurant_agents.order import order_agent
from restaurant_agents.reservation import reservation_agent
from restaurant_agents.triage import triage_agent

complaints_agent.handoffs = [
        make_handoff(menu_agent),
        make_handoff(order_agent),
        make_handoff(reservation_agent),
        make_handoff(triage_agent),
    ]