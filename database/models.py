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

    procedures = db.relationship(
        'Procedure',
        backref='client',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='Procedure.sequence_number',
    )

    def __repr__(self):
        return f'<Client {self.name}>'


class Procedure(db.Model):
    """
    One laser procedure belonging to a client.

    interval_days stores the gap from the PREVIOUS procedure (0 for the first).
    This lets us support fixed intervals today and custom per-procedure intervals
    later without any schema change.
    """
    __tablename__ = 'procedures'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', ondelete='CASCADE'),
                          nullable=False, index=True)
    sequence_number = db.Column(db.Integer, nullable=False)   # 1, 2, 3, ...
    scheduled_date = db.Column(db.Date, nullable=False)
    interval_days = db.Column(db.Integer, nullable=False, default=0)   # gap from previous
    completed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Procedure #{self.sequence_number} client={self.client_id} {self.scheduled_date}>'
