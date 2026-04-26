from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text
from app.core.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    process_id = Column(String, index=True, nullable=False)

    message = Column(Text, nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)