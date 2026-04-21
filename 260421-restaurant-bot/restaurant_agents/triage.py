# restaurant_agents/triage.py
import os
import streamlit as st
from agents import (
    Agent,
    RunContextWrapper,
    input_guardrail,
    Runner,
    GuardrailFunctionOutput,
    handoff,
)

from models import UserAccountContext, InputGuardRailOutput, HandoffData

from utils import make_handoff

# .env에서 모델명 가져오기
MODEL_NAME = os.getenv("OLLAMA_MODEL", "gemma4:e2b")

input_guardrail_agent = Agent(
    name="Input Guardrail Agent",
    model=MODEL_NAME,
    instructions="""당신은 레스토랑 봇의 보안 요원(Guardrail)입니다.
사용자의 요청이 다음 세 가지 범주 중 하나에 해당하는지 엄격하게 확인하세요:
1. 테이블 예약 (날짜, 시간, 인원 등)
2. 메뉴 문의 (메뉴 종류, 식재료, 알레르기 정보, 채식 여부 등)
3. 음식 주문

[규칙]
- 당신은 반드시 아래의 JSON 형식(schema)으로만 응답해야 합니다. 임의로 키(key) 이름을 만들지 마세요. 마크다운 없이 순수 JSON만 출력하세요.
- 사용자가 위 세 가지와 무관한 주제(예: 정치, 날씨, 코딩, 타사 정보 등)를 물어보면 즉시 tripwire를 작동시키고 거절 이유를 반환하세요.
- 대화 시작 시의 가벼운 인사말(안녕, 반가워 등)이나 일상적인 스몰토크는 허용합니다. 
- 단, 스몰토크를 넘어서 레스토랑 서비스와 무관한 구체적인 정보나 도움을 요구할 경우 절대 통과시켜서는 안 됩니다.""",
    output_type=InputGuardRailOutput,
)

@input_guardrail
async def off_topic_guardrail(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
    input: str,
):
    result = await Runner.run(
        input_guardrail_agent,
        input,
        context=wrapper.context,
    )

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_off_topic,
    )

triage_agent = Agent(
    name="Triage Agent",
    model=MODEL_NAME,
    instructions="""당신은 레스토랑의 리셉션 데스크 담당자입니다. 
    고객의 요청을 분석하여 '메뉴 안내', '주문', '예약' 중 가장 적절한 전문가에게 연결하세요.
    직접 길게 답변하지 말고 빠르게 해당 담당자에게 위임(Handoff)하는 것이 목표입니다.""",
    input_guardrails=[
        off_topic_guardrail,
    ],
)

from restaurant_agents.menu import menu_agent
from restaurant_agents.order import order_agent
from restaurant_agents.reservation import reservation_agent

triage_agent.handoffs = [
        make_handoff(menu_agent),
        make_handoff(order_agent),
        make_handoff(reservation_agent)
    ]