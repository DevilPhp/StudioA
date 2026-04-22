from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """Staff account that can log in and manage clients."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    clients = db.relationship(
        'Client',
        backref='owner',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

    def __repr__(self):
        return f'<User {self.username}{" *admin*" if self.is_admin else ""}>'


class Client(db.Model):
    """A client receiving procedures."""
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    treatments = db.relationship(
        'ClientTreatment',
        backref='client',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='ClientTreatment.created_at.desc()',
    )

    def __repr__(self):
        return f'<Client {self.name}>'


class ProcedureTemplate(db.Model):
    """
    A reusable procedure definition (e.g. "Hands", "Face", "Bikini").
    Holds the default interval between sessions.
    Shared across all users for now.
    """
    __tablename__ = 'procedure_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    default_interval_days = db.Column(db.Integer, nullable=False, default=30)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<ProcedureTemplate {self.name} every {self.default_interval_days}d>'


class ClientTreatment(db.Model):
    """
    A named procedure attached to a client (e.g. "Hands procedure" for Jane Doe).
    Holds its own sessions. Optionally linked to a template — but we copy the
    name and interval at creation time so deleting the template won't break
    existing treatments.
    """
    __tablename__ = 'client_treatments'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', ondelete='CASCADE'),
                          nullable=False, index=True)
    template_id = db.Column(db.Integer, db.ForeignKey('procedure_templates.id', ondelete='SET NULL'),
                            nullable=True, index=True)

    name = db.Column(db.String(120), nullable=False)
    default_interval_days = db.Column(db.Integer, nullable=False, default=30)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    sessions = db.relationship(
        'Procedure',
        backref='treatment',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='Procedure.sequence_number',
    )

    # Convenience for templates to count their progress
    template = db.relationship('ProcedureTemplate', lazy='joined')

    def __repr__(self):
        return f'<ClientTreatment {self.name} client={self.client_id}>'


class Procedure(db.Model):
    """
    One session within a treatment.

    interval_days stores the gap from the PREVIOUS session in this treatment
    (0 for the first session).
    """
    __tablename__ = 'procedures'

    id = db.Column(db.Integer, primary_key=True)
    treatment_id = db.Column(db.Integer, db.ForeignKey('client_treatments.id', ondelete='CASCADE'),
                             nullable=False, index=True)
    sequence_number = db.Column(db.Integer, nullable=False)   # 1, 2, 3, ...
    scheduled_date = db.Column(db.Date, nullable=False)
    interval_days = db.Column(db.Integer, nullable=False, default=0)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Procedure #{self.sequence_number} treatment={self.treatment_id} {self.scheduled_date}>'
