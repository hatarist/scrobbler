import datetime
import hashlib

from collections import defaultdict

from scrobbler.api.consts import AUTH_KEY_MAPPING, SCROBBLE_KEY_MAPPING


def md5(data):
    return hashlib.md5(data.encode('utf-8')).hexdigest()


def api_response(*lines):
    return '\n'.join(lines + ('',))


def authenticate(user, timestamp, auth):
    """
    Returns a tuple of (User, Token.id).
    """
    if user is None:
        return (None, None)

    if auth == md5(user.api_password + timestamp):
        return (user, None)
    else:
        for token in user.tokens:
            if auth == md5(token.key + timestamp):
                return (user, token.id)

    return (None, None)


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

        if k_readable_name == 'timestamp':
            value = datetime.datetime.fromtimestamp(int(value))
        elif k_readable_name == 'length':
            value = datetime.timedelta(seconds=int(value))

        scrobbles[k_index][k_readable_name] = value

    # Convert dict to list & sort by timestamps
    scrobbles = sorted(scrobbles.values(), key=lambda d: d.get('i', 0))

    return (session_id, scrobbles)
