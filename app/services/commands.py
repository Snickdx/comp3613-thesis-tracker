"""
Pseudo command / audit trail — the intended refactor target.

Domain mutations currently happen inline in services. This module pretends to
be a Command history but:
  - logging is optional and often skipped by callers
  - payloads are free-form strings, not structured command objects
  - there is no execute()/undo() — only append-after-the-fact notes
  - some entries omit actor_id or use the wrong actor

Ideal student fix: Command objects (pair, submit, request_feedback,
complete_feedback, add_progress_note, …) run through an invoker that appends
an immutable audit event for every successful execution.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session, select

from app.database import engine
from app.models.event_log import EventLog


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def record(
    action: str,
    *,
    actor_id: int | None = None,
    payload: dict[str, Any] | None = None,
    silent: bool = False,
) -> None:
    """Best-effort append. Callers may forget this entirely."""
    if silent:
        # DEFECT: "silent" path used to skip audit for "internal" updates
        return
    with Session(engine) as session:
        session.add(
            EventLog(
                action=action,
                actor_id=actor_id,
                payload=json.dumps(payload or {}),
                created_at=_now(),
            )
        )
        session.commit()


def history(*, limit: int = 100) -> list[dict[str, Any]]:
    with Session(engine) as session:
        rows = session.exec(
            select(EventLog).order_by(EventLog.id.desc()).limit(limit)
        ).all()
        items = [row.model_dump() for row in rows]
    out = []
    for item in items:
        try:
            item["payload"] = json.loads(item["payload"] or "{}")
        except json.JSONDecodeError:
            pass
        out.append(item)
    return out


def rewrite_last(action: str, payload: dict[str, Any]) -> None:
    """
    DEFECT: mutable history — last row can be overwritten, so the log is not
    a trustworthy audit trail.
    """
    with Session(engine) as session:
        last = session.exec(
            select(EventLog).order_by(EventLog.id.desc()).limit(1)
        ).first()
        if last:
            last.action = action
            last.payload = json.dumps(payload)
            session.add(last)
            session.commit()
