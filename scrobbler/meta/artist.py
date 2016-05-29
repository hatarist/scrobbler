from sqlalchemy import func

from scrobbler import db, lastfm
from scrobbler.meta.consts import SYNC_META
from scrobbler.models import Artist, ArtistTag


def sync(name, method=SYNC_META.INSERT_OR_UPDATE):
    artist = (db.session.query(Artist)
              .filter(func.lower(Artist.name) == name.lower())
              .first())

    data = lastfm.artist(name)

    if not data:
        return False

    if artist is None and SYNC_META(method) in (SYNC_META.INSERT_ONLY, SYNC_META.INSERT_OR_UPDATE):
        artist = Artist(
            name=data['name'],
            bio=data['bio'],
            image_url=data['image'],
            playcount=data['playcount']
        )
        db.session.add(artist)
        db.session.commit()

        for tag_name, tag_weight in data['tags']:
            tag = (db.session.query(ArtistTag)
                   .filter(ArtistTag.artist_id == artist.id, ArtistTag.tag == tag_name).first())

            if tag is None:
                tag = ArtistTag(artist=artist, tag=tag_name, strength=tag_weight)

            db.session.add(tag)

        db.session.commit()

    elif artist is not None and method == SYNC_META.INSERT_OR_UPDATE:
        artist.name = data['name']
        artist.bio = data['bio']
        artist.image_url = data['image']
        artist.playcount = data['playcount']
        artist.save()

        # Rewrite all tags
        db.session.query(ArtistTag).filter(ArtistTag.artist_id == artist.id).delete()

        for tag_name, tag_weight in data['tags']:
            tag = (db.session.query(ArtistTag)
                   .filter(ArtistTag.artist_id == artist.id, ArtistTag.tag == tag_name).first())

            if tag is None:
                tag = ArtistTag(artist=artist, tag=tag_name, strength=tag_weight)

            db.session.add(tag)

        db.session.commit()

    return data
