import os
from duckduckgo_search import DDGS
from agents import Agent, function_tool

# 비동기 스레드(asyncio)에서 실행되어 Streamlit 세션에 접근 못하는 문제를 피하기 위한 파이썬 리스트
current_query_log = []

@function_tool
def search_web(query: str) -> str:
    """사용자의 요청(명언, 최신 기법, 동기부여, 조언 등)에 답하기 위해 외부 웹 검색을 수행하는 도구입니다. 
    자신의 지식으로 지어내지 말고, 구체적인 정보나 명언을 요구받으면 반드시 이 도구를 호출하세요."""
    
    # 📌 콘솔 디버깅용: 정말로 이 함수를 실행하기 위해 들어왔는지 터미널에 찍어줍니다.
    print(f"\n==============================================")
    print(f"🔊 [TOOL 호출됨!] 에이전트가 검색을 시작했습니다.")
    print(f"🔊 검색어(Query): '{query}'")
    print(f"==============================================\n")
    
    # 전역 변수 리스트에 보관하여 app.py 메인 스레드에서 화면에 그릴 수 있도록 함
    current_query_log.append(query)

    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return "검색 결과가 없습니다."
        return "\n\n".join([f"제목: {r['title']}\n내용: {r['body']}" for r in results])
    except Exception as e:
        return f"검색 중 오류가 발생했습니다: {str(e)}"

# 에이전트 인스턴스 생성
model_name = os.getenv("OLLAMA_MODEL", "gemma4:e4b")

life_coach_agent = Agent(
    name="Life Coach Agent",
    model=model_name,
    instructions=(
        "당신은 세계 최고의 라이프 코치입니다. "
        "사용자의 목표 달성과 긍정적인 습관 형성을 돕기 위해 전문적이고 동기부여가 되는 조언을 제공합니다. "
        "주의: '특정 기법', '명언', '최신 방법', '검색해줘' 등의 요청이 들어오면 절대로 혼자서 지어내지 마세요! "
        "반드시 'search_web' 도구를 호출하여 최신 웹 검색 결과를 얻은 뒤, 그 내용을 바탕으로 한국어로 친절하게 답변해야 합니다. "
        "도구가 반환한 정보들을 활용할 때 출처나 검색 결과를 자연스럽게 언급해주세요."
    ),
    tools=[search_web],
)
