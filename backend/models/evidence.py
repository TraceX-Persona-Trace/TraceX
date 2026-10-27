from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id"), nullable=False)
    source_type = Column(String, nullable=False)
    source_name = Column(String, nullable=False)
    source_url = Column(String, nullable=True)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    evidence_type = Column(String, nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    collected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    metadata_json = Column(Text, nullable=True)
    normalised_value = Column(String, nullable=True)  # Chunk 6: matchable canonical value

    investigation = relationship("Investigation", back_populates="evidence")
