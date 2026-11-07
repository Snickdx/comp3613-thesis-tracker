from typing import Optional

from sqlmodel import Field, SQLModel


class Submission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pairing_id: int = Field(index=True)
    title: str
    content: str
    created_at: str
