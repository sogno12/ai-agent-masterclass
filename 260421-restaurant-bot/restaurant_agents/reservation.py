# restaurant_agents/reservation.py
import os
from agents import Agent, RunContextWrapper
from models import UserAccountContext

from utils import make_handoff

# .env에서 모델명 가져오기
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3")

def dynamic_account_agent_instructions(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
):
    user_name = wrapper.context.user_name

    return f"""당신은 테이블 예약 담당자입니다.
    고객명은 {user_name}님입니다.
    날짜, 시간, 방문 인원수를 확인하여 예약을 돕는 것이 주 임무입니다."""

reservation_agent = Agent(
    name="Reservation_Agent",
    model=MODEL_NAME,
    instructions=dynamic_account_agent_instructions
)

from restaurant_agents.menu import menu_agent
from restaurant_agents.order import order_agent
from restaurant_agents.triage import triage_agent
from restaurant_agents.complaints import complaints_agent

reservation_agent.handoffs = [
        make_handoff(menu_agent),
        make_handoff(order_agent),
        make_handoff(triage_agent),
        make_handoff(complaints_agent)
    ]
