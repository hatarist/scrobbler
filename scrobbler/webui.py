"""Provides a web-interface."""

import datetime

from flask import Blueprint, render_template, request
from sqlalchemy import func

from scrobbler import db
from scrobbler.models import Scrobble

blueprint = Blueprint('webui', __name__)


@blueprint.route("/")
def index():
    return render_template('index.html')


@blueprint.route("/latest/")
def last_scrobbles():
    scrobbles = (db.session
                 .query(Scrobble.id, Scrobble.time, Scrobble.artist, Scrobble.track)
                 .order_by(Scrobble.time.desc())
                 .limit(20)
                 .all()
                 )
    return render_template('latest.html', scrobbles=scrobbles)


@blueprint.route("/top/artists/")
def top_artists():
    count = func.count(Scrobble.artist).label('plays')
    time_from = datetime.datetime.now() - datetime.timedelta(days=7)
    chart = (db.session
             .query(Scrobble.artist, count)
             .group_by(func.lower(Scrobble.artist))
             .filter(Scrobble.time >= time_from)
             .order_by(count.desc())
             .limit(20)
             .all()
             )
    return render_template('top_artists.html', chart=enumerate(chart, start=1))


@blueprint.route("/top/tracks/")
def top_tracks():
    plays = func.count(Scrobble.artist).label('plays')
    chart = (db.session
             .query(Scrobble.artist, Scrobble.track, plays)
             .group_by(func.lower(Scrobble.artist), func.lower(Scrobble.track))
             .order_by(plays.desc())
             .limit(20)
             .all()
             )
    return render_template('top_tracks.html', chart=chart)


@blueprint.route("/top/tracks/yearly/")
def top_tracks_yearly():
    plays = func.count(Scrobble.artist).label('plays')
    charts = {}

    year_from = 2006
    year_to = 2016
    stat_count = 1000
    show_count = 100

    for year in range(year_from, year_to + 1):
        time_from = datetime.datetime(year, 1, 1)
        time_to = datetime.datetime(year, 12, 31, 23, 59, 59, 999999)
        charts[year] = (db.session
                        .query(Scrobble.artist, Scrobble.track, plays, Scrobble.title)
                        .filter(Scrobble.time >= time_from, Scrobble.time <= time_to)
                        .group_by(func.lower(Scrobble.artist), func.lower(Scrobble.track))
                        .order_by(plays.desc())
                        .limit(stat_count)
                        .all()
                        )

    charts = charts.items()

    return render_template(
        'top_tracks_yearly.html',
        charts=charts,
        show_count=show_count
    )


@blueprint.route("/top/artists/yearly/")
def top_artists_yearly():
    plays = func.count(Scrobble.artist).label('plays')
    charts = {}

    year_from = 2006
    year_to = 2016
    stat_count = 1000
    show_count = 100

    for year in range(year_from, year_to + 1):
        time_from = datetime.datetime(year, 1, 1)
        time_to = datetime.datetime(year, 12, 31, 23, 59, 59, 999999)
        charts[year] = (db.session
                        .query(Scrobble.artist, plays)
                        .filter(Scrobble.time >= time_from, Scrobble.time <= time_to)
                        .group_by(func.lower(Scrobble.artist))
                        .order_by(plays.desc())
                        .limit(stat_count)
                        .all()
                        )

    position_changes = {}
    # calculate chart positions
    for year in range(year_from + 1, year_to + 1):
        chart = {artist: position for position, (artist, plays) in enumerate(charts[year], 1)}
        prev_chart = {artist: position for position, (artist, plays) in enumerate(charts[year - 1], 1)}

        prev_charts = (chart for chart_year, chart in charts.items() if chart_year < year)
        prev_artists = {artist for chart in prev_charts for (artist, plays) in chart}

        if year not in position_changes:
            position_changes[year] = {}

        for artist, data in chart.items():
            if artist in prev_chart:
                position_changes[year][artist] = prev_chart[artist] - chart[artist]
            elif artist not in prev_artists:
                position_changes[year][artist] = 'new'

    charts = sorted(charts.items())
    position_changes = position_changes.items()

    return render_template(
        'top_artists_yearly.html',
        charts=charts,
        position_changes=position_changes,
        show_count=show_count
    )


@blueprint.route("/unique/yearly/")
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
                     .filter(Scrobble.time >= time_from, Scrobble.time <= time_to)
                     .count()
                     )
        unique_artists = (db.session
                          .query(Scrobble.artist)
                          .filter(Scrobble.time >= time_from, Scrobble.time <= time_to)
                          .group_by(func.lower(Scrobble.artist))
                          .count()
                          )
        unique_tracks = (db.session
                         .query(Scrobble.artist, Scrobble.track)
                         .filter(Scrobble.time >= time_from, Scrobble.time <= time_to)
                         .group_by(func.lower(Scrobble.artist), func.lower(Scrobble.track))
                         .count()
                         )

        stats[year] = (scrobbles, unique_artists, unique_tracks)

    stats = stats.items()

    return render_template('unique_yearly.html', stats=stats)


@blueprint.route("/milestones/")
def milestones():
    step = request.args.get('step', 10000)
    max_id = db.session.query(func.max(Scrobble.id).label('max_id')).first().max_id
    m_list = range(step, max_id, step)
    scrobbles = db.session.query(Scrobble).filter(Scrobble.id.in_(m_list)).order_by(Scrobble.id.desc())
    return render_template('milestones.html', scrobbles=scrobbles)
