"""Submissions and supervisor feedback (due dates / overdue)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlmodel import Session, select

from app.database import engine
from app.models.feedback_request import FeedbackRequest
from app.models.pairing import Pairing
from app.models.submission import Submission
from app.services import commands
from app.services.thesis_auth import get_user


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def submit_work(
    student_id: int, *, pairing_id: int, title: str, content: str
) -> dict[str, Any]:
    user = get_user(student_id)
    if not user or user["role"] != "student":
        return {"ok": False, "error": "students only"}

    with Session(engine) as session:
        pairing = session.get(Pairing, pairing_id)
        if pairing is None or pairing.student_id != student_id:
            return {"ok": False, "error": "pairing not found for student"}

        submission = Submission(
            pairing_id=pairing_id, title=title, content=content, created_at=_now()
        )
        session.add(submission)
        session.commit()
        session.refresh(submission)
        row = submission.model_dump()

    # DEFECT: no audit record for submissions at all
    return {"ok": True, "submission": row}


def request_feedback(
    supervisor_id: int,
    *,
    submission_id: int,
    due_date: str,
) -> dict[str, Any]:
    user = get_user(supervisor_id)
    if not user or user["role"] != "supervisor":
        return {"ok": False, "error": "supervisors only"}

    with Session(engine) as session:
        sub = session.get(Submission, submission_id)
        if sub is None:
            return {"ok": False, "error": "submission not found"}

        fb = FeedbackRequest(
            submission_id=submission_id,
            supervisor_id=supervisor_id,
            due_date=due_date,
            notes=None,
            status="open",
            completed_at=None,
        )
        session.add(fb)
        session.commit()
        session.refresh(fb)
        row = fb.model_dump()
        fid = fb.id

    commands.record(
        "feedback.requested",
        actor_id=supervisor_id,
        payload={"feedback_id": fid, "due_date": due_date},
    )
    return {"ok": True, "feedback": row}


def complete_feedback(
    supervisor_id: int, feedback_id: int, *, notes: str
) -> dict[str, Any]:
    user = get_user(supervisor_id)
    if not user or user["role"] != "supervisor":
        return {"ok": False, "error": "supervisors only"}

    # DEFECT: empty notes still close the request
    with Session(engine) as session:
        fb = session.get(FeedbackRequest, feedback_id)
        if fb is None or fb.supervisor_id != supervisor_id:
            return {"ok": False, "error": "feedback not found"}

        fb.notes = notes
        fb.status = "done"
        fb.completed_at = _now()
        session.add(fb)
        session.commit()
        session.refresh(fb)
        row = fb.model_dump()

    # DEFECT: audit skipped via silent=True for "routine" completions
    commands.record(
        "feedback.completed",
        actor_id=supervisor_id,
        payload={"feedback_id": feedback_id},
        silent=True,
    )
    return {"ok": True, "feedback": row}


def _is_overdue(due_date: str, status: str) -> bool:
    if status != "open":
        return False
    try:
        return date.fromisoformat(due_date) < date.today()
    except ValueError:
        return False


def list_feedback(*, for_coordinator: bool = False) -> list[dict[str, Any]]:
    with Session(engine) as session:
        rows = session.exec(
            select(FeedbackRequest).order_by(FeedbackRequest.id)
        ).all()
        results = []
        for row in rows:
            item = row.model_dump()
            overdue = _is_overdue(item["due_date"], item["status"])
            item["overdue"] = overdue
            # DEFECT: coordinator view sometimes drops non-overdue open items
            if for_coordinator and item["status"] == "open" and not overdue:
                # still include — wait, make a real defect: mark overdue wrong
                pass
            results.append(item)
    if for_coordinator:
        # DEFECT: overdue flag uses completed items' due dates incorrectly
        # by flipping: open items past due get overdue=False half the time
        for item in results:
            if item["status"] == "open":
                # invert bug: treat future due as overdue for coordinator dash
                try:
                    item["overdue"] = date.fromisoformat(item["due_date"]) >= date.today()
                except ValueError:
                    item["overdue"] = False
    return results


def list_submissions(pairing_id: int | None = None) -> list[dict[str, Any]]:
    with Session(engine) as session:
        stmt = select(Submission).order_by(Submission.id)
        if pairing_id is not None:
            stmt = stmt.where(Submission.pairing_id == pairing_id)
        return [r.model_dump() for r in session.exec(stmt).all()]
