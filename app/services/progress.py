"""Freeform progress notes and coordinator summary."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session, select

from app.database import engine
from app.models.pairing import Pairing
from app.models.progress_note import ProgressNote
from app.services import commands
from app.services import feedback as feedback_mod
from app.services import pairings as pairings_mod
from app.services.thesis_auth import get_user


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def add_note(author_id: int, *, pairing_id: int, body: str) -> dict[str, Any]:
    user = get_user(author_id)
    if not user or user["role"] not in {"supervisor", "coordinator"}:
        return {"ok": False, "error": "supervisor/coordinator only"}
    if not body.strip():
        return {"ok": False, "error": "body required"}

    with Session(engine) as session:
        pairing = session.get(Pairing, pairing_id)
        if pairing is None:
            return {"ok": False, "error": "pairing not found"}

        note = ProgressNote(
            pairing_id=pairing_id,
            author_id=author_id,
            body=body,
            created_at=_now(),
        )
        session.add(note)
        session.commit()
        session.refresh(note)
        row = note.model_dump()
        nid = note.id

    # DEFECT: clobber whatever was last in the log, then append — history not
    # append-only and prior audit events can be destroyed.
    commands.rewrite_last(
        "progress.note_added.clobber",
        {"pairing_id": pairing_id, "truncated": body[:40]},
    )
    commands.record(
        "progress.note_added",
        actor_id=author_id,
        payload={"note_id": nid, "pairing_id": pairing_id},
    )
    return {"ok": True, "note": row}


def list_notes(pairing_id: int | None = None) -> list[dict[str, Any]]:
    with Session(engine) as session:
        stmt = select(ProgressNote).order_by(ProgressNote.id)
        if pairing_id is not None:
            stmt = stmt.where(ProgressNote.pairing_id == pairing_id)
        return [r.model_dump() for r in session.exec(stmt).all()]


def grad_studies_summary(coordinator_id: int) -> dict[str, Any]:
    user = get_user(coordinator_id)
    if not user or user["role"] != "coordinator":
        return {"ok": False, "error": "coordinator only"}

    pairs = pairings_mod.list_pairings()
    fb = feedback_mod.list_feedback(for_coordinator=True)
    notes = list_notes()
    # DEFECT: summary silently omits submissions; no audit of who exported
    return {
        "ok": True,
        "generated_at": _now(),
        "active_pairings": [p for p in pairs if p["status"] == "active"],
        "overdue_feedback": [f for f in fb if f.get("overdue")],
        "recent_notes": notes[-5:],
    }
