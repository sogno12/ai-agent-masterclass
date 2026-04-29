import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List
from litellm import completion

# 환경 변수 로드 (.env 파일에서 OPENAI_BASE_URL 등을 가져옵니다)
load_dotenv()

# --- 1. 상태(State) 정의 ---
class Page(BaseModel):
    page_number: int
    text: str
    visual_prompt: str

class StoryState(BaseModel):
    theme: str
    pages: List[Page] = []

# --- 2. Story Writer Agent ---
def story_writer_node(state: StoryState) -> StoryState:
    print(f"\n🚀 '{state.theme}' 테마로 동화 작성을 시작합니다...")
    print("(로컬 LLM을 사용하므로 컴퓨터 성능에 따라 시간이 조금 걸릴 수 있습니다.)")
    
    # .env에서 설정한 모델명 가져오기
    model_name = os.getenv("OLLAMA_MODEL", "gemma2")
    
    # 시스템 프롬프트: JSON 구조 강제 및 SD용 영문 프롬프트 지시
    system_prompt = """
    너는 상상력이 풍부한 어린이 동화 작가야. 
    사용자가 제공하는 테마를 바탕으로 정확히 5페이지 분량의 동화를 작성해줘.
    
    [중요 규칙]
    1. 반드시 아래 JSON 형식으로만 응답해야 해. 마크다운(```json)이나 다른 설명은 절대 추가하지 마.
    2. 'visual_prompt'는 Stable Diffusion 이미지 생성을 위한 것이니, 반드시 쉼표로 구분된 짧은 영어 키워드로 작성해. (예: 1girl, cute rabbit, fantasy forest, highly detailed, masterpiece)
    3. 'text'는 어린이가 읽기 쉬운 따뜻한 한국어 문장으로 작성해.
    
    [JSON 출력 형태]
    {
      "pages": [
        {"page_number": 1, "text": "동화 내용 1...", "visual_prompt": "english keyword 1, english keyword 2..."},
        {"page_number": 2, "text": "동화 내용 2...", "visual_prompt": "english keyword 1, english keyword 2..."},
        {"page_number": 3, "text": "동화 내용 3...", "visual_prompt": "english keyword 1, english keyword 2..."},
        {"page_number": 4, "text": "동화 내용 4...", "visual_prompt": "english keyword 1, english keyword 2..."},
        {"page_number": 5, "text": "동화 내용 5...", "visual_prompt": "english keyword 1, english keyword 2..."}
      ]
    }
    """
    
    try:
        # LiteLLM을 통해 Ollama 호출
        # 'openai/' 접두사를 붙이면 LiteLLM이 자동으로 OPENAI_BASE_URL(Ollama)로 연결합니다.
        response = completion(
            model=f"openai/{model_name}",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"테마: {state.theme}"}
            ],
            response_format={"type": "json_object"}
        )
        
        # 응답 텍스트 파싱
        result_text = response.choices[0].message.content
        
        # 간혹 LLM이 ```json 태그를 붙이는 경우를 대비한 안전 장치
        result_text = result_text.replace("```json", "").replace("```", "").strip()
        
        result_json = json.loads(result_text)
        
        # 파싱된 데이터를 State에 Pydantic 모델 리스트로 변환하여 저장
        state.pages = [Page(**page) for page in result_json.get("pages", [])]
        print("✅ 동화 작성이 완료되었습니다!")
        
    except json.JSONDecodeError:
        print("❌ LLM이 올바른 JSON 형태를 반환하지 않았습니다. 원본 응답을 확인하세요:")
        print(result_text)
    except Exception as e:
        print(f"❌ 동화 작성 중 오류 발생: {e}")
        
    return state

# --- 기존 import 아래에 추가 ---
import requests
import base64

# ... (기존 코드 유지) ...

# --- 3. Illustrator Agent (Stable Diffusion 연동) ---
def illustrator_node(state: StoryState) -> StoryState:
    print("\n🎨 [Illustrator Agent] 생성된 스토리를 바탕으로 삽화 작업을 시작합니다...")
    
    # .env에서 SD API 주소 가져오기
    sd_url = os.getenv("STABLE_DIFFUSION_URL", "http://127.0.0.1:7860/sdapi/v1/txt2img")
    
    # 이미지 저장 폴더 생성
    output_dir = "output_images"
    os.makedirs(output_dir, exist_ok=True)

    for page in state.pages:
        print(f"   ⏳ [Page {page.page_number}] 이미지 생성 중... (프롬프트: {page.visual_prompt[:30]}...)")
        
        # Stable Diffusion API 페이로드 구성
        payload = {
            "prompt": page.visual_prompt,
            "negative_prompt": "ugly, blurry, deformed, text, watermark, bad anatomy, bad proportions",
            "steps": 20, # 퀄리티를 높이려면 30~40으로 조정 (단, 속도 느려짐)
            "width": 768,
            "height": 512,
            "cfg_scale": 7
        }

        try:
            # SD API 호출
            response = requests.post(sd_url, json=payload, timeout=60) # 타임아웃 60초 설정
            response.raise_for_status()
            r = response.json()

            # Base64 이미지 데이터 디코딩
            image_data = base64.b64decode(r['images'][0])
            
            # 파일 저장
            file_path = os.path.join(output_dir, f"page_{page.page_number}.png")
            with open(file_path, "wb") as f:
                f.write(image_data)
                
            print(f"   ✅ 완료: {file_path} 저장됨")
            
        except requests.exceptions.ConnectionError:
            print("   ❌ 오류: Stable Diffusion API에 연결할 수 없습니다.")
            print("      (웹 UI가 켜져 있는지, --api 플래그가 설정되어 있는지 확인하세요.)")
            break # 연결 안 되면 루프 중단
        except Exception as e:
            print(f"   ❌ 이미지 생성 실패 (페이지 {page.page_number}): {e}")

    print("🎉 모든 삽화 작업이 완료되었습니다!")
    return state

# langgraph 임포트를 지우고, google.adk.graph로 변경합니다.
from google.adk.graph import StateGraph, END

# --- 4. ADK Graph (파이프라인) 연결 ---
workflow = StateGraph(StoryState)

workflow.add_node("story_writer", story_writer_node)
workflow.add_node("illustrator", illustrator_node)

workflow.set_entry_point("story_writer")
workflow.add_edge("story_writer", "illustrator")
workflow.add_edge("illustrator", END)

# ADK가 인식할 수 있는 형태로 컴파일합니다.
root_agent = workflow.compile()

# --- 테스트 코드 (파이프라인 실행) ---
if __name__ == "__main__":
    # 1. 테스트용 초기 State 생성
    test_theme = "별을 따러 우주로 간 아기 고양이"
    initial_state = StoryState(theme=test_theme)
    
    # 2. 에이전트 순차 실행 (순차적 파이프라인)
    print("="*50)
    print("📚 AI 동화책 제작 파이프라인 시작 📚")
    print("="*50)
    
    # Writer 노드 실행
    state_after_writing = story_writer_node(initial_state)
    
    # 페이지가 정상적으로 생성되었을 때만 그림 작업 시작
    if state_after_writing.pages:
        # Illustrator 노드 실행
        final_state = illustrator_node(state_after_writing)
        
        print("\n✨ 모든 작업이 완료되었습니다! 'output_images' 폴더를 확인해 보세요.")
    else:
        print("\n❌ 스토리 생성에 실패하여 이미지 작업을 진행하지 않습니다.")