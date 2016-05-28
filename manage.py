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
def find_similar_names(field_name):
    """
        Find similar names in the `scrobbles` table. Really useful to nuke the dupes.

        Usage:
        ./manage.py find_similar_names D1
        ./manage.py find_similar_names D1L

        For further info about D-fields, see `DiffArtists` and `find_similar_artists()`.
    """
    from scrobbler.commands.metadata import find_similar_artists
    find_similar_artists(field_name)


if __name__ == "__main__":
    manager.run()
