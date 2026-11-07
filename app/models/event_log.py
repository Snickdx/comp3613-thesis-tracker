from typing import Optional

from sqlmodel import Field, SQLModel


class EventLog(SQLModel, table=True):
    """Pseudo "command history" — incomplete and mutable in the baseline."""

    __tablename__ = "event_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    action: str
    actor_id: Optional[int] = None
    payload: Optional[str] = None
    created_at: str
