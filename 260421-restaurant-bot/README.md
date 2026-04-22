# 🍽️ AI Restaurant Bot (Multi-Agent System)

Ollama 로컬 모델을 활용하여 레스토랑의 예약, 메뉴 안내, 주문, 그리고 고객 불만 처리까지 도와주는 인공지능 멀티 에이전트 시스템입니다. OpenAI의 최신 `openai-agents` SDK를 기반으로 설계되었으며, 안정적인 서비스 운영을 위한 이중 가드레일과 실시간 모니터링 시스템을 갖추고 있습니다.

## 🚀 주요 기능

### 1. Multi-Agent Orchestration
- **Triage Agent**: 고객의 요청(예약, 메뉴, 주문, 불만)을 분석하여 최적의 전문가 에이전트에게 자동 연결합니다.
- **Complaints Agent (신규)**: 불만이 감지된 고객에게 공감과 사과를 전하고, 할인 쿠폰 발급이나 매니저 콜백 등의 실질적인 해결책을 제공합니다.

### 2. 이중 Guardrails (보안 및 품질 보장)
- **Input Guardrails**: 레스토랑 업무와 무관한 질문(Off-topic)이나 부적절한 언어(욕설 등)를 감지하여 시스템 진입 단계에서 차단합니다.
- **Output Guardrails**: 에이전트의 답변이 전문적인지, 시스템 프롬프트 등 내부 정보가 유출되지 않았는지 최종 검수하여 안전한 응답만 사용자에게 전달합니다.

### 3. 실시간 통합 모니터링
- **Handoff Monitor**: 에이전트 간 권한 위임 발생 시 원인과 상세 내용을 실시간으로 확인합니다.
- **Tool Monitor (신규)**: 에이전트가 내부적으로 어떤 함수(할인 쿠폰 발급, 매니저 호출 등)를 실행했는지 시간과 상세 파라미터를 사이드바에서 즉시 모니터링합니다.
- **Async Logic**: Streamlit의 비동기 환경에서 발생하는 컨텍스트 유실 문제를 전역 큐(Global Queue) 방식으로 해결하여 안정적인 로그 업데이트를 보장합니다.

### 4. 개인화된 고객 응대
- **Context Awareness**: 유저의 등급(VIP/Basic)과 이름을 인식하여 차별화된 응대 톤과 서비스를 제공합니다.

## 🛠️ 기술 스택

- **Language**: Python 3.x
- **Framework**: [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)
- **UI**: Streamlit
- **LLM Engine**: Ollama (Llama 3.1, Qwen 2.5, Gemma 등)
- **Package Manager**: uv

## 📂 프로젝트 구조

```text
260421-restaurant-bot/
├── main.py                 # Streamlit UI 및 메인 실행 로직 (비동기 로그 처리 포함)
├── models.py               # Pydantic 기반 데이터 모델 (Guardrail, Context 등)
├── utils.py                # Handoff/Tool 실행 기록 및 유틸리티 함수
├── .env                    # 환경 변수 및 로컬 모델 설정
└── restaurant_agents/      # 전문가 에이전트 폴더
    ├── triage.py           # Triage 에이전트 및 이중 가드레일(In/Out) 정의
    ├── complaints.py       # 고객 불만 처리 전문가 (Tool 호출 기능 포함)
    ├── menu.py             # 메뉴 및 알레르기 안내 전문가
    ├── order.py            # 주문 처리 전문가
    └── reservation.py      # 테이블 예약 전문가
```