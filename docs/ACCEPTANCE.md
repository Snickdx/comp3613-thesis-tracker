# Thesis Tracker — public acceptance criteria

Derived from elicitable stakeholder needs (Phase 1). Instructor private defects are **not** listed here.

## Roles

1. Product supports **student**, **supervisor**, and **coordinator** behaviours (even if chat personas are only coordinator + supervisor).
2. Passwords are stored hashed; login never returns password material.

## Pairings

3. Student–supervisor pairings are recorded when agreed; coordinator can list active pairings.
4. Supervisor capacity is enforced (cannot silently exceed `max_students`).

## Submissions & feedback

5. Students can submit work against their pairing.
6. Supervisors record in-app feedback **notes** with a configurable due date; empty notes cannot close feedback.
7. Overdue open feedback is correctly flagged for the coordinator (past due ⇒ overdue; future due ⇒ not overdue).

## Progress

8. Progress is freeform notes (no required milestone checklist).
9. Coordinator can produce a progress summary suitable for grad studies (pairings, feedback pressure, recent notes).

## Audit

10. Domain actions (pair, submit, request/complete feedback, add progress note, export summary) leave an **append-only** audit/command history with actor and payload — not silent skips or rewritten rows.
