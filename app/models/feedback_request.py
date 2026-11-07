from typing import Optional

from sqlmodel import Field, SQLModel


class FeedbackRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    submission_id: int = Field(index=True)
    supervisor_id: int = Field(index=True)
    due_date: str
    notes: Optional[str] = None
    status: str
    completed_at: Optional[str] = None
