import datetime
import hashlib

from collections import defaultdict

from scrobbler import app, db
from scrobbler.constants import AUTH_KEY_MAPPING, SCROBBLE_KEY_MAPPING, PERIODS
from scrobbler.models import User


def md5(data):
    return hashlib.md5(data.encode('utf-8')).hexdigest()


def api_response(*lines):
    return '\n'.join(lines + ('',))


def authenticate(username, timestamp, auth):
    user = db.session.query(User).filter(User.username == username).first()
    if user is None or auth != md5(user.password + timestamp):
        return False

    return user


def parse_auth_request(args):
    data = {AUTH_KEY_MAPPING[k]: v for k, v in args.items() if k in AUTH_KEY_MAPPING}

    if not {'auth', 'timestamp', 'username'}.issubset(data):
        return False

    return data


def parse_np_request(args):
    data = {SCROBBLE_KEY_MAPPING[k]: v for k, v in args.items() if k in SCROBBLE_KEY_MAPPING}

    if not {'session_id', 'artist', 'track'}.issubset(data):
        return False

    return data


def parse_scrobble_request(args):
    args = args.copy()
    if 's' not in args:
        return (False, [])

    session_id = args.pop('s')

    scrobbles = defaultdict(lambda: defaultdict(str))

    for key, value in args.items():
        k_name = key[:1]
        k_index = int(key[1:].strip('[]') or 0)

        k_readable_name = SCROBBLE_KEY_MAPPING[k_name]

        if k_index not in scrobbles:
            scrobbles[k_index] = {}

        if k_readable_name in ('timestamp', 'length'):
            value = int(value)

        scrobbles[k_index][k_readable_name] = value

    # Convert dict to list & sort by timestamps
    scrobbles = sorted(scrobbles.values(), key=lambda d: d.get('i', 0))

    return (session_id, scrobbles)


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
