from datetime import date, datetime

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort

from database import DB_Functions as db
from .auth import login_required, admin_required

adminBP = Blueprint('admin', __name__, url_prefix='/admin')


# ---------------------------------------------------------------------------
# Dashboard & clients
# ---------------------------------------------------------------------------
@adminBP.route('/')
@login_required
def dashboard():
    clients = db.get_clients_for_user(session['user_id'])
    return render_template(
        'admin/dashboard.html',
        clients=clients,
        username=session.get('username'),
    )


@adminBP.route('/clients/new', methods=['GET', 'POST'])
@login_required
def new_client():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Client name is required.', 'error')
            return render_template('admin/new_client.html'), 400

        client = db.create_client(session['user_id'], name)
        if not client:
            flash('Could not create client.', 'error')
            return render_template('admin/new_client.html'), 400

        return redirect(url_for('admin.client_detail', client_id=client.id))

    return render_template('admin/new_client.html')


@adminBP.route('/clients/<int:client_id>')
@login_required
def client_detail(client_id):
    client = db.get_client(client_id, session['user_id'])
    if not client:
        abort(404)
    procedures = db.get_procedures_for_client(client_id, session['user_id'])
    return render_template(
        'admin/client_detail.html',
        client=client,
        procedures=procedures,
        today=date.today(),
    )


@adminBP.route('/clients/<int:client_id>/delete', methods=['POST'])
@login_required
def delete_client(client_id):
    if db.delete_client(client_id, session['user_id']):
        flash('Client deleted.', 'success')
    return redirect(url_for('admin.dashboard'))


# ---------------------------------------------------------------------------
# Scheduling
# ---------------------------------------------------------------------------
@adminBP.route('/clients/<int:client_id>/schedule', methods=['POST'])
@login_required
def schedule_procedures(client_id):
    client = db.get_client(client_id, session['user_id'])
    if not client:
        abort(404)

    try:
        number = int(request.form.get('number_of_procedures', 0))
        interval = int(request.form.get('interval_days', 0))
        start_raw = request.form.get('start_date', '').strip()
        start = datetime.strptime(start_raw, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        flash('Please fill in valid numbers and a valid start date.', 'error')
        return redirect(url_for('admin.client_detail', client_id=client_id))

    if number < 1 or number > 50:
        flash('Number of procedures must be between 1 and 50.', 'error')
        return redirect(url_for('admin.client_detail', client_id=client_id))
    if interval < 1 or interval > 365:
        flash('Interval must be between 1 and 365 days.', 'error')
        return redirect(url_for('admin.client_detail', client_id=client_id))

    # Fixed interval for now. The DB layer already takes a list, so switching
    # to custom per-procedure intervals later means only changing this line.
    intervals = [interval] * (number - 1)

    db.create_schedule(
        client_id=client_id,
        user_id=session['user_id'],
        start_date=start,
        intervals=intervals,
        replace_existing=True,
    )
    flash(f'Scheduled {number} procedures.', 'success')
    return redirect(url_for('admin.client_detail', client_id=client_id))


@adminBP.route('/procedures/<int:procedure_id>/toggle', methods=['POST'])
@login_required
def toggle_procedure(procedure_id):
    proc = db.toggle_procedure_completed(procedure_id, session['user_id'])
    if not proc:
        abort(404)
    return redirect(url_for('admin.client_detail', client_id=proc.client_id))


# ---------------------------------------------------------------------------
# User management (admin-only)
# ---------------------------------------------------------------------------
@adminBP.route('/users', methods=['GET'])
@admin_required
def list_users():
    users = db.list_users()
    return render_template('admin/users.html', users=users)


@adminBP.route('/users/new', methods=['POST'])
@admin_required
def create_user():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    is_admin = request.form.get('is_admin') == 'on'

    if not username or not password:
        flash('Username and password are required.', 'error')
        return redirect(url_for('admin.list_users'))
    if len(password) < 6:
        flash('Password must be at least 6 characters.', 'error')
        return redirect(url_for('admin.list_users'))

    user = db.create_user(username, password, is_admin=is_admin)
    if not user:
        flash('Username already exists.', 'error')
    else:
        flash(f"User '{username}' created.", 'success')
    return redirect(url_for('admin.list_users'))


@adminBP.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_id == session.get('user_id'):
        flash("You can't delete your own account.", 'error')
        return redirect(url_for('admin.list_users'))
    if db.delete_user(user_id):
        flash('User deleted.', 'success')
    return redirect(url_for('admin.list_users'))
