#!/usr/bin/env python
from flask.ext.script import Manager

from scrobbler.wsgi import app, db


manager = Manager(app)


@manager.shell
def make_shell_context():
    from pprint import pprint

    from flask_sqlalchemy import get_debug_queries
    from sqlalchemy import func

    from scrobbler.models import Scrobble, User, Session, NowPlaying, Artist, ArtistTag

    return dict(
        app=app, db=db, pprint=pprint, gq=get_debug_queries, func=func,
        Scrobble=Scrobble, NowPlaying=NowPlaying, User=User, Session=Session, Artist=Artist,
        ArtistTag=ArtistTag,
    )


@manager.command
def initdb():
    db.create_all()


@manager.command
@manager.option('-c', '--chunks', dest='chunks', default=1, help='Split data to chunks of N')
@manager.option('-i', '--index', dest='index', default=0, help='Start a chunk from index M')
def find_similar_names(field_name, chunks, index):
    """
        Find similar names in the `scrobbles` table. Really useful to nuke the dupes.

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
def fix_length():
    from scrobbler.commands.metadata import fix_scrobble_length
    fix_scrobble_length()


if __name__ == "__main__":
    manager.run()
