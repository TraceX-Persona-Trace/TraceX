from typing import Optional
from pydantic import BaseModel


class GraphNodeResponse(BaseModel):
    id: int
    investigation_id: int
    node_type: str
    label: str
    external_id: Optional[str]
    confidence: float
    metadata_json: Optional[str]

    model_config = {"from_attributes": True}


class GraphEdgeResponse(BaseModel):
    id: int
    investigation_id: int
    source_node_id: int
    target_node_id: int
    edge_relationship: str
    confidence: float
    metadata_json: Optional[str]

    model_config = {"from_attributes": True}
