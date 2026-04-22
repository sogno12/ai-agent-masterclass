# main.py
import os
import streamlit as st
from dotenv import load_dotenv

# 1. 환경변수 로드
load_dotenv()
# 2. OpenAI 클라이언트가 Ollama를 바라보도록 강제 설정
# openai-agents SDK는 내부적으로 OpenAI 라이브러리를 사용하므로 이 환경 변수를 읽습니다.
os.environ["OPENAI_BASE_URL"] = os.getenv("OLLAMA_API_URL")
# (Ollama를 쓸 때는 API 키 검증을 안 하지만, 에러 방지용으로 값 유지)
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "ollama") 

from agents import Runner
from agents.exceptions import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered
from restaurant_agents.triage import triage_agent
from models import UserAccountContext
from utils import TOOL_EXECUTION_QUEUE

st.set_page_config(page_title="AI Restaurant Bot", layout="wide")
st.title("🍽️ AI 레스토랑 봇 (Monitoring 모드)")

# 2. 유저 컨텍스트 설정 (SJ님 정보)
user_account_ctx = UserAccountContext(
    customer_id=1,
    user_name="SJ",
    tier="VIP"
)

# 3. 세션 상태 초기화 (메시지 및 Handoff 로그 저장)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "handoff_logs" not in st.session_state:
    st.session_state.handoff_logs = [] # 사이드바용 로그 리스트
if "tool_logs" not in st.session_state:
    st.session_state.tool_logs = [] # Tool 로그 저장소 추가
if "current_agent" not in st.session_state:
    st.session_state.current_agent = triage_agent

# ==========================================
# 🌟 사이드바: 권한 위임 실시간 모니터링
# ==========================================
with st.sidebar:
    # Handoff Monitor UI
    st.header("🔄 Handoff Monitor")
    st.caption("에이전트 간 권한 위임 발생 이력")
    
    if not st.session_state.handoff_logs:
        st.write("현재까지 발생한 위임이 없습니다.")
    
    for log in reversed(st.session_state.handoff_logs):
        with st.expander(f"📍 To: {log['to_agent']}", expanded=True):
            st.write(f"**Reason:** {log['reason']}")
            st.write(f"**Type:** {log['issue_type']}")
            st.info(f"{log['description']}")

    st.divider() # ➖ 구분선 추가

    # Tool Monitor UI
    st.header("🛠️ Tool Monitor")
    st.caption("에이전트 도구(함수) 실행 이력")
    
    if not st.session_state.tool_logs:
        st.write("현재까지 실행된 도구가 없습니다.")
    else:
        for log in reversed(st.session_state.tool_logs):
            with st.expander(f"⚙️ {log['tool_name']} ({log['time']})", expanded=True):
                st.write(f"**Agent:** {log['agent_name']}")
                st.success(f"{log['detail']}") # 초록색 박스로 표시

# ----------------- 채팅 UI -----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            st.markdown(f"**[{msg['agent_name']}]** {msg['content']}")
        else:
            st.markdown(msg["content"])

# 4. 사용자 입력 처리
if prompt := st.chat_input("질문을 입력하세요..."):
    # 1️. 유저 메시지를 세션에 추가하고 화면에 즉시 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    # 2️. 로딩 애니메이션 시작 (유저 메시지는 이미 떠 있는 상태)
    with st.spinner("에이전트 협업 중..."):
        try:
            # Runner 실행
            result = Runner.run_sync(
                st.session_state.current_agent, 
                prompt,
                context=user_account_ctx
            )

            # 에이전트 실행이 끝난 후, 임시 큐에 쌓인 도구 로그를 세션 상태로 옮김
            if TOOL_EXECUTION_QUEUE:
                st.session_state.tool_logs.extend(TOOL_EXECUTION_QUEUE)
                TOOL_EXECUTION_QUEUE.clear() # 큐 비우기

            # Handoff 감지 로직
            new_agent = result.last_agent
            
            if new_agent.name != st.session_state.current_agent.name:
                handoff_text = f"[{new_agent.name}로 handoff] {new_agent.name} 전문가에게 연결합니다..."
                st.session_state.messages.append({"role": "handoff", "content": handoff_text})
                
                # 현재 에이전트 업데이트
                st.session_state.current_agent = new_agent

            # 빈 메시지 방어 로직 (로컬 모델 벙어리 방지)
            bot_reply = result.final_output
            
            if not bot_reply or bot_reply.strip() == "":
                # 모델이 Handoff만 하고 말을 안 했을 때 자연스럽게 이어주는 대사
                bot_reply = "연결되었습니다. 원하시는 내용을 편하게 말씀해 주세요!"

            # 봇 응답 저장
            st.session_state.messages.append({
                "role": "assistant", 
                "content": bot_reply, 
                "agent_name": new_agent.name
            })

        except InputGuardrailTripwireTriggered:
            # 입력 가드레일(부적절 단어, 주제 이탈)에 걸렸을 때
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "죄송합니다. 레스토랑 서비스와 관련 없는 질문이나 부적절한 표현은 답변드리기 어렵습니다. 메뉴 안내, 예약, 주문 등에 대해 문의해 주세요!",
                "agent_name": "System Security"
            })
            
        except OutputGuardrailTripwireTriggered:
            # 출력 가드레일(보안, 전문성 부족)에 걸렸을 때
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "죄송합니다. 요청하신 내용에 대해 적절한 응답을 생성하는 데 어려움이 있습니다. 다시 한번 정중히 부탁드립니다.",
                "agent_name": "System Security"
            })
    
    # 3️. 상태 업데이트를 위해 재실행(화면 전체 강제 새로고침)
    # 이걸 호출하면 Streamlit이 위에서부터 다시 그리면서 사이드바 로그와 채팅을 즉시 띄웁니다.
    st.rerun()