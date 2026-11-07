# COMP 3613 Thesis Tracker (Phase 2 starter)

Flawed baseline **0.2.0** built on [uwidcit/faststart](https://github.com/uwidcit/faststart) (`96ccfce`).

FastStart provides the SSR shell, JWT cookie auth, SQLModel, `manage.py`, and Render/Docker wiring. The thesis-tracker scenario adds domain models/services and a JSON API under `/api` (see `/docs`).

## Quick start

```text
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Windows: Copy-Item .env.example .env
python manage.py init
python manage.py run
```

Open http://127.0.0.1:5000 — SSR auth shell; scenario JSON under `/api` and OpenAPI at `/docs`.

## Seeded API accounts

| Email | Password | Role |
| --- | --- | --- |
| `coord@example.com` | `coord-dev` | coordinator |
| `super1@example.com` | `super-dev` | supervisor (max 2 students) |
| `super2@example.com` | `super-dev` | supervisor (max 1 student) |
| `student1@example.com` | `stud-dev` | student (paired with `super1`) |
| `student2@example.com` | `stud-dev` | student |
| `student3@example.com` | `stud-dev` | student |

JSON login: `POST /api/auth/login` with `{"email","password"}`. Domain routes take an `actor_id` (demo auth) in the body or query string.

## Student brief

See [`ASSIGNMENT.md`](ASSIGNMENT.md) and [`docs/ACCEPTANCE.md`](docs/ACCEPTANCE.md).

## Tests

```bash
python -m pytest tests -q
```
