import datetime

from flask import render_template
from flask.ext.login import current_user, login_required
from sqlalchemy import func

from scrobbler import app, db
from scrobbler.models import NowPlaying, Scrobble
from scrobbler.webui.helpers import get_argument
from scrobbler.webui.views import blueprint


@blueprint.route("/latest/")
@login_required
def last_scrobbles():
    count = get_argument('count', default=app.config['RESULTS_COUNT'])

    scrobbles = (db.session
                 .query(Scrobble.id, Scrobble.artist, Scrobble.track, Scrobble.time)
                 .filter(Scrobble.user_id == current_user.id)
                 .order_by(Scrobble.time.desc())
                 .limit(count)
                 .all()
                 )

    nowplaying = (db.session
                  .query(NowPlaying.id, NowPlaying.artist, NowPlaying.track, NowPlaying.time)
                  .filter(NowPlaying.user_id == current_user.id)
                  .first()
                  )

    return render_template('latest.html', scrobbles=scrobbles, nowplaying=nowplaying)


@blueprint.route("/unique/yearly/")
@login_required
def unique_yearly():
    stats = {}

    year_from = 2006
    year_to = 2016

    """
    for year in range(year_from, year_to + 1):
        for month in range(1, 13):
            time_from = datetime.datetime(year, month, 1)
            time_to = time_from + datetime.timedelta(days=calendar.monthrange(year, month)[1])
            ...
            stats[str(year) + '-' + str(month)] = (unique_artists, unique_tracks)
    """

    for year in range(year_from, year_to + 1):
        time_from = datetime.datetime(year, 1, 1)
        time_to = datetime.datetime(year, 12, 31, 23, 59, 59, 999999)
        scrobbles = (db.session
                     .query(Scrobble)
                     .filter(Scrobble.user_id == current_user.id)
                     .filter(Scrobble.time >= time_from, Scrobble.time <= time_to)
                     .count()
                     )
        unique_artists = (db.session
                          .query(Scrobble.artist)
                          .filter(Scrobble.user_id == current_user.id)
                          .filter(Scrobble.time >= time_from, Scrobble.time <= time_to)
                          .group_by(func.lower(Scrobble.artist))
                          .count()
                          )
        unique_tracks = (db.session
                         .query(Scrobble.artist, Scrobble.track)
                         .filter(Scrobble.user_id == current_user.id)
                         .filter(Scrobble.time >= time_from, Scrobble.time <= time_to)
                         .group_by(func.lower(Scrobble.artist), func.lower(Scrobble.track))
                         .count()
                         )

        stats[year] = (scrobbles, unique_artists, unique_tracks)

    stats = stats.items()

    return render_template(
        'unique_yearly.html',
        stats=stats
    )


@blueprint.route("/milestones/")
@login_required
def milestones():
    step = get_argument('step', default=10000)

    max_id = db.session.query(func.max(Scrobble.id).label('max_id')).first().max_id
    m_list = range(step, max_id, step)
    scrobbles = (db.session
                 .query(Scrobble)
                 .filter(Scrobble.user_id == current_user.id)
                 .filter(Scrobble.id.in_(m_list))
                 .order_by(Scrobble.id.desc())
                 )

    return render_template(
        'milestones.html',
        scrobbles=scrobbles
    )
