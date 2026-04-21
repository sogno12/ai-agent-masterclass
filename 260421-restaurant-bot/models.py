# models.py
from pydantic import BaseModel
from typing import Optional


class UserAccountContext(BaseModel):
    customer_id: int
    user_name: str
    tier: str = "basic"
    email: Optional[str] = None  # premium entreprise

class InputGuardRailOutput(BaseModel):
    is_off_topic: bool
    reason: str

class HandoffData(BaseModel):
    to_agent_name: str
    reason: str
    issue_type: str
    issue_description: str