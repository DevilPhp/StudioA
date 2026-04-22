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
    treatments = db.get_treatments_for_client(client_id, session['user_id'])
    return render_template(
        'admin/client_detail.html',
        client=client,
        treatments=treatments,
        today=date.today(),
    )


@adminBP.route('/clients/<int:client_id>/delete', methods=['POST'])
@login_required
def delete_client(client_id):
    if db.delete_client(client_id, session['user_id']):
        flash('Client deleted.', 'success')
    return redirect(url_for('admin.dashboard'))


# ---------------------------------------------------------------------------
# Treatments
# ---------------------------------------------------------------------------
@adminBP.route('/clients/<int:client_id>/treatments/new', methods=['GET', 'POST'])
@login_required
def new_treatment(client_id):
    client = db.get_client(client_id, session['user_id'])
    if not client:
        abort(404)

    templates = db.list_templates()

    if request.method == 'POST':
        template_id_raw = request.form.get('template_id', '').strip()
        freeform_name = request.form.get('freeform_name', '').strip()
        interval_raw = request.form.get('interval_days', '').strip()
        sessions_raw = request.form.get('number_of_sessions', '').strip()
        start_raw = request.form.get('start_date', '').strip()
        save_as_template = request.form.get('save_as_template') == 'on'

        template_id = None
        name: str
        interval_days: int

        try:
            number_of_sessions = int(sessions_raw)
            start_date = datetime.strptime(start_raw, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            flash('Please fill in a valid number of sessions and start date.', 'error')
            return render_template('admin/new_treatment.html',
                                   client=client, templates=templates,
                                   today=date.today()), 400

        if template_id_raw:
            try:
                template_id = int(template_id_raw)
            except ValueError:
                flash('Invalid template selection.', 'error')
                return render_template('admin/new_treatment.html',
                                       client=client, templates=templates,
                                       today=date.today()), 400
            template = db.get_template(template_id)
            if not template:
                flash('Selected template not found.', 'error')
                return render_template('admin/new_treatment.html',
                                       client=client, templates=templates,
                                       today=date.today()), 400
            name = template.name
            try:
                interval_days = int(interval_raw) if interval_raw else template.default_interval_days
            except ValueError:
                interval_days = template.default_interval_days
            save_as_template = False
        else:
            if not freeform_name:
                flash('Give the treatment a name or pick a template.', 'error')
                return render_template('admin/new_treatment.html',
                                       client=client, templates=templates,
                                       today=date.today()), 400
            try:
                interval_days = int(interval_raw)
            except (ValueError, TypeError):
                flash('Interval must be a number.', 'error')
                return render_template('admin/new_treatment.html',
                                       client=client, templates=templates,
                                       today=date.today()), 400
            name = freeform_name

        if number_of_sessions < 1 or number_of_sessions > 50:
            flash('Number of sessions must be between 1 and 50.', 'error')
            return render_template('admin/new_treatment.html',
                                   client=client, templates=templates,
                                   today=date.today()), 400
        if interval_days < 1 or interval_days > 365:
            flash('Interval must be between 1 and 365 days.', 'error')
            return render_template('admin/new_treatment.html',
                                   client=client, templates=templates,
                                   today=date.today()), 400

        treatment = db.create_treatment_with_schedule(
            client_id=client_id,
            user_id=session['user_id'],
            name=name,
            number_of_sessions=number_of_sessions,
            interval_days=interval_days,
            start_date=start_date,
            template_id=template_id,
            save_as_template=save_as_template,
        )
        if not treatment:
            flash('Could not create treatment.', 'error')
            return render_template('admin/new_treatment.html',
                                   client=client, templates=templates,
                                   today=date.today()), 400

        if save_as_template and not template_id:
            flash(f'Treatment created. Template "{name}" saved for future use.', 'success')
        else:
            flash(f'Treatment "{name}" created with {number_of_sessions} sessions.', 'success')
        return redirect(url_for('admin.treatment_detail', treatment_id=treatment.id))

    return render_template(
        'admin/new_treatment.html',
        client=client,
        templates=templates,
        today=date.today(),
    )


@adminBP.route('/treatments/<int:treatment_id>')
@login_required
def treatment_detail(treatment_id):
    treatment = db.get_treatment(treatment_id, session['user_id'])
    if not treatment:
        abort(404)
    sessions = db.get_sessions_for_treatment(treatment_id, session['user_id'])
    return render_template(
        'admin/treatment_detail.html',
        treatment=treatment,
        sessions=sessions,
        today=date.today(),
    )


@adminBP.route('/treatments/<int:treatment_id>/delete', methods=['POST'])
@login_required
def delete_treatment(treatment_id):
    treatment = db.get_treatment(treatment_id, session['user_id'])
    if not treatment:
        abort(404)
    client_id = treatment.client_id
    db.delete_treatment(treatment_id, session['user_id'])
    flash('Treatment deleted.', 'success')
    return redirect(url_for('admin.client_detail', client_id=client_id))


# ---------------------------------------------------------------------------
# Individual sessions
# ---------------------------------------------------------------------------
@adminBP.route('/procedures/<int:procedure_id>/toggle', methods=['POST'])
@login_required
def toggle_procedure(procedure_id):
    proc = db.toggle_session_completed(procedure_id, session['user_id'])
    if not proc:
        abort(404)
    return redirect(url_for('admin.treatment_detail', treatment_id=proc.treatment_id))


@adminBP.route('/procedures/<int:procedure_id>/reschedule', methods=['POST'])
@login_required
def reschedule_procedure(procedure_id):
    date_raw = request.form.get('new_date', '').strip()
    cascade_mode = request.form.get('cascade_mode', db.CASCADE_NONE)

    if cascade_mode not in db.VALID_CASCADE_MODES:
        flash('Invalid cascade option.', 'error')
        cascade_mode = db.CASCADE_NONE

    try:
        new_date = datetime.strptime(date_raw, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        flash('Invalid date.', 'error')
        proc = db._get_session_scoped(procedure_id, session['user_id'])
        if proc:
            return redirect(url_for('admin.treatment_detail', treatment_id=proc.treatment_id))
        abort(404)

    proc = db.reschedule_session(
        procedure_id=procedure_id,
        user_id=session['user_id'],
        new_date=new_date,
        cascade_mode=cascade_mode,
    )
    if not proc:
        abort(404)

    messages = {
        db.CASCADE_NONE: 'Session rescheduled. Other sessions unchanged.',
        db.CASCADE_SHIFT: 'Session rescheduled. Upcoming sessions shifted by the same amount.',
        db.CASCADE_RECALCULATE: 'Session rescheduled. Upcoming sessions recalculated from the new date.',
    }
    flash(messages[cascade_mode], 'success')
    return redirect(url_for('admin.treatment_detail', treatment_id=proc.treatment_id))


# ---------------------------------------------------------------------------
# Procedure templates
# ---------------------------------------------------------------------------
@adminBP.route('/templates')
@login_required
def list_templates():
    templates = db.list_templates()
    return render_template('admin/templates.html', templates=templates)


@adminBP.route('/templates/new', methods=['POST'])
@login_required
def create_template():
    name = request.form.get('name', '').strip()
    try:
        interval = int(request.form.get('default_interval_days', 0))
    except ValueError:
        interval = 0

    if not name:
        flash('Template name is required.', 'error')
    elif interval < 1 or interval > 365:
        flash('Default interval must be between 1 and 365 days.', 'error')
    else:
        tpl = db.create_template(name, interval)
        if tpl:
            flash(f'Template "{name}" created.', 'success')
        else:
            flash('A template with that name already exists.', 'error')
    return redirect(url_for('admin.list_templates'))


@adminBP.route('/templates/<int:template_id>/update', methods=['POST'])
@login_required
def update_template(template_id):
    name = request.form.get('name', '').strip()
    try:
        interval = int(request.form.get('default_interval_days', 0))
    except ValueError:
        interval = 0

    if not name or interval < 1 or interval > 365:
        flash('Please provide a valid name and interval.', 'error')
    else:
        tpl = db.update_template(template_id, name, interval)
        if tpl:
            flash('Template updated.', 'success')
        else:
            flash('Could not update template (name may be taken).', 'error')
    return redirect(url_for('admin.list_templates'))


@adminBP.route('/templates/<int:template_id>/delete', methods=['POST'])
@login_required
def delete_template(template_id):
    if db.delete_template(template_id):
        flash('Template deleted. Existing treatments using it keep their data.', 'success')
    return redirect(url_for('admin.list_templates'))


# ---------------------------------------------------------------------------
# User management (admin-only) — unchanged
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
