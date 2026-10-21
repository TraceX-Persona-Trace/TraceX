from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class CreateInvestigationRequest(BaseModel):
    title: str
    description: Optional[str] = None
    mode: str = "demo"


class UpdateInvestigationRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    mode: Optional[str] = None


class InvestigationResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    mode: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvestigationListResponse(BaseModel):
    items: List[InvestigationResponse]
    total: int
