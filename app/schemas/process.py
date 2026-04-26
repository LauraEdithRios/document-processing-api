from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class ProgressResponse(BaseModel):
    total_files: int
    processed_files: int
    percentage: int


class ProcessResultResponse(BaseModel):
    total_words: int
    total_lines: int
    total_characters: int
    most_frequent_words: List[str]
    files_processed: List[str]
    summary: Optional[str] = None


class ProcessResponse(BaseModel):
    process_id: str
    status: str
    progress: ProgressResponse
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    results: Optional[ProcessResultResponse] = None


class ProcessListItemResponse(BaseModel):
    process_id: str
    status: str
    progress: ProgressResponse
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None