from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from app.core.database import Base


class Process(Base):
    __tablename__ = "processes"

    id = Column(String, primary_key=True, index=True)

    status = Column(String, nullable=False, default="PENDING")

    total_files = Column(Integer, nullable=False, default=0)
    processed_files = Column(Integer, nullable=False, default=0)
    percentage = Column(Integer, nullable=False, default=0)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    error_message = Column(String, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)