"""Thesis-tracker scenario JSON API (OpenAPI /docs)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import commands, feedback, pairings, progress
from app.services import thesis_auth as auth

router = APIRouter(tags=["thesis-tracker"])


class LoginBody(BaseModel):
    email: str
    password: str


class PairingBody(BaseModel):
    student_id: int
    supervisor_id: int
    actor_id: int = Field(description="Acting user id (demo auth)")


class SubmitBody(BaseModel):
    pairing_id: int
    title: str
    content: str
    actor_id: int


class FeedbackRequestBody(BaseModel):
    submission_id: int
    due_date: str = Field(description="ISO date YYYY-MM-DD")
    actor_id: int


class FeedbackCompleteBody(BaseModel):
    notes: str = ""
    actor_id: int


class ProgressBody(BaseModel):
    pairing_id: int
    body: str
    actor_id: int


def _ok_or_400(result: dict[str, Any]) -> dict[str, Any]:
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/auth/login")
def login(body: LoginBody) -> dict[str, Any]:
    user = auth.login(body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="invalid credentials")
    return {"user": user}


@router.get("/pairings")
def list_pairings() -> dict[str, Any]:
    return {"pairings": pairings.list_pairings()}


@router.post("/pairings")
def create_pairing(body: PairingBody) -> dict[str, Any]:
    return _ok_or_400(
        pairings.create_pairing(body.actor_id, body.student_id, body.supervisor_id)
    )


@router.post("/submissions")
def submit(body: SubmitBody) -> dict[str, Any]:
    return _ok_or_400(
        feedback.submit_work(
            body.actor_id,
            pairing_id=body.pairing_id,
            title=body.title,
            content=body.content,
        )
    )


@router.get("/submissions")
def list_submissions(pairing_id: int | None = None) -> dict[str, Any]:
    return {"submissions": feedback.list_submissions(pairing_id)}


@router.post("/feedback")
def request_feedback(body: FeedbackRequestBody) -> dict[str, Any]:
    return _ok_or_400(
        feedback.request_feedback(
            body.actor_id,
            submission_id=body.submission_id,
            due_date=body.due_date,
        )
    )


@router.post("/feedback/{feedback_id}/complete")
def complete_feedback(feedback_id: int, body: FeedbackCompleteBody) -> dict[str, Any]:
    return _ok_or_400(
        feedback.complete_feedback(body.actor_id, feedback_id, notes=body.notes)
    )


@router.get("/feedback")
def list_feedback(coordinator_view: bool = False) -> dict[str, Any]:
    return {"feedback": feedback.list_feedback(for_coordinator=coordinator_view)}


@router.post("/progress/notes")
def add_progress(body: ProgressBody) -> dict[str, Any]:
    return _ok_or_400(
        progress.add_note(body.actor_id, pairing_id=body.pairing_id, body=body.body)
    )


@router.get("/progress/notes")
def list_progress(pairing_id: int | None = None) -> dict[str, Any]:
    return {"notes": progress.list_notes(pairing_id)}


@router.get("/coordinator/summary")
def summary(actor_id: int) -> dict[str, Any]:
    result = progress.grad_studies_summary(actor_id)
    if not result.get("ok"):
        raise HTTPException(status_code=403, detail=result.get("error"))
    return result


@router.get("/audit")
def audit(limit: int = 100) -> dict[str, Any]:
    return {"events": commands.history(limit=limit)}
