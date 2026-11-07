"""Seed roles, one pairing, and sample feedback for the thesis-tracker scenario."""

from __future__ import annotations

from sqlmodel import Session, select

from app.database import drop_all, engine, ensure_db_and_tables
from app.models.feedback_request import FeedbackRequest
from app.models.pairing import Pairing
from app.models.submission import Submission
from app.models.user import User
from app.utilities.security import encrypt_password

USERS = [
    # username, email, password, role, display_name, max_students
    ("coord", "coord@example.com", "coord-dev", "coordinator", "PG Coordinator", None),
    ("super1", "super1@example.com", "super-dev", "supervisor", "Dr. Supervisor", 2),
    ("super2", "super2@example.com", "super-dev", "supervisor", "Dr. Capacity Full", 1),
    ("student1", "student1@example.com", "stud-dev", "student", "Student One", None),
    ("student2", "student2@example.com", "stud-dev", "student", "Student Two", None),
    ("student3", "student3@example.com", "stud-dev", "student", "Student Three", None),
]


def seed(*, reset: bool = False) -> None:
    import app.models  # noqa: F401

    if reset:
        try:
            drop_all()
        except Exception:
            pass
    ensure_db_and_tables()

    with Session(engine) as session:
        existing = session.exec(select(User)).first()
        if existing and not reset:
            return

        for username, email, password, role, display_name, cap in USERS:
            session.add(
                User(
                    username=username,
                    email=email,
                    password=encrypt_password(password),
                    role=role,
                    display_name=display_name,
                    max_students=cap,
                )
            )
        session.commit()

        student = session.exec(
            select(User).where(User.email == "student1@example.com")
        ).one()
        supervisor = session.exec(
            select(User).where(User.email == "super1@example.com")
        ).one()

        pairing = Pairing(
            student_id=student.id,
            supervisor_id=supervisor.id,
            status="active",
            created_at="2099-01-01T10:00:00+00:00",
        )
        session.add(pairing)
        session.commit()
        session.refresh(pairing)

        submission = Submission(
            pairing_id=pairing.id,
            title="Chapter 1 draft",
            content="Intro text…",
            created_at="2099-01-05T10:00:00+00:00",
        )
        session.add(submission)
        session.commit()
        session.refresh(submission)

        session.add(
            FeedbackRequest(
                submission_id=submission.id,
                supervisor_id=supervisor.id,
                due_date="2020-01-01",
                notes=None,
                status="open",
                completed_at=None,
            )
        )
        session.commit()
