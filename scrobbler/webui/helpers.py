import datetime

from flask import flash

from scrobbler import app, db, login_manager
from scrobbler.webui.consts import PERIODS
from scrobbler.models import User


@app.template_filter('timesince')
def timesince(d, now=None):
    chunks = (
        (60 * 60 * 24 * 365, 'year'),
        (60 * 60 * 24 * 30, 'month'),
        (60 * 60 * 24 * 7, 'week'),
        (60 * 60 * 24, 'day'),
        (60 * 60, 'hour'),
        (60, 'minute'),
        (1, 'second')
    )

    if not isinstance(d, datetime.datetime):
        d = datetime.datetime.fromtimestamp(d)
    if now and not isinstance(now, datetime.datetime):
        now = datetime.datetime.fromtimestamp(now)

    if not now:
        now = datetime.datetime.now()

    delta = now - (d - datetime.timedelta(0, 0, d.microsecond))
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


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


def show_form_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"<b>{}</b>: {}".format(getattr(form, field).label.text, error), 'error')
