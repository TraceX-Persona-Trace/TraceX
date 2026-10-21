from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Correlation(Base):
    __tablename__ = "correlations"

    id = Column(Integer, primary_key=True, index=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id"), nullable=False)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=True)
    correlation_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    investigation = relationship("Investigation", back_populates="correlations")
