import datetime

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.types import TypeDecorator, Integer

from scrobbler import db


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
    username = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(32))
    settings = db.Column(db.String(255))

    sessions = db.relationship('Session', backref='user')


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

    @hybrid_property
    def title(self):
        return self.artist + " - " + self.track

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
