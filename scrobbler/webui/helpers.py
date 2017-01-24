import datetime
from functools import wraps

from flask import flash, request
from flask_login import current_user

from scrobbler import app, db, login_manager, __VERSION__
from scrobbler.webui.consts import PERIODS
from scrobbler.models import User


def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if app.login_manager._login_disabled:
            return func(*args, **kwargs)
        elif not current_user.is_authenticated or not current_user.is_admin:
            return app.login_manager.unauthorized()
        return func(*args, **kwargs)
    return decorated_view


@app.context_processor
def periods():
    return {'PERIODS': PERIODS}


@app.context_processor
def project_version():
    return {'PROJECT_VERSION': __VERSION__}


@app.context_processor
def signup_enabled():
    return {'SIGNUP_ENABLED': app.config['SIGNUP_ENABLED']}


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


def show_form_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"<b>{}</b>: {}".format(getattr(form, field).label.text, error), 'error')


def get_argument(arg_name, arg_type=None, default=0):
    arg_type = arg_type or int

    try:
        return arg_type(request.args.get(arg_name))
    except (TypeError, ValueError):
        return default


def range_to_datetime(s_from, s_to):
    try:
        dt_from = datetime.datetime.strptime(s_from, '%Y-%m-%d')
    except ValueError:
        dt_from = datetime.datetime.strptime(s_from, '%Y-%m-%d %H:%M:%S')

    try:
        dt_to = datetime.datetime.strptime(s_to, '%Y-%m-%d')
        dt_to = dt_to + datetime.timedelta(days=1) - datetime.timedelta(microseconds=1)
    except ValueError:
        dt_to = datetime.datetime.strptime(s_to, '%Y-%m-%d %H:%M:%S')

    return (dt_from, dt_to)
