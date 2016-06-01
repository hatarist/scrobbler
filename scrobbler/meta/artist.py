from scrobbler import db, lastfm
from scrobbler.meta.consts import SYNC_META
from scrobbler.models import Artist


def sync(name, method=SYNC_META.INSERT_OR_UPDATE):
    artist = (db.session.query(Artist)
              .filter(Artist.name == name)
              .first())

    data = lastfm.artist(name)

    if not data:
        return False

    if artist is None and SYNC_META(method) in (SYNC_META.INSERT_ONLY, SYNC_META.INSERT_OR_UPDATE):
        artist = Artist(
            name=data['name'],
            bio=data['bio'],
            image_url=data['image'],
            playcount=data['playcount'],
            tags=data['tags'],
        )
        db.session.add(artist)
    elif artist is not None and method == SYNC_META.INSERT_OR_UPDATE:
        artist.name = data['name']
        artist.bio = data['bio']
        artist.image_url = data['image']
        artist.playcount = data['playcount']
        artist.tags = data['tags']
        artist.save()

    db.session.commit()

    return data
