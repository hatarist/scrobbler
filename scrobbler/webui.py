"""Provides a web-interface."""

import datetime

from flask import abort, Blueprint, redirect, render_template, request, url_for
from flask import current_app as app
from sqlalchemy import func

from scrobbler import db
from scrobbler.constants import PERIODS
from scrobbler.models import Scrobble

blueprint = Blueprint('webui', __name__)


@blueprint.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@blueprint.route("/")
def index():
    return redirect(url_for('webui.dashboard'))


@blueprint.route("/dashboard/")
def dashboard():
    return render_template('dashboard.html')


@blueprint.route("/latest/")
def last_scrobbles():
    scrobbles = (db.session
                 .query(Scrobble.id, Scrobble.artist, Scrobble.track, Scrobble.time)
                 .order_by(Scrobble.time.desc())
                 .limit(request.args.get('count', app.config['RESULTS_COUNT']))
                 .all()
                 )
    return render_template('latest.html', scrobbles=scrobbles)


@blueprint.route("/top/artists/")
@blueprint.route("/top/artists/<period>/")
def top_artists(period=None):
    period, days = PERIODS.get(period, PERIODS['1w'])

    scrobbles = func.count(Scrobble.artist).label('count')
    time_from = datetime.datetime.now() - datetime.timedelta(days=days)
    chart = (db.session
             .query(Scrobble.artist, scrobbles)
             .group_by(func.lower(Scrobble.artist))
             .filter(Scrobble.time >= time_from)
             .order_by(scrobbles.desc())
             .limit(request.args.get('count', app.config['RESULTS_COUNT']))
             .all()
             )

    max_count = chart[0][1]
    chart = enumerate(chart, start=1)

    return render_template('top_artists.html', period=period, chart=chart, max_count=max_count)


@blueprint.route("/top/tracks/")
@blueprint.route("/top/tracks/<period>/")
def top_tracks(period=None):
    period, days = PERIODS.get(period, PERIODS['1w'])

    scrobbles = func.count(Scrobble.artist).label('count')
    time_from = datetime.datetime.now() - datetime.timedelta(days=days)
    chart = (db.session
             .query(Scrobble.artist, Scrobble.track, scrobbles)
             .group_by(func.lower(Scrobble.artist), func.lower(Scrobble.track))
             .filter(Scrobble.time >= time_from)
             .order_by(scrobbles.desc())
             .limit(request.args.get('count', app.config['RESULTS_COUNT']))
             .all()
             )

    max_count = chart[0][2]
    chart = enumerate(chart, start=1)

    return render_template('top_tracks.html', period=period, chart=chart, max_count=max_count)


@blueprint.route("/top/tracks/yearly/")
def top_tracks_yearly():
    scrobbles = func.count(Scrobble.artist).label('count')
    charts = {}

    year_from = 2006
    year_to = 2016
    stat_count = 10000
    show_count = 100

    for year in range(year_from, year_to + 1):
        time_from = datetime.datetime(year, 1, 1)
        time_to = datetime.datetime(year, 12, 31, 23, 59, 59, 999999)
        charts[year] = (db.session
                        .query(Scrobble.artist, Scrobble.track, scrobbles)
                        .filter(Scrobble.time >= time_from, Scrobble.time <= time_to)
                        .group_by(func.lower(Scrobble.artist), func.lower(Scrobble.track))
                        .order_by(scrobbles.desc())
                        .limit(stat_count)
                        .all()
                        )

    position_changes = {}

    for year in range(year_from + 1, year_to + 1):

        chart = {
            '{} – {}'.format(artist, track): position for position, (artist, track, scrobbles) in enumerate(charts[year], 1)
        }

        prev_chart = {
            '{} – {}'.format(artist, track): position for position, (artist, track, scrobbles) in enumerate(charts[year - 1], 1)
        }

        prev_charts = (chart for chart_year, chart in charts.items() if chart_year < year)
        prev_tracks = {'{} – {}'.format(artist, track) for chart in prev_charts for (artist, track, scrobbles) in chart}

        if year not in position_changes:
            position_changes[year] = {}

        for title in chart:
            if title in prev_chart:
                position_changes[year][title] = prev_chart[title] - chart[title]
            elif title not in prev_tracks:
                position_changes[year][title] = 'new'

    charts = sorted(charts.items())

    return render_template(
        'top_tracks_yearly.html',
        charts=charts,
        position_changes=position_changes,
        show_count=show_count
    )


@blueprint.route("/top/artists/yearly/")
def top_artists_yearly():
    scrobbles = func.count(Scrobble.artist).label('count')
    charts = {}

    year_from = 2006
    year_to = 2016
    stat_count = 1000
    show_count = 100

    for year in range(year_from, year_to + 1):
        time_from = datetime.datetime(year, 1, 1)
        time_to = datetime.datetime(year, 12, 31, 23, 59, 59, 999999)
        charts[year] = (db.session
                        .query(Scrobble.artist, scrobbles)
                        .filter(Scrobble.time >= time_from, Scrobble.time <= time_to)
                        .group_by(func.lower(Scrobble.artist))
                        .order_by(scrobbles.desc())
                        .limit(stat_count)
                        .all()
                        )

    position_changes = {}

    for year in range(year_from + 1, year_to + 1):
        chart = {artist: position for position, (artist, scrobbles) in enumerate(charts[year], 1)}
        prev_chart = {
            artist: position for position, (artist, scrobbles) in enumerate(charts[year - 1], 1)
        }

        prev_charts = (chart for chart_year, chart in charts.items() if chart_year < year)
        prev_artists = {artist for chart in prev_charts for (artist, scrobbles) in chart}

        if year not in position_changes:
            position_changes[year] = {}

        for artist, data in chart.items():
            if artist in prev_chart:
                position_changes[year][artist] = prev_chart[artist] - chart[artist]
            elif artist not in prev_artists:
                position_changes[year][artist] = 'new'

    charts = sorted(charts.items())

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
    scrobbles = (db.session
                 .query(Scrobble)
                 .filter(Scrobble.id.in_(m_list))
                 .order_by(Scrobble.id.desc())
                 )

    return render_template('milestones.html', scrobbles=scrobbles)


@blueprint.route("/artist/<name>/")
def artist(name=None):

    scrobbles = func.count(Scrobble.track).label('count')
    first_time = func.min(Scrobble.time).label('first_time')
    query = (db.session
             .query(scrobbles, Scrobble.track, first_time)
             .filter(func.lower(Scrobble.artist) == name.lower())
             .order_by(scrobbles.desc())
             )

    total_scrobbles, _, first_time_heard = query.first()

    chart = (query.group_by(func.lower(Scrobble.track))
             .limit(request.args.get('count', app.config['RESULTS_COUNT']))
             .all()
             )

    if not chart:
        abort(404)

    max_count = chart[0][0]
    chart = enumerate(chart, start=1)

    return render_template('artist.html', chart=chart, total=total_scrobbles, max_count=max_count)


@blueprint.route("/search/")
def search():
    search_query = request.args.get('q')

    if not search_query:
        abort(404)  # :D

    artists = (db.session.query(Scrobble.artist)
               .filter(Scrobble.artist.ilike('%{}%'.format(search_query))).distinct()
               .limit(request.args.get('count', app.config['RESULTS_COUNT'])).all())
    tracks = (db.session.query(Scrobble.artist, Scrobble.track)
              .filter(Scrobble.track.ilike('%{}%'.format(search_query))).distinct()
              .limit(request.args.get('count', app.config['RESULTS_COUNT'])).all())

    if not artists and not tracks:
        abort(404)

    artists = enumerate(artists, start=1)
    tracks = enumerate(tracks, start=1)

    return render_template('search.html', artists=artists, tracks=tracks)
