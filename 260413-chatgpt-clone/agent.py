import os
from duckduckgo_search import DDGS
from agents import Agent, function_tool
from rag_service import search_documents

import requests # 추가: 외부 API(Stable Diffusion) 통신용
import base64   # 추가: 이미지 데이터 변환용
import time     # 추가: 이미지 파일명 생성용


# 비동기 스레드(asyncio)에서 실행되어 Streamlit 세션에 접근 못하는 문제를 피하기 위한 파이썬 리스트
current_query_log = []
current_file_search_log = []
current_image_log = []

@function_tool
def search_web(query: str) -> str:
    """사용자의 요청(명언, 최신 기법, 동기부여, 조언 등)에 답하기 위해 외부 웹 검색을 수행하는 도구입니다. 
    자신의 지식으로 지어내지 말고, 구체적인 정보나 명언을 요구받으면 반드시 이 도구를 호출하세요.
    ★주의: 사용자가 '나의 목표', '내 기록', '내가 쓴 글', '내 파일' 등을 언급하면 이 도구를 절대 사용하지 마세요!★"""
    
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
    """★가장 우선적으로 호출해야 하는 도구★ 
    사용자가 '내 목표', '내 파일', '나의 다짐', '내 루틴', '내가 올린 글' 등 본인의 개인적인 기록이나 과거 정보를 물어볼 때 무조건 이 도구를 먼저 호출하세요.
    사용자가 최근 자신의 목표 진행 상황, 어제/오늘의 일기, 혹은 개인적인 다짐 등을 묻거나 이를 바탕으로 조언을 구할 때 호출하는 도구입니다.
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

@function_tool
def generate_vision_board(prompt: str) -> str:
    """사용자가 '비전 보드', '동기부여 포스터', '이미지 만들어줘' 등을 요청할 때 호출하는 도구입니다.
    Stable Diffusion을 사용하여 이미지를 생성하고 로컬 파일 경로를 반환합니다.
    주의: prompt는 반드시 영어 키워드 중심으로 요약/번역해서 전달해야 좋은 결과가 나옵니다."""
    
    print(f"\n==============================================")
    print(f"🎨 [TOOL 호출됨!] 에이전트가 이미지 생성을 시작했습니다.")
    print(f"🎨 프롬프트(요청): '{prompt}'")
    print(f"==============================================\n")

    stable_diffusion_url = os.getenv("STABLE_DIFFUSION_URL", "http://127.0.0.1:7860/sdapi/v1/txt2img")

    # 1. 프롬프트 앞뒤에 귀여운 일러스트 스타일 주문을 강제로 붙입니다.
    cute_prompt = f"cute, flat vector illustration, chibi style, simple icon, white background, {prompt}"
    
    # Stable Diffusion API로 보낼 데이터
    payload = {
        "prompt": cute_prompt,
        "negative_prompt": "ugly, low quality, bad anatomy, missing fingers, blurry, text, watermark",
        "steps": 20,
        "width": 512,
        "height": 512
    }
    current_image_log.append(prompt)

    timeout_second = 180
    try:
        print(f"⏳ Stable Diffusion API에 이미지 생성을 요청합니다... (최대 {timeout_second}초 대기)")
        
        # timeout=60 을 추가하여 60초 이상 걸리면 무한정 멈춰있지 않고 에러를 내뿜게 합니다.
        response = requests.post(stable_diffusion_url, json=payload, timeout=timeout_second) 
        response.raise_for_status() 
        r = response.json()

        print(f"✅ 이미지 생성 완료! 데이터 디코딩 중...")
        image_data = base64.b64decode(r['images'][0])

        os.makedirs("output", exist_ok=True)
        filename = f"vision_board_{int(time.time())}.png"
        filepath = os.path.join("output", filename)

        with open(filepath, "wb") as f:
            f.write(image_data)
            
        print(f"💾 이미지 저장 완료: {filepath}")

        return f"이미지가 성공적으로 생성되었습니다. 파일 경로: {filepath}"
        
    except requests.exceptions.Timeout:
        print(f"❌ 에러: Stable Diffusion 응답이 너무 오래 걸립니다 ({timeout_second}초 초과).")
        return "이미지 생성 시간이 초과되었습니다. Stable Diffusion 서버 상태나 VRAM을 확인해주세요."
    except Exception as e:
        print(f"❌ 이미지 생성 중 오류: {str(e)}")
        return f"이미지 생성 중 오류가 발생했습니다: {str(e)}"

# 에이전트 인스턴스 생성
model_name = os.getenv("OLLAMA_MODEL", "gemma4:e4b")

life_coach_agent = Agent(
    name="Life Coach Agent",
    model=model_name,
    instructions=(
        "당신은 세계 최고의 라이프 코치입니다. "
        "사용자의 목표 달성과 긍정적인 습관 형성을 돕기 위해 맞춤형이고 동기부여가 되는 조언을 제공합니다. "
        "사용자가 과거 자신의 기록(일기, 개인 목표 등)에 대해 묻거나 조언을 구할 경우 가장 먼저 'search_personal_records' 도구를 호출하세요. "
        "그리고 '특정 기법', '명언', '최신 방법', '검색해줘' 등의 요청이 들어오면 반드시 'search_web' 도구를 호출하세요. "
        "만약 사용자가 목표를 시각화하고 싶어 하거나 '비전 보드', '동기부여 이미지/포스터' 생성을 요청하면 반드시 'generate_vision_board' 도구를 호출하세요. "
        "★중요(이미지 도구 사용 시 주의사항): 추상적인 감정이나 복잡한 배경을 프롬프트로 넘기지 마세요. 사용자의 목표를 상징하는 '단 하나의 귀여운 사물이나 동물'을 정해서, 아주 짧고 명확한 영어 키워드(예: 'a cute running cat', 'a small apple', 'a dumbbell')로만 번역해서 도구에 넘기세요.★ "
        "도구가 반환한 정보, 개인 기록, 생성된 이미지 경로를 활용하여 한국어로 친절하고 힘차게 답변해주세요."
    ),
    tools=[search_web, search_personal_records, generate_vision_board], # 도구 추가
)
