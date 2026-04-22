"""
DB_Functions
------------
All database operations live here. Route handlers call these, not the models
directly, so swapping/extending storage later stays simple.
"""

from datetime import date, timedelta
from typing import Sequence

import click
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

from .models import db, User, Client, Procedure


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
def init_db(app):
    """Bind SQLAlchemy to the Flask app, create tables, register CLI cmds."""
    db.init_app(app)
    with app.app_context():
        db.create_all()
    _register_cli(app)


def _register_cli(app):
    """Expose `flask seed-admin` so you can create the first admin user."""

    @app.cli.command("seed-admin")
    @click.option("--username", prompt=True, help="Admin username")
    @click.option(
        "--password",
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
        help="Admin password",
    )
    def seed_admin(username, password):
        """Create the very first admin user. Safe to re-run (idempotent)."""
        existing = User.query.filter_by(username=username).first()
        if existing:
            if existing.is_admin:
                click.echo(f"✓ User '{username}' already exists and is admin.")
                return
            existing.is_admin = True
            db.session.commit()
            click.echo(f"✓ User '{username}' promoted to admin.")
            return

        user = create_user(username, password, is_admin=True)
        if user:
            click.echo(f"✓ Admin user '{username}' created.")
        else:
            click.echo("✗ Could not create admin user.")


# ---------------------------------------------------------------------------
# Users / auth
# ---------------------------------------------------------------------------
def create_user(username: str, password: str, is_admin: bool = False) -> User | None:
    """Create a user. Returns None if username is taken or inputs are empty."""
    username = (username or "").strip()
    if not username or not password:
        return None
    if User.query.filter_by(username=username).first():
        return None

    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        is_admin=is_admin,
    )
    db.session.add(user)
    db.session.commit()
    return user


def verify_user(username: str, password: str) -> User | None:
    """Return the User if credentials are valid, else None."""
    user = User.query.filter_by(username=(username or "").strip()).first()
    if user and check_password_hash(user.password_hash, password):
        return user
    return None


def get_user(user_id: int) -> User | None:
    return User.query.get(user_id)


def list_users() -> list[User]:
    return User.query.order_by(User.username).all()


def delete_user(user_id: int) -> bool:
    user = User.query.get(user_id)
    if not user:
        return False
    db.session.delete(user)
    db.session.commit()
    return True


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------
def create_client(user_id: int, name: str) -> Client | None:
    name = (name or "").strip()
    if not name:
        return None
    client = Client(user_id=user_id, name=name)
    db.session.add(client)
    db.session.commit()
    return client


def get_clients_for_user(user_id: int) -> list[Client]:
    return (
        Client.query
        .filter_by(user_id=user_id)
        .order_by(Client.created_at.desc())
        .all()
    )


def get_client(client_id: int, user_id: int) -> Client | None:
    """Scoped lookup — users can only see their own clients."""
    return Client.query.filter_by(id=client_id, user_id=user_id).first()


def delete_client(client_id: int, user_id: int) -> bool:
    client = get_client(client_id, user_id)
    if not client:
        return False
    db.session.delete(client)
    db.session.commit()
    return True


# ---------------------------------------------------------------------------
# Procedures / scheduling
# ---------------------------------------------------------------------------
def calculate_procedure_dates(
    start_date: date,
    intervals: Sequence[int],
) -> list[date]:
    """
    Given a start date and a list of intervals (gap in days from the previous
    procedure), return the list of scheduled dates.

    Procedure 1 is ALWAYS on start_date.
    Procedure 2 is on start_date + intervals[0].
    Procedure 3 is on start_date + intervals[0] + intervals[1]. ...

    `intervals` therefore has length (number_of_procedures - 1).

    Example — 4 procedures, 30 days apart:
        start=2026-01-01, intervals=[30, 30, 30]
        -> [2026-01-01, 2026-01-31, 2026-03-02, 2026-04-01]
    """
    dates = [start_date]
    running = start_date
    for gap in intervals:
        running = running + timedelta(days=int(gap))
        dates.append(running)
    return dates


def create_schedule(
    client_id: int,
    user_id: int,
    start_date: date,
    intervals: Sequence[int],
    replace_existing: bool = True,
) -> list[Procedure]:
    """
    Persist a full schedule for a client.

    `intervals` has length (number_of_procedures - 1).
    For fixed-interval scheduling pass [30, 30, 30, ...] — for custom
    intervals later, pass whatever the UI collects.
    """
    client = get_client(client_id, user_id)
    if not client:
        return []

    if replace_existing:
        Procedure.query.filter_by(client_id=client_id).delete()

    dates = calculate_procedure_dates(start_date, intervals)
    # interval stored with each procedure = gap from the PREVIOUS one
    gaps = [0] + list(intervals)

    procedures = [
        Procedure(
            client_id=client_id,
            sequence_number=i + 1,
            scheduled_date=d,
            interval_days=gaps[i],
        )
        for i, d in enumerate(dates)
    ]
    db.session.add_all(procedures)
    db.session.commit()
    return procedures


def get_procedures_for_client(client_id: int, user_id: int) -> list[Procedure]:
    if not get_client(client_id, user_id):
        return []
    return (
        Procedure.query
        .filter_by(client_id=client_id)
        .order_by(Procedure.sequence_number)
        .all()
    )


def toggle_procedure_completed(procedure_id: int, user_id: int) -> Procedure | None:
    """Flip the completed flag on a procedure that the user owns."""
    proc = (
        db.session.query(Procedure)
        .join(Client, Client.id == Procedure.client_id)
        .filter(Procedure.id == procedure_id, Client.user_id == user_id)
        .first()
    )
    if not proc:
        return None
    proc.completed = not proc.completed
    db.session.commit()
    return proc
