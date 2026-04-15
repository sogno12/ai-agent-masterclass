import os
import chromadb
from chromadb.utils import embedding_functions

# 서버의 OLLAMA 주소 가져오기 (app.py에서 load_dotenv됨)
ollama_api_url_v1 = os.getenv("OLLAMA_API_URL", "http://localhost:11434/v1")
# v1 호환 모드가 아닌 표준 ollama api 주소로 변환
ollama_base_url = ollama_api_url_v1.replace("/v1", "")
embedding_url = f"{ollama_base_url}/api/embeddings"

# 한국어 특화 임베딩 모델 사용 설정
embedding_model_name = "bona/bge-m3-korean:latest"

# ChromaDB 초기화 (로컬 디렉토리에 저장)
CHROMA_DB_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
os.makedirs(CHROMA_DB_DIR, exist_ok=True)
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

# Ollama Embedding Function 준비
ollama_ef = embedding_functions.OllamaEmbeddingFunction(
    url=embedding_url,
    model_name=embedding_model_name
)

# Collection 가져오기 또는 생성 (유사도 검색 시 코사인 거리 사용)
collection = chroma_client.get_or_create_collection(
    name="user_docs",
    embedding_function=ollama_ef,
    metadata={"hnsw:space": "cosine"}
)

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50):
    """간단한 텍스트 청킹(분할) 함수. 지정된 길이 단위로 자르되 겹치게(overlap) 분할합니다."""
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
        
    return chunks

def add_document(file_name: str, file_content: str):
    """텍스트 문서의 내용을 청킹하여 ChromaDB 측에 삽입합니다."""
    print(f"\n==============================================")
    print(f"📥 [RAG Service] 파일 업로드 및 임베딩 처리 시작: '{file_name}'")
    print(f"==============================================\n")
    
    chunks = chunk_text(file_content)
    
    if not chunks:
        print("⚠️ [RAG Service] 텍스트가 비어있어 저장하지 않습니다.")
        return
        
    ids = [f"{file_name}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": file_name} for _ in range(len(chunks))]
    
    # DB에 추가 (이미 존재하는 ID면 덮어쓰거나 무시될 수 있으나 여기선 덮어쓰기 형태 가능)
    # upsert를 사용하면 기존 데이터 갱신도 가능합니다.
    collection.upsert(
        documents=chunks,
        metadatas=metadatas,
        ids=ids
    )
    print(f"✅ [RAG Service] '{file_name}' -> 총 {len(chunks)}개의 의미 조각으로 분리되어 Vector DB에 저장 성공!\n")

def search_documents(query: str, n_results: int = 3):
    """
    쿼리를 이용해 Vector DB를 검색하고 가장 관련된 텍스트 조각들을 문자열로 반환합니다.
    """
    print(f"\n==============================================")
    print(f"🔍 [RAG Service] Vector DB 무의미망 검색 시작")
    print(f"🎯 검색 쿼리: '{query}'")
    print(f"==============================================\n")
    
    # 저장된 문서가 없다면 빈 문자열 반환
    if collection.count() == 0:
        print("⚠️ [RAG Service] DB가 비어있어 검색을 건너뜁니다.")
        return "현재 기록된(업로드된) 과거 일기나 목표 파일이 없습니다."
        
    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count()) # n_results가 전체 수보다 크면 에러날 수 있음 보호
    )
    
    # 결과 포맷팅
    documents = results['documents'][0]
    metadatas = results['metadatas'][0]
    
    if not documents:
        return "관련된 기록을 찾지 못했습니다."
        
    ret_lines = ["🔍 [검색된 과거 기록/목표 내용]"]
    for i, doc in enumerate(documents):
        source = metadatas[i].get('source', '알 수 없는 문서')
        ret_lines.append(f"--- 출처: {source} ---")
        ret_lines.append(doc)
        
    print(f"✅ [RAG Service] 검색 완료: {len(documents)}개의 관련 기록 조각을 인출하여 에이전트에게 전달합니다.\n")
    return "\n".join(ret_lines)
