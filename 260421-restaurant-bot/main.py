# main.py
import os
import streamlit as st
from dotenv import load_dotenv
from agents.exceptions import InputGuardrailTripwireTriggered

# 1. 환경변수 로드
load_dotenv()

# 2. OpenAI 클라이언트가 Ollama를 바라보도록 강제 설정
# openai-agents SDK는 내부적으로 OpenAI 라이브러리를 사용하므로 이 환경 변수를 읽습니다.
os.environ["OPENAI_BASE_URL"] = os.getenv("OLLAMA_API_URL")
# (Ollama를 쓸 때는 API 키 검증을 안 하지만, 에러 방지용으로 값 유지)
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "ollama") 

from agents import Runner
from restaurant_agents.triage import triage_agent
from models import UserAccountContext

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
if "current_agent" not in st.session_state:
    st.session_state.current_agent = triage_agent

# ==========================================
# 🌟 사이드바: 권한 위임 실시간 모니터링
# ==========================================
with st.sidebar:
    st.header("🔄 Handoff Monitor")
    st.caption("에이전트 간 권한 위임 발생 이력")
    
    if not st.session_state.handoff_logs:
        st.write("현재까지 발생한 위임이 없습니다.")
    
    for log in reversed(st.session_state.handoff_logs):
        with st.expander(f"📍 To: {log['to_agent']}", expanded=True):
            st.write(f"**Reason:** {log['reason']}")
            st.write(f"**Type:** {log['issue_type']}")
            st.info(f"{log['description']}")

# ----------------- 채팅 UI -----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            st.markdown(f"**[{msg['agent_name']}]** {msg['content']}")
        else:
            st.markdown(msg["content"])

# 4. 사용자 입력 처리
if prompt := st.chat_input("질문을 입력하세요..."):
    # 유저 메시지 저장
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.spinner("에이전트 협업 중..."):
        # Runner 실행
        result = Runner.run_sync(
            st.session_state.current_agent, 
            prompt,
            context=user_account_ctx
        )
        
        new_agent = result.last_agent
        
        # 1️⃣ Handoff 감지 로직
        if new_agent.name != st.session_state.current_agent.name:
            handoff_text = f"[{new_agent.name}로 handoff] {new_agent.name} 전문가에게 연결합니다..."
            st.session_state.messages.append({"role": "handoff", "content": handoff_text})
            
            # 현재 에이전트 업데이트
            st.session_state.current_agent = new_agent

        # 2️⃣ 빈 메시지 방어 로직 (로컬 모델 벙어리 방지)
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
        
    # 3️⃣ 화면 전체 강제 새로고침 (이게 핵심입니다!)
    # 이걸 호출하면 Streamlit이 위에서부터 다시 그리면서 사이드바 로그와 채팅을 즉시 띄웁니다.
    st.rerun()