
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import pbkdf2_sha256 as encrypt

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    firstName = db.Column(db.String(), nullable=False)
    surname = db.Column(db.String(), nullable=False)
    telephone = db.Column(db.String(), nullable=True)


class Clients(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(), nullable=False)
    surname = db.Column(db.String(), nullable=False)
    telephone = db.Column(db.String(), nullable=True)

class DB_Functions():
    def init_db(app):
        db.init_app(app)
        with app.app_context():
            db.create_all()

    @staticmethod
    def addAdminUser():
        admin = User(
            username='admin',
            password = encrypt.hash('000'),
            firstName = 'admin',
            surname = 'admin',
            telephone = '+359887990939'
        )
        db.session.add(admin)
        db.session.commit()