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

    return f"""당신은 레스토랑의 메뉴 전문가입니다.
    고객명은 {user_name}님입니다.
    우리 레스토랑은 스테이크, 파스타, 채식 샐러드를 판매합니다.
    - 스테이크: 한우 등급, 땅콩 알레르기 주의
    - 파스타: 토마토 베이스, 해산물 포함
    - 샐러드: 채식(비건) 가능
    메뉴와 알레르기 정보를 상세히 설명하세요."""

menu_agent = Agent(
    name="Menu_Agent",
    model=MODEL_NAME,
    instructions=dynamic_account_agent_instructions,
)

from restaurant_agents.order import order_agent
from restaurant_agents.reservation import reservation_agent
from restaurant_agents.triage import triage_agent

menu_agent.handoffs = [
        make_handoff(order_agent),
        make_handoff(reservation_agent),
        make_handoff(triage_agent),
    ]