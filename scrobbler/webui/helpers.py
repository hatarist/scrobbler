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


@app.template_filter('bignum')
def bignum(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '%.2f%s' % (num, ['', 'K', 'M'][magnitude]) if magnitude > 0 else num


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
