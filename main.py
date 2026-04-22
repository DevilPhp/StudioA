import sys
import os

# import eventlet
# eventlet.monkey_patch()

# Load environment variables from .env BEFORE anything reads os.environ.
# In production (gunicorn on the server), real env vars take precedence;
# python-dotenv only fills in what isn't already set.
from dotenv import load_dotenv
# load_dotenv()

from urllib.parse import quote_plus

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Blueprint
from flask_socketio import SocketIO, emit
from database import DB_Functions as db
from routes import blueprints
from datetime import datetime


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------
def _require_env(name: str) -> str:
    """Fail fast on startup if a required env var is missing."""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Check your .env file (copy .env.example if you haven't yet)."
        )
    return value


def _build_database_uri() -> str:
    user = _require_env('DB_USER')
    password = _require_env('DB_PASSWORD')
    host = os.environ.get('DB_HOST', 'localhost')
    port = os.environ.get('DB_PORT', '5432')
    name = _require_env('DB_NAME')
    # quote_plus handles special chars in the password safely (e.g. @ : / #)
    return f"postgresql://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{name}"


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__, static_folder='static')
socketio = SocketIO(app, cors_allowed_origins="*")

# Prefer a stable secret from env so sessions survive restarts.
# Fall back to a random one only if FLASK_SECRET_KEY isn't set.
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or os.urandom(24)

# app.config['SQLALCHEMY_DATABASE_URI'] = _build_database_uri()
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
#     "pool_size": 10,
#     "max_overflow": 20,
#     "pool_timeout": 30,
#     "pool_recycle": 1800,
# }

# Bind SQLAlchemy, create tables, register CLI commands (seed-admin, etc.)
# db.init_db(app)

for blueprint in blueprints:
    app.register_blueprint(blueprint)


@app.route('/')
def index():
    return redirect(url_for('home.homeBG'))

# The /login route is provided by routes/auth.py (authBP)


if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=8001)