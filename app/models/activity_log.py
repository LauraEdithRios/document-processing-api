from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String, Text
from app.core.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    process_id = Column(String, index=True, nullable=False)
    message = Column(Text, nullable=False)
    level = Column(String, nullable=False, default="INFO")  # INFO, WARNING, ERROR
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))