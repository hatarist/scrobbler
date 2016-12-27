#!/usr/bin/env python
from flask_script import Manager

from scrobbler.wsgi import app, db


manager = Manager(app)


@manager.shell
def make_shell_context():
    from pprint import pprint

    from flask_sqlalchemy import get_debug_queries
    from sqlalchemy import desc, func

    from scrobbler.models import Artist, NowPlaying, Scrobble, Session, User

    return dict(
        app=app, db=db, pprint=pprint, gq=get_debug_queries, func=func, desc=desc,
        Scrobble=Scrobble, NowPlaying=NowPlaying, User=User, Session=Session, Artist=Artist
    )


@manager.command
def initdb():
    db.create_all()


@manager.command
@manager.option('-c', '--chunks', dest='chunks', default=1, help='Split data to chunks of N')
@manager.option('-i', '--index', dest='index', default=0, help='Start a chunk from index M')
def find_similar_artists(field_name, chunks, index):
    """
        Find similar artist names in the `scrobbles` table. Really useful to nuke the dupes.

        Usage:
        ./manage.py find_similar_names D1
        ./manage.py find_similar_names D1L

        You can also split it into chunks and run multiple processes for the faster processing:

        ./manage.py find_similar D2 -c 4 -i 0  # runs the D2 algorithm over [0::4]
        ./manage.py find_similar D2 -c 4 -i 1  # runs the D2 algorithm over [1::4]
        ./manage.py find_similar D2 -c 4 -i 2  # runs the D2 algorithm over [2::4]
        ./manage.py find_similar D2 -c 4 -i 3  # runs the D2 algorithm over [3::4]

        For further info about D-fields, see `DiffArtists` and `find_similar_artists()`.
    """
    from scrobbler.commands.metadata import find_similar_artists
    find_similar_artists(field_name, int(chunks), int(index))


@manager.command
@manager.option('-a', '--artists-count', dest='count', default=50, help='Fix data for top N artists')
@manager.option('-c', '--chunks', dest='chunks', default=1, help='Split data to chunks of N')
@manager.option('-i', '--index', dest='index', default=0, help='Start a chunk from index M')
def find_similar_tracks(field_name, count, chunks, index):
    """
        Find similar track names in the `scrobbles` table. Really useful to nuke the dupes.
    """
    from scrobbler.commands.metadata import find_similar_tracks
    find_similar_tracks(field_name, int(count), int(chunks), int(index))


@manager.command
@manager.option('-l', '--limit', dest='limit', default=0, help='How many artists to download')
def download_artist_metadata(limit):
    """
        Download artists' metadata from the Last.FM.
    """
    from scrobbler.commands.metadata import download_artist_metadata
    download_artist_metadata(limit)


@manager.command
def fix_length():
    from scrobbler.commands.metadata import fix_scrobble_length
    fix_scrobble_length()


@manager.command
def find_sequences():
    from scrobbler.commands.metadata import find_sequences
    find_sequences()


if __name__ == "__main__":
    manager.run()
