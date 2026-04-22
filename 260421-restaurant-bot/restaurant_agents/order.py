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

    return f"""당신은 주문을 받는 에이전트입니다.
    고객명은 {user_name}님입니다.
    메뉴와 수량을 확인하여 주문을 돕는 것이 주 임무입니다."""

order_agent = Agent(
    name="Order_Agent",
    model=MODEL_NAME,
    instructions=dynamic_account_agent_instructions,
)


from restaurant_agents.menu import menu_agent
from restaurant_agents.reservation import reservation_agent
from restaurant_agents.triage import triage_agent
from restaurant_agents.complaints import complaints_agent

order_agent.handoffs = [
        make_handoff(menu_agent),
        make_handoff(reservation_agent),
        make_handoff(triage_agent),
        make_handoff(complaints_agent),
    ]
