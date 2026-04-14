import sqlite3
import uuid
import datetime
from typing import List, Dict

class SQLiteSession:
    def __init__(self, db_path="sessions.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            # 세션 테이블 (방 목록)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # 메시지 테이블 (방 안에 속한 채팅 내역)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )
            ''')
            conn.commit()

    def get_all_sessions(self) -> List[Dict]:
        """모든 세션을 최근 생성순으로 가져옵니다."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT session_id, title, created_at FROM sessions ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    def create_session(self, title: str = None) -> str:
        """새로운 대화 세션을 생성하고 ID를 반환합니다."""
        session_id = str(uuid.uuid4())
        if not title:
            # Time-based default title
            now_str = datetime.datetime.now().strftime("%y-%m-%d %H:%M")
            title = f"새로운 대화 ({now_str})"
            
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO sessions (session_id, title) VALUES (?, ?)", (session_id, title))
            conn.commit()
        return session_id

    def add_message(self, session_id: str, role: str, content: str):
        """특정 세션에 새로운 메시지를 추가합니다."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)", 
                         (session_id, role, content))
            conn.commit()

    def get_messages(self, session_id: str) -> List[Dict]:
        """특정 세션의 대화 내용을 모두 불러옵니다."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC", 
                                (session_id,)).fetchall()
            return [{"role": r["role"], "content": r["content"]} for r in rows]

    def clear_session(self, session_id: str):
        """특정 세션의 모든 메시지 기록을 날려버립니다 (초기화)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.commit()

    def reset_all(self):
        """데이터베이스의 모든 세션과 대화 기록을 완전히 파괴합니다."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DROP TABLE IF EXISTS messages")
            conn.execute("DROP TABLE IF EXISTS sessions")
            conn.commit()
        self._init_db()
