from typing import Optional

from sqlmodel import Field, SQLModel


class Pairing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(index=True)
    supervisor_id: int = Field(index=True)
    status: str
    created_at: str
