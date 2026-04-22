from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from database import DB_Functions as db

authBP = Blueprint('auth', __name__)


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------
def login_required(view):
    """Redirect unauthenticated users to the login page."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('auth.login'))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    """Only admin users may access the wrapped view."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('auth.login'))
        if not session.get('is_admin'):
            flash('Admin access required.', 'error')
            return redirect(url_for('admin.dashboard'))
        return view(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@authBP.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = db.verify_user(username, password)
        if user:
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            return redirect(url_for('admin.dashboard'))

        flash('Invalid username or password', 'error')
        return render_template('admin/login.html'), 401

    if session.get('user_id'):
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/login.html')


@authBP.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
