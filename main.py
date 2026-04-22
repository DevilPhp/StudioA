import sys
import os

# import eventlet
# eventlet.monkey_patch()

from dotenv import load_dotenv
load_dotenv()

from urllib.parse import quote_plus

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Blueprint
from flask_socketio import SocketIO, emit
from database import DB_Functions as db
from routes import blueprints
# from utils.bg_dates import register as register_bg_dates
from datetime import datetime


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------
def _require_env(name: str) -> str:
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
    return f"postgresql://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{name}"


def _resolve_secret_key() -> str:
    """
    Return the Flask secret key from the environment.

    If FLASK_SECRET_KEY isn't set we only fall back to a random key when
    running the dev server directly (python main.py) — which means a single
    process. Under gunicorn (or any multi-worker setup) every worker would
    otherwise generate a DIFFERENT random key, causing session cookies
    signed by worker A to be rejected by worker B and logging the user out
    on every request that happens to land on a different worker.
    """
    key = os.environ.get('FLASK_SECRET_KEY')
    if key:
        return key

    # Detect whether we're running under a WSGI server (gunicorn, uwsgi, ...).
    # If we are, there's almost certainly > 1 worker and no stable key == bugs.
    under_wsgi = 'gunicorn' in sys.argv[0] or 'uwsgi' in sys.argv[0] \
                 or os.environ.get('SERVER_SOFTWARE', '').startswith(('gunicorn', 'uwsgi'))

    if under_wsgi:
        raise RuntimeError(
            "FLASK_SECRET_KEY is not set. Running under a WSGI server without "
            "a stable secret causes session cookies to be invalidated across "
            "worker processes, logging users out on every request.\n\n"
            "Fix: set FLASK_SECRET_KEY in your .env file. Generate one with:\n"
            "    python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    # Single-process dev fallback only
    print(
        "⚠ FLASK_SECRET_KEY not set — using a random key for this dev session. "
        "Sessions will not survive an app restart.",
        file=sys.stderr,
    )
    return os.urandom(24).hex()


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__, static_folder='static')
socketio = SocketIO(app, cors_allowed_origins="*")

app.secret_key = _resolve_secret_key()

app.config['SQLALCHEMY_DATABASE_URI'] = _build_database_uri()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 30,
    "pool_recycle": 1800,
}

# Bind SQLAlchemy, create tables, register CLI commands (seed-admin, etc.)
db.init_db(app)
# register_bg_dates(app)

for blueprint in blueprints:
    app.register_blueprint(blueprint)


@app.route('/')
def index():
    return redirect(url_for('home.homeBG'))


if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=8001)