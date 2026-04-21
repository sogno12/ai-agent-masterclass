import os

# README 내용 구성
readme_content = """
# 🍽️ AI Restaurant Bot (Multi-Agent System)

Ollama 로컬 모델을 활용하여 레스토랑의 예약, 메뉴 안내, 주문을 도와주는 인공지능 멀티 에이전트 시스템입니다. OpenAI의 최신 `openai-agents` SDK를 기반으로 설계되었습니다.

## 🚀 주요 기능

- **Multi-Agent Orchestration**: Triage 에이전트가 고객의 요청을 분석하여 적절한 전문가(예약, 메뉴, 주문)에게 자동 연결합니다.
- **Handoff Monitoring**: 에이전트 간 권한 위임이 발생할 때, 그 이유와 상세 내용을 사이드바에서 실시간으로 확인할 수 있습니다.
- **Input Guardrails**: 레스토랑 업무와 무관한 질문(Off-topic)이 들어올 경우 보안 에이전트가 이를 감지하여 차단합니다.
- **User Context Awareness**: 유저의 등급(Tier)과 이름을 인식하여 개인화된 응대를 제공합니다.
- **Local LLM Integration**: Ollama를 통해 로컬 환경에서 모델을 실행하여 데이터 프라이버시를 보호합니다.

## 🛠️ 기술 스택

- **Language**: Python 3.x
- **Framework**: [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)
- **UI**: Streamlit
- **LLM Engine**: Ollama (Gemma, Llama 등)
- **Package Manager**: uv

## 📂 프로젝트 구조

```text
260421-restaurant-bot/
├── main.py                 # Streamlit UI 및 메인 실행 로직
├── models.py               # Pydantic 기반 데이터 모델 (Context, HandoffData)
├── utils.py                # Handoff 생성 및 로그 처리를 위한 공통 유틸리티
├── .env                    # 환경 변수 설정 파일
└── restaurant_agents/      # 전문가 에이전트 폴더
    ├── triage.py           # Triage 에이전트 및 가드레일 정의
    ├── menu.py             # 메뉴 및 알레르기 안내 전문가
    ├── order.py            # 주문 처리 전문가
    └── reservation.py      # 테이블 예약 전문가 (Dynamic Instructions 적용)