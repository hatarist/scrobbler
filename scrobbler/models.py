from datetime import datetime

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
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
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.now)

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
        self._webui_password = bcrypt.generate_password_hash(data).decode('utf-8')

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

    def __str__(self):
        return self.username

    def __repr__(self):
        return "<User {username}>".format(username=self.username)


class Session(db.Model):
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(32))
    created_at = db.Column(db.DateTime(timezone=True))


class BaseScrobble(object):
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
    musicbrainz = db.Column(db.String(255))

    def __str__(self):
        return "{artist} - {track}".format(artist=self.artist, track=self.track)


class Scrobble(db.Model, BaseScrobble):
    __tablename__ = 'scrobbles'

    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    source = db.Column(db.String(255))
    rating = db.Column(db.String(255))
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=True)
    album_id = db.Column(db.Integer, db.ForeignKey('albums.id'), nullable=True)

    def __repr__(self):
        return "<Scrobble #{id}: {artist} - {track}>".format(
            id=self.id,
            artist=self.artist,
            track=self.track
        )


class NowPlaying(db.Model, BaseScrobble):
    __tablename__ = 'np'

    def __repr__(self):
        return "<NP #{id}: {artist} - {track}>".format(
            id=self.id,
            artist=self.artist,
            track=self.track
        )


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    # initial_name = db.Column(db.String(255))
    bio = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    playcount = db.Column(db.Integer, default=0)
    local_playcount = db.Column(db.Integer, default=0)
    mbid = db.Column(db.String(64))
    tags = db.Column(JSONB)
    genre = db.Column(db.String(64))

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Artist #{id}: {artist}>".format(
            id=self.id,
            artist=self.name
        )


class Album(db.Model):
    __tablename__ = 'albums'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=True)
    artist = relationship("Artist")
    date = db.Column(db.Date)
    image_url = db.Column(db.String(255))
    playcount = db.Column(db.Integer, default=0)
    local_playcount = db.Column(db.Integer, default=0)
    tags = db.Column(JSONB)
    genre = db.Column(db.String(64))

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Artist #{id}: {artist}>".format(
            id=self.id,
            artist=self.name
        )


class BaseDiff(object):
    """
    This table contains the normalized results of string comparison algorightms.

    - Dn contains the normalized value for the original object names;
    - DnL contains the normalized value for the lowercased object names.

    Each Dn field (D1, D2, D3 etc.) uses different algorithms (ifast_comp, Levenshtein, etc.).
    """

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


class DiffArtists(db.Model, BaseDiff):
    __tablename__ = 'diff_artists'

    id = db.Column(db.Integer, primary_key=True)

    artist1 = db.Column(db.String(255), nullable=False)
    artist2 = db.Column(db.String(255), nullable=False)


class DiffTracks(db.Model, BaseDiff):
    __tablename__ = 'diff_tracks'

    id = db.Column(db.Integer, primary_key=True)

    artist = db.Column(db.String(255), nullable=False)
    track1 = db.Column(db.String(255), nullable=False)
    track2 = db.Column(db.String(255), nullable=False)


class BaseCorrection(object):
    id = db.Column(db.Integer, primary_key=True)
    old = db.Column(db.String(255), nullable=False)
    new = db.Column(db.String(255), nullable=False)


class ArtistCorrection(BaseCorrection, db.Model):
    __tablename__ = 'correction_artists'


class TrackCorrection(BaseCorrection, db.Model):
    __tablename__ = 'correction_tracks'

    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    artist = relationship("Artist")


class TagCorrection(BaseCorrection, db.Model):
    __tablename__ = 'correction_tags'
