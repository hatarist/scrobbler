import datetime

from sqlalchemy.types import TypeDecorator, Integer
from sqlalchemy.ext.hybrid import hybrid_property

from scrobbler import bcrypt, db
from scrobbler.api.helpers import md5


class IntegerDateTime(TypeDecorator):
    """ A type that decorates DateTime, converts to unix time on
    the way in and to datetime.datetime objects on the way out. """

    impl = Integer  # In schema, you want these datetimes to be stored as integers.

    def process_bind_param(self, value, _):
        """ Assumes a datetime.datetime """
        if value is None:
            return None
        elif isinstance(value, int):
            return value
        elif isinstance(value, datetime.datetime):
            return int(value.strftime('%s'))

        raise ValueError("Can operate only on integer/datetime values. "
                         "Offending value type: {0}".format(type(value).__name__))

    def process_result_value(self, value, _):
        if value is not None:  # support nullability
            return datetime.datetime.fromtimestamp(float(value))


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True)
    email = db.Column(db.String(255), unique=True)
    _api_password = db.Column('api_password', db.String(32))
    _webui_password = db.Column('webui_password', db.String(128))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(IntegerDateTime, nullable=False, default=datetime.datetime.now)
    settings = db.Column(db.String(255))

    sessions = db.relationship('Session', backref='user')

    @hybrid_property
    def api_password(self):
        return self._api_password

    @api_password.setter
    def _set_api_password(self, data):
        self._api_password = md5(data)

    @hybrid_property
    def webui_password(self):
        return self._webui_password

    @webui_password.setter
    def _set_webui_password(self, data):
        self._webui_password = bcrypt.generate_password_hash(data)

    def validate_password(self, data):
        return self.api_password == md5(data)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return "{}".format(self.id)


class Session(db.Model):
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(32))
    session_time = db.Column(IntegerDateTime)


class BaseScrobble():
    time = db.Column(IntegerDateTime, nullable=False)

    # Track metadata
    artist = db.Column(db.String(255), nullable=False)
    track = db.Column(db.String(255), nullable=False)
    album = db.Column(db.String(255))
    tracknumber = db.Column(db.String(255))
    length = db.Column(db.Integer, nullable=False)

    # Optional information
    musicbrainz = db.Column(db.String(255))

    def __init__(self, **kwargs):
        self.time = kwargs.pop('timestamp', kwargs.pop('time', None))
        super(BaseScrobble, self).__init__(**kwargs)


class Scrobble(BaseScrobble, db.Model):
    __tablename__ = 'scrobbles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Optional information
    source = db.Column(db.String(255))
    rating = db.Column(db.String(255))


class NowPlaying(BaseScrobble, db.Model):
    __tablename__ = 'np'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    playcount = db.Column(db.Integer, default=0)


class ArtistTag(db.Model):
    __tablename__ = 'artist_tags'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    tag = db.Column(db.String(255))
    strength = db.Column(db.Integer)
