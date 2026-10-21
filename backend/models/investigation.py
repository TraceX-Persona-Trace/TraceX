from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from database import Base


class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="active")
    mode = Column(String, nullable=False, default="demo")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    evidence = relationship("Evidence", back_populates="investigation", cascade="all, delete-orphan")
    correlations = relationship("Correlation", back_populates="investigation", cascade="all, delete-orphan")
    graph_nodes = relationship("GraphNode", back_populates="investigation", cascade="all, delete-orphan")
    graph_edges = relationship("GraphEdge", back_populates="investigation", cascade="all, delete-orphan")
