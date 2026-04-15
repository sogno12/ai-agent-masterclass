import os
from duckduckgo_search import DDGS
from agents import Agent, function_tool
from rag_service import search_documents

# 비동기 스레드(asyncio)에서 실행되어 Streamlit 세션에 접근 못하는 문제를 피하기 위한 파이썬 리스트
current_query_log = []
current_file_search_log = []

@function_tool
def search_web(query: str) -> str:
    """사용자의 요청(명언, 최신 기법, 동기부여, 조언 등)에 답하기 위해 외부 웹 검색을 수행하는 도구입니다. 
    자신의 지식으로 지어내지 말고, 구체적인 정보나 명언을 요구받으면 반드시 이 도구를 호출하세요."""
    
    # 📌 콘솔 디버깅용
    print(f"\n==============================================")
    print(f"🔊 [TOOL 호출됨!] 에이전트가 최신 웹 검색을 시작했습니다.")
    print(f"🔊 검색어(Query): '{query}'")
    print(f"==============================================\n")
    
    current_query_log.append(query)

    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return "검색 결과가 없습니다."
        return "\n\n".join([f"제목: {r['title']}\n내용: {r['body']}" for r in results])
    except Exception as e:
        return f"웹 검색 중 오류가 발생했습니다: {str(e)}"

@function_tool
def search_personal_records(query: str) -> str:
    """사용자가 최근 자신의 목표 진행 상황, 어제/오늘의 일기, 혹은 개인적인 다짐 등을 묻거나 이를 바탕으로 조언을 구할 때 호출하는 도구입니다.
    사용자의 개인 저장소에 올라가 있는 과거 기록 파일들을 읽어서 맥락을 파악합니다.
    검색할 내용(query)을 구체적인 키워드로 요약해서 보내세요. (예: '올해 목표', '수면 시간', '운동')"""
    
    print(f"\n==============================================")
    print(f"📁 [TOOL 호출됨!] 에이전트가 개인 기록(VectorDB) 검색을 시작했습니다.")
    print(f"📁 검색어(Query): '{query}'")
    print(f"==============================================\n")
    
    current_file_search_log.append(query)
    
    try:
        return search_documents(query)
    except Exception as e:
        return f"문서 검색 중 에러가 발생했습니다: {str(e)}"

# 에이전트 인스턴스 생성
model_name = os.getenv("OLLAMA_MODEL", "gemma4:e4b")

life_coach_agent = Agent(
    name="Life Coach Agent",
    model=model_name,
    instructions=(
        "당신은 세계 최고의 라이프 코치입니다. "
        "사용자의 목표 달성과 긍정적인 습관 형성을 돕기 위해 맞춤형이고 동기부여가 되는 조언을 제공합니다. "
        "사용자가 과거 자신의 기록(일기, 개인 목표 등)에 대해 묻거나 조언을 구할 경우 가장 먼저 'search_personal_records' 도구를 호출하여 사용자의 상태와 다짐을 확인하세요. "
        "그리고 '특정 기법', '명언', '최신 방법', '검색해줘' 등의 요청이 들어오면 혼자서 지어내지 말고 반드시 'search_web' 도구를 호출하세요. "
        "도구가 반환한 정보나 개인 기록을 활용하여 한국어로 친절하게 답변해주세요."
    ),
    tools=[search_web, search_personal_records],
)
