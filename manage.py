from flask.ext.script import Manager, Shell

from scrobbler.wsgi import app, db


manager = Manager(app)


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

manager.add_command('shell', Shell(make_context=make_shell_context))


if __name__ == "__main__":
    manager.run()
