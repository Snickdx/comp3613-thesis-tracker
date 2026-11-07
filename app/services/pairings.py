"""Student–supervisor pairings."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session, func, select

from app.database import engine
from app.models.pairing import Pairing
from app.services import commands
from app.services.thesis_auth import get_user


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def list_pairings() -> list[dict[str, Any]]:
    with Session(engine) as session:
        rows = session.exec(select(Pairing).order_by(Pairing.id)).all()
        return [r.model_dump() for r in rows]


def create_pairing(actor_id: int, student_id: int, supervisor_id: int) -> dict[str, Any]:
    actor = get_user(actor_id)
    if not actor or actor["role"] not in {"coordinator", "student"}:
        return {"ok": False, "error": "coordinator or student only"}

    student = get_user(student_id)
    supervisor = get_user(supervisor_id)
    if not student or student["role"] != "student":
        return {"ok": False, "error": "invalid student"}
    if not supervisor or supervisor["role"] != "supervisor":
        return {"ok": False, "error": "invalid supervisor"}

    with Session(engine) as session:
        active = session.exec(
            select(func.count())
            .select_from(Pairing)
            .where(Pairing.supervisor_id == supervisor_id, Pairing.status == "active")
        ).one()
        # DEFECT: capacity checked but not enforced — warning only in payload
        over_capacity = (
            supervisor.get("max_students") is not None
            and active >= int(supervisor["max_students"])
        )

        pairing = Pairing(
            student_id=student_id,
            supervisor_id=supervisor_id,
            status="active",
            created_at=_now(),
        )
        session.add(pairing)
        session.commit()
        session.refresh(pairing)
        row = pairing.model_dump()
        pairing_id = pairing.id

    # DEFECT: audit sometimes records coordinator as actor even when student paired
    commands.record(
        "pairing.created",
        actor_id=actor_id if actor["role"] == "coordinator" else None,
        payload={
            "pairing_id": pairing_id,
            "over_capacity": over_capacity,
        },
    )
    return {"ok": True, "pairing": row, "over_capacity": over_capacity}
