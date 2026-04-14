import streamlit as st
import os
from dotenv import load_dotenv
load_dotenv(override=True)

from agents import Runner, set_tracing_disabled
set_tracing_disabled(True) # OpenAI 서버로 Tracing 정보 전송(401 에러 원인)을 끕니다.

from agent import life_coach_agent, current_query_log
from sqlite_session import SQLiteSession

st.set_page_config(page_title="AI Life Coach", page_icon="💡", layout="wide")

# DB 세션 초기화
@st.cache_resource
def get_db():
    return SQLiteSession()

db = get_db()

# ==========================================
# 1. 상태 동기화 및 메시지 선로딩 (사이드바 제어용)
# ==========================================
# 상태에 논리적 현재 방 ID 변수가 없다면 가상 세션으로 시작
if "current_session_id" not in st.session_state:
    st.session_state["current_session_id"] = "NEW"

current_id = st.session_state["current_session_id"]

# DB 세션이 할당되었을 때만 메시지를 가져옴
messages = []
if current_id != "NEW":
    messages = db.get_messages(current_id)

# ==========================================
# 2. 사이드바 (세션 관리 및 디버깅)
# ==========================================
with st.sidebar:
    st.title("📂 대화 세션 관리")
    
    # 새 대화 생성 버튼
    if st.button("➕ 새 대화 시작", use_container_width=True):
        st.session_state["current_session_id"] = "NEW"
        st.rerun()
        
    st.divider()
    
    # 기존 세션 목록 (가장 최신 방부터)
    all_sessions = db.get_all_sessions()
        
    # 방 상태 유효성 검증 (삭제된 방 ID를 들고 있는 엣지 케이스 방지)
    valid_ids = [s["session_id"] for s in all_sessions]
    if st.session_state["current_session_id"] != "NEW" and st.session_state["current_session_id"] not in valid_ids:
        st.session_state["current_session_id"] = "NEW"
        
    # 방 목록을 옵션으로 만들기
    session_options = {}
    
    # 💡 사용자가 실제로 '새 대화' 상태일 때만 라디오 버튼 목록에 가상 세션을 띄워줍니다.
    if st.session_state["current_session_id"] == "NEW":
        session_options["NEW"] = "✨ 새로운 대화 (입력 대기 중)"
        
    for s in all_sessions:
        session_options[s["session_id"]] = s["title"]
        
    # 화면 렌더링 전, Radio 위젯의 상태(키)를 논리 상태와 동기화 (오류 방지)
    st.session_state["session_radio"] = st.session_state["current_session_id"]
    
    # 라디오 버튼이 변경될 때 논리 상태를 업데이트하는 콜백 함수
    def on_session_change():
        st.session_state["current_session_id"] = st.session_state["session_radio"]

    selected_session = st.radio(
        "과거 대화 방 목록",
        options=list(session_options.keys()),
        format_func=lambda x: session_options[x],
        key="session_radio",
        on_change=on_session_change
    )
    
    st.divider()
    
    # 2. 디버깅 및 초기화 도구
    st.subheader("🛠 설정 및 디버그")
    
    def reset_db_callback():
        db.reset_all()
        st.session_state["current_session_id"] = "NEW"
        
    # on_click 콜백을 사용하면 위젯 인스턴스화 후 상태 변경 오류를 완벽히 피할 수 있음
    st.button("🗑️ 모든 대화 초기화 (DB 날리기)", type="primary", use_container_width=True, on_click=reset_db_callback)
        
    with st.expander("🔍 현재 방의 메모리 상태 보기"):
        if st.session_state["current_session_id"] == "NEW":
            st.info("아직 메모리가 생성되지 않은 가상의 대화방입니다.")
        else:
            raw_msgs = db.get_messages(st.session_state["current_session_id"])
            st.json(raw_msgs)

# ==========================================
# 3. 메인 대화 영역
# ==========================================
st.title("💡 당신만의 AI 라이프 코치")
st.markdown("어떤 목표를 세우고 싶으신가요? 최신 정보를 바탕으로 실천 가능한 조언을 드릴게요!")

# 화면용 임시 인사말 (DB에 넣지는 않음)
if not messages:
    messages = [{"role": "assistant", "content": "안녕하세요! 오늘은 어떤 목표나 고민을 나누고 싶으신가요?"}]

# 이전 대화들 화면에 그리기
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 💡 Ghosting(이전 화면 잔상) 억제 장치
# Streamlit은 현재 스크립트가 완전히 끝나기 전까지 이전 화면 요소들을 반투명하게 남겨둡니다.
# 이를 방지하기 위해 빈 컨테이너 10개를 깔아서 기존 UI 블록들을 즉시 덮어씌워 소멸시킵니다.
for _ in range(10):
    st.empty()

# DB 마지막 메시지가 "user"라면, AI가 응답할 차례!
# 만약 가상 세션("NEW")이라면 AI가 반응하면 안됨 (아직 사용자가 문장을 완전히 입력 후 처리되지 않은 상태)
if current_id != "NEW" and messages and messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        # 검색 도구가 실행될 때마다 파이썬 전역 로그 배열 비우기
        current_query_log.clear()
        
        with st.spinner("라이프 코치가 최신 정보를 기반으로 생각하는 중..."):
            try:
                user_prompt = messages[-1]["content"]
                # 이전 컨텍스트 (마지막 유저 발화 제외 최대 5개)
                history_texts = [f"{m['role']}: {m['content']}" for m in messages[-6:-1]] 
                history_str = "\n".join(history_texts)
                
                context_prompt = (
                    f"다음은 과거 대화 맥락입니다:\n{history_str}\n\n"
                    f"가장 마지막에 작성된 user의 요청('{user_prompt}')에 강력하게 조언해주세요. "
                    f"만약 정확한 지식, 팁, 명언, 정보가 필요하다면 당신에게 주어진 'search_web' 도구를 적극적으로 먼저 호출하여야 합니다."
                )
                
                # openai-agents 실행 (GIL 잠금 방지로 인한 지연 시에도 Streamlit 화면표시 보증)
                result = Runner.run_sync(life_coach_agent, context_prompt)
                
                # LLM 처리가 끝난 뒤 실행되었던 툴(웹 검색) 내역을 DB에 인서트
                for query in current_query_log:
                    tool_msg = f"🔍 **[웹 검색: \"{query}\"]**"
                    db.add_message(current_id, "assistant", tool_msg) 
                
                # 최종 텍스트 DB 인서트 및 즉시 rerun
                db.add_message(current_id, "assistant", result.final_output)
                st.rerun() # DB 저장 후 다시 렌더링하여 안정성 확보
                
            except Exception as e:
                st.error(f"오류가 발생했습니다. Ollama가 켜져 있는지 확인하세요.\n\n에러 메시지: {e}")
                # 💡 에러 발생 시 앱이 'AI 응답 대기' 상태에 영원히 갇히지 않도록(사이드바 잠금 해전) 에러 메시지도 시스템 응답으로 DB에 저장합니다.
                db.add_message(current_id, "assistant", "⚠️ 시스템 오류로 인해 답변을 생성하지 못했습니다. 설정을 확인하고 다시 시도해주세요.")
                st.rerun()

# 사용자 입력 위젯 (AI 응답 중일때는 무시되도록 처리)
if prompt := st.chat_input("예: 아침 6시에 일어나는 습관을 들이고 싶어."):
    if not (current_id != "NEW" and messages and messages[-1]["role"] == "user"):
        # 💡 지연 생성 장치(Lazy Creation): 만약 아직 DB 방이 없는 'NEW' 상태라면 이때 실제 방을 판다!
        if current_id == "NEW":
            new_db_id = db.create_session()
            st.session_state["current_session_id"] = new_db_id
            current_id = new_db_id
            
            # 첫 번째 기본 인사말도 DB에 꽂아준다 (일관성 유지)
            db.add_message(current_id, "assistant", "안녕하세요! 오늘은 어떤 목표나 고민을 나누고 싶으신가요?")
            
        # 1) 사용자 메시지 DB 저장
        db.add_message(current_id, "user", prompt)
        st.rerun() # 챗 입력 즉시 rerun하여 화면에 반영함
