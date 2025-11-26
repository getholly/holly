from datetime import datetime

from pydantic import BaseModel


class UserLLMApiKeySchema(BaseModel):
    id: int
    llm_id: int
    llm_name: str
    api_key: str  # Masked or partial
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class UserLLMApiKeyCreateSchema(BaseModel):
    llm_id: int
    api_key: str


class UserLLMApiKeyUpdateSchema(BaseModel):
    api_key: str
