"""
DB_Functions
------------
All database operations live here. Route handlers call these, not the models
directly.
"""

from datetime import date, timedelta
from typing import Sequence

import click
from werkzeug.security import generate_password_hash, check_password_hash

from .models import db, User, Client, Procedure, ProcedureTemplate, ClientTreatment


# Cascade modes for reschedule_session()
CASCADE_NONE = "none"              # only the chosen session moves
CASCADE_SHIFT = "shift"            # upcoming sessions slide by the same delta
CASCADE_RECALCULATE = "recalc"     # upcoming sessions rebuilt from new_date
                                   #   using the treatment's default interval
VALID_CASCADE_MODES = {CASCADE_NONE, CASCADE_SHIFT, CASCADE_RECALCULATE}


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
    _register_cli(app)


def _register_cli(app):
    @app.cli.command("seed-admin")
    @click.option("--username", prompt=True, help="Admin username")
    @click.option(
        "--password", prompt=True, hide_input=True, confirmation_prompt=True,
        help="Admin password",
    )
    def seed_admin(username, password):
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
        click.echo(
            f"✓ Admin user '{username}' created." if user
            else "✗ Could not create admin user."
        )


# ---------------------------------------------------------------------------
# Users / auth
# ---------------------------------------------------------------------------
def create_user(username: str, password: str, is_admin: bool = False) -> User | None:
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
    return Client.query.filter_by(id=client_id, user_id=user_id).first()


def delete_client(client_id: int, user_id: int) -> bool:
    client = get_client(client_id, user_id)
    if not client:
        return False
    db.session.delete(client)
    db.session.commit()
    return True


# ---------------------------------------------------------------------------
# Procedure templates (shared across users)
# ---------------------------------------------------------------------------
def list_templates() -> list[ProcedureTemplate]:
    return ProcedureTemplate.query.order_by(ProcedureTemplate.name).all()


def get_template(template_id: int) -> ProcedureTemplate | None:
    return ProcedureTemplate.query.get(template_id)


def create_template(name: str, default_interval_days: int) -> ProcedureTemplate | None:
    name = (name or "").strip()
    if not name or default_interval_days < 1:
        return None
    existing = ProcedureTemplate.query.filter(
        db.func.lower(ProcedureTemplate.name) == name.lower()
    ).first()
    if existing:
        return None
    tpl = ProcedureTemplate(name=name, default_interval_days=int(default_interval_days))
    db.session.add(tpl)
    db.session.commit()
    return tpl


def update_template(template_id: int, name: str, default_interval_days: int) -> ProcedureTemplate | None:
    tpl = get_template(template_id)
    if not tpl:
        return None
    name = (name or "").strip()
    if not name or default_interval_days < 1:
        return None
    clash = ProcedureTemplate.query.filter(
        db.func.lower(ProcedureTemplate.name) == name.lower(),
        ProcedureTemplate.id != template_id,
    ).first()
    if clash:
        return None
    tpl.name = name
    tpl.default_interval_days = int(default_interval_days)
    db.session.commit()
    return tpl


def delete_template(template_id: int) -> bool:
    tpl = get_template(template_id)
    if not tpl:
        return False
    db.session.delete(tpl)
    db.session.commit()
    return True


# ---------------------------------------------------------------------------
# Scheduling maths (pure, no DB)
# ---------------------------------------------------------------------------
def calculate_procedure_dates(
    start_date: date,
    intervals: Sequence[int],
) -> list[date]:
    """
    Given a start date and intervals (gap-from-previous), return each session date.
    `intervals` has length (number_of_sessions - 1).
    """
    dates = [start_date]
    running = start_date
    for gap in intervals:
        running = running + timedelta(days=int(gap))
        dates.append(running)
    return dates


# ---------------------------------------------------------------------------
# Client treatments
# ---------------------------------------------------------------------------
def get_treatments_for_client(client_id: int, user_id: int) -> list[ClientTreatment]:
    if not get_client(client_id, user_id):
        return []
    return (
        ClientTreatment.query
        .filter_by(client_id=client_id)
        .order_by(ClientTreatment.created_at.desc())
        .all()
    )


def get_treatment(treatment_id: int, user_id: int) -> ClientTreatment | None:
    return (
        db.session.query(ClientTreatment)
        .join(Client, Client.id == ClientTreatment.client_id)
        .filter(ClientTreatment.id == treatment_id, Client.user_id == user_id)
        .first()
    )


def create_treatment_with_schedule(
    client_id: int,
    user_id: int,
    name: str,
    number_of_sessions: int,
    interval_days: int,
    start_date: date,
    template_id: int | None = None,
    save_as_template: bool = False,
) -> ClientTreatment | None:
    client = get_client(client_id, user_id)
    if not client:
        return None

    name = (name or "").strip()
    if not name or number_of_sessions < 1 or interval_days < 1:
        return None

    template = get_template(template_id) if template_id else None
    if template_id and not template:
        return None

    if save_as_template and not template:
        create_template(name, interval_days)  # silently no-op on duplicate name

    treatment = ClientTreatment(
        client_id=client_id,
        template_id=template.id if template else None,
        name=name,
        default_interval_days=int(interval_days),
    )
    db.session.add(treatment)
    db.session.flush()

    intervals = [int(interval_days)] * (number_of_sessions - 1)
    dates = calculate_procedure_dates(start_date, intervals)
    gaps = [0] + intervals

    sessions = [
        Procedure(
            treatment_id=treatment.id,
            sequence_number=i + 1,
            scheduled_date=d,
            interval_days=gaps[i],
        )
        for i, d in enumerate(dates)
    ]
    db.session.add_all(sessions)
    db.session.commit()
    return treatment


def delete_treatment(treatment_id: int, user_id: int) -> bool:
    treatment = get_treatment(treatment_id, user_id)
    if not treatment:
        return False
    db.session.delete(treatment)
    db.session.commit()
    return True


def get_sessions_for_treatment(treatment_id: int, user_id: int) -> list[Procedure]:
    if not get_treatment(treatment_id, user_id):
        return []
    return (
        Procedure.query
        .filter_by(treatment_id=treatment_id)
        .order_by(Procedure.sequence_number)
        .all()
    )


# ---------------------------------------------------------------------------
# Single session (procedure) actions
# ---------------------------------------------------------------------------
def _get_session_scoped(procedure_id: int, user_id: int) -> Procedure | None:
    return (
        db.session.query(Procedure)
        .join(ClientTreatment, ClientTreatment.id == Procedure.treatment_id)
        .join(Client, Client.id == ClientTreatment.client_id)
        .filter(Procedure.id == procedure_id, Client.user_id == user_id)
        .first()
    )


def toggle_session_completed(procedure_id: int, user_id: int) -> Procedure | None:
    proc = _get_session_scoped(procedure_id, user_id)
    if not proc:
        return None
    proc.completed = not proc.completed
    db.session.commit()
    return proc


def reschedule_session(
    procedure_id: int,
    user_id: int,
    new_date: date,
    cascade_mode: str = CASCADE_NONE,
) -> Procedure | None:
    """
    Change a session's date. cascade_mode controls what happens to later
    sessions in the SAME treatment:

      CASCADE_NONE         Only this session moves. Everything else unchanged.

      CASCADE_SHIFT        Every later session moves by the same number of
                           days as this one did. Preserves any previous
                           manual adjustments to the spacing between later
                           sessions.

      CASCADE_RECALCULATE  Later sessions are rebuilt from the new date
                           using the treatment's default interval. Any
                           previous manual adjustments to later sessions
                           are OVERWRITTEN.

    Past/completed sessions and any session earlier than the moved one
    are never touched.
    """
    if cascade_mode not in VALID_CASCADE_MODES:
        return None

    proc = _get_session_scoped(procedure_id, user_id)
    if not proc:
        return None

    delta = (new_date - proc.scheduled_date).days
    proc.scheduled_date = new_date

    if cascade_mode == CASCADE_NONE or delta == 0 and cascade_mode == CASCADE_SHIFT:
        # Nothing else to do. (The "delta == 0 and SHIFT" case is a no-op too.)
        # For RECALCULATE we still run below even when delta==0 because the
        # interval itself might have been changed on earlier manual edits.
        if cascade_mode != CASCADE_RECALCULATE:
            db.session.commit()
            return proc

    later_sessions = (
        Procedure.query
        .filter(
            Procedure.treatment_id == proc.treatment_id,
            Procedure.sequence_number > proc.sequence_number,
        )
        .order_by(Procedure.sequence_number)
        .all()
    )

    if cascade_mode == CASCADE_SHIFT:
        for s in later_sessions:
            s.scheduled_date = s.scheduled_date + timedelta(days=delta)
            # interval_days between this session and the previous one is
            # unchanged (everyone moved together), so don't touch it.

    elif cascade_mode == CASCADE_RECALCULATE:
        # Rebuild from the moved session using the treatment's default interval.
        interval = proc.treatment.default_interval_days
        running = new_date
        for s in later_sessions:
            running = running + timedelta(days=interval)
            s.scheduled_date = running
            s.interval_days = interval

    db.session.commit()
    return proc
