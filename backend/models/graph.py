from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship as orm_relationship
from backend.database import Base


class GraphNode(Base):
    __tablename__ = "graph_nodes"

    id = Column(Integer, primary_key=True, index=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id"), nullable=False)
    node_type = Column(String, nullable=False)
    label = Column(String, nullable=False)
    external_id = Column(String, nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)
    metadata_json = Column(Text, nullable=True)

    investigation = orm_relationship("Investigation", back_populates="graph_nodes")


class GraphEdge(Base):
    __tablename__ = "graph_edges"

    id = Column(Integer, primary_key=True, index=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id"), nullable=False)
    source_node_id = Column(Integer, ForeignKey("graph_nodes.id"), nullable=False)
    target_node_id = Column(Integer, ForeignKey("graph_nodes.id"), nullable=False)
    edge_relationship = Column("relationship", String, nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    metadata_json = Column(Text, nullable=True)

    investigation = orm_relationship("Investigation", back_populates="graph_edges")
