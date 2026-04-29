import os
import json
import requests
import base64
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List
from litellm import completion

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
    model_name = os.getenv("OLLAMA_MODEL", "gemma2")
    
    system_prompt = """
    너는 상상력이 풍부한 어린이 동화 작가야. 
    사용자가 제공하는 테마를 바탕으로 정확히 5페이지 분량의 동화를 작성해줘.
    
    [중요 규칙]
    1. 반드시 아래 JSON 형식으로만 응답해야 해. 마크다운(```json)이나 다른 설명은 절대 추가하지 마.
    2. 'visual_prompt'는 Stable Diffusion 이미지 생성을 위한 것이니, 반드시 쉼표로 구분된 짧은 영어 키워드로 작성해.
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
        response = completion(
            model=f"openai/{model_name}",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"테마: {state.theme}"}
            ],
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result_text = result_text.replace("```json", "").replace("```", "").strip()
        result_json = json.loads(result_text)
        state.pages = [Page(**page) for page in result_json.get("pages", [])]
        print("✅ 동화 작성이 완료되었습니다!")
        
    except Exception as e:
        print(f"❌ 동화 작성 중 오류 발생: {e}")
        
    return state

# --- 3. Illustrator Agent ---
def illustrator_node(state: StoryState) -> StoryState:
    print("\n🎨 [Illustrator Agent] 삽화 작업을 시작합니다...")
    sd_url = os.getenv("STABLE_DIFFUSION_URL", "[http://127.0.0.1:7860/sdapi/v1/txt2img](http://127.0.0.1:7860/sdapi/v1/txt2img)")
    
    # 💥 중요: ADK Web UI와 통신할 때는 루트 경로를 기준으로 output_images 폴더를 잡습니다.
    output_dir = "output_images"
    os.makedirs(output_dir, exist_ok=True)

    for page in state.pages:
        print(f"   ⏳ [Page {page.page_number}] 이미지 생성 중...")
        payload = {
            "prompt": page.visual_prompt,
            "negative_prompt": "ugly, blurry, deformed, text, watermark, bad anatomy",
            "steps": 20,
            "width": 768,
            "height": 512,
            "cfg_scale": 7
        }

        try:
            response = requests.post(sd_url, json=payload, timeout=60)
            response.raise_for_status()
            r = response.json()
            image_data = base64.b64decode(r['images'][0])
            
            file_path = os.path.join(output_dir, f"page_{page.page_number}.png")
            with open(file_path, "wb") as f:
                f.write(image_data)
            print(f"   ✅ 완료: {file_path} 저장됨")
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
