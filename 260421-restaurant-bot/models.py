# models.py
from pydantic import BaseModel
from typing import Optional

class UserAccountContext(BaseModel):
    customer_id: int
    user_name: str
    tier: str = "basic"
    email: Optional[str] = None

class InputGuardRailOutput(BaseModel):
    is_off_topic: bool
    is_inappropriate: bool  # 부적절한 언어 필터링 추가
    reason: str

class OutputGuardRailOutput(BaseModel): # 출력 검수용 모델 추가
    is_professional: bool
    is_secure: bool
    reason: str

class HandoffData(BaseModel):
    to_agent_name: str
    reason: str
    issue_type: str
    issue_description: str