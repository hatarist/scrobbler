import datetime

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.types import TypeDecorator, Integer
from sqlalchemy.orm import relationship

from scrobbler import bcrypt, db
from scrobbler.api.helpers import md5


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True)
    email = db.Column(db.String(255), unique=True)
    _api_password = db.Column('api_password', db.String(32))
    _webui_password = db.Column('webui_password', db.String(128))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow)
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

    def validate_api_password(self, data):
        return self.api_password == md5(data)

    def validate_webui_password(self, data):
        try:
            return bcrypt.check_password_hash(self.webui_password, data)
        except ValueError:
            return False

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
    created_at = db.Column(db.DateTime(timezone=True))


class BaseScrobble():
    id = db.Column(db.Integer, primary_key=True)

    @declared_attr
    def user_id(cls):
        return db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    played_at = db.Column(db.DateTime(timezone=True), nullable=False)

    # Track metadata
    artist = db.Column(db.String(255), nullable=False)
    track = db.Column(db.String(255), nullable=False)
    album = db.Column(db.String(255))
    tracknumber = db.Column(db.String(255))
    length = db.Column(db.Integer, nullable=False)

    # Optional information
    musicbrainz = db.Column(db.String(255))


class Scrobble(db.Model, BaseScrobble):
    __tablename__ = 'scrobbles'

    source = db.Column(db.String(255))
    rating = db.Column(db.String(255))


class NowPlaying(db.Model, BaseScrobble):
    __tablename__ = 'np'


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    playcount = db.Column(db.Integer, default=0)

    tags = relationship("ArtistTag", back_populates="artist")

    def __str__(self):
        return self.name


class ArtistTag(db.Model):
    __tablename__ = 'artist_tags'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    artist = relationship("Artist", back_populates="tags")
    tag = db.Column(db.String(255))
    strength = db.Column(db.Integer)

    def __str__(self):
        return self.tag


class DiffArtists(db.Model):
    """
    This table contains the normalized results of string comparison algorightms.

    - Dn contains the normalized value for the original artist names;
    - DnL contains the normalized value for the lowercased artist names.

    Each Dn field (D1, D2, D3 etc.) uses different algorithms (ifast_comp, Levenshtein, etc.).
    """
    __tablename__ = 'diff_artists'

    id = db.Column(db.Integer, primary_key=True)

    artist1 = db.Column(db.String(255), nullable=False)
    artist2 = db.Column(db.String(255), nullable=False)

    ignore = db.Column(db.Boolean, default=False, nullable=False)

    # distance.ifast_comp()
    D1 = db.Column(db.Float)
    D1L = db.Column(db.Float)

    # distance.levenshtein()
    D2 = db.Column(db.Float)
    D2L = db.Column(db.Float)

    # distance.sorensen()
    D3 = db.Column(db.Float)
    D3L = db.Column(db.Float)

    # distance.jaccard()
    D4 = db.Column(db.Float)
    D4L = db.Column(db.Float)

    # distance.hamming()
    D5 = db.Column(db.Float)
    D5L = db.Column(db.Float)
