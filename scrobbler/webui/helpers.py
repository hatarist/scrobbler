import datetime

from flask import flash, request

from scrobbler import app, db, login_manager, __VERSION__
from scrobbler.webui.consts import PERIODS
from scrobbler.models import User


@app.template_filter('timesince')
def timesince(time, now=None):
    chunks = (
        (60 * 60 * 24 * 365, 'year'),
        (60 * 60 * 24 * 30, 'month'),
        (60 * 60 * 24 * 7, 'week'),
        (60 * 60 * 24, 'day'),
        (60 * 60, 'hour'),
        (60, 'minute'),
        (1, 'second')
    )

    if not now:
        now = datetime.datetime.now().replace(tzinfo=time.tzinfo)

    delta = now - (time - datetime.timedelta(0, 0, time.microsecond))
    since = delta.days * 24 * 60 * 60 + delta.seconds
    if since <= 0:
        return 'in the future'
    for i, (seconds, name) in enumerate(chunks):
        count = since // seconds
        if count != 0:
            break

    if count > 1:
        name += 's'

    return '%(number)d %(type)s ago' % {'number': count, 'type': name}


@app.context_processor
def periods():
    return {'PERIODS': PERIODS}


@app.context_processor
def project_version():
    return {'PROJECT_VERSION': __VERSION__}


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
