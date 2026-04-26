from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class ProcessResult(Base):
    __tablename__ = "process_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    process_id = Column(String, index=True, nullable=False)

    total_words = Column(Integer, nullable=False, default=0)
    total_lines = Column(Integer, nullable=False, default=0)
    total_characters = Column(Integer, nullable=False, default=0)

    most_frequent_words = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    files_processed = Column(Text, nullable=True)