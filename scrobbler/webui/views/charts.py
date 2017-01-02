import datetime

from flask import render_template, request
from flask_login import current_user, login_required
from sqlalchemy import func

from scrobbler import app, db
from scrobbler.models import Scrobble
from scrobbler.webui.consts import PERIODS
from scrobbler.webui.helpers import range_to_datetime
from scrobbler.webui.views import blueprint


def get_chart_params(period):
    period, days = PERIODS.get(period, PERIODS['1w'])
    time_from = request.args.get('from')
    time_to = request.args.get('to')
    custom_range = False
    count = int(request.args.get('count', app.config['RESULTS_COUNT']))

    if time_from is None or time_to is None:
        time_from = datetime.datetime.now() - datetime.timedelta(days=days)
        time_to = datetime.datetime.now()
    else:
        time_from, time_to = range_to_datetime(time_from, time_to)
        custom_range = True

    return {
        'period': period,
        'days': days,
        'time_from': time_from,
        'time_to': time_to,
        'custom_range': custom_range,
        'count': count,
    }


@blueprint.route("/top/artists/")
@blueprint.route("/top/artists/<period>/")
@login_required
def top_artists(period=None):
    params = get_chart_params(period)

    scrobbles = func.count(Scrobble.artist).label('count')
    chart = (
        db.session.query(Scrobble.artist, scrobbles)
        .group_by(Scrobble.artist)
        .filter(
            Scrobble.user_id == current_user.id,
            Scrobble.played_at >= params['time_from'],
            Scrobble.played_at <= params['time_to'],
        )
        .order_by(scrobbles.desc())
        .limit(params['count'])
        .all()
    )

    return render_template(
        'charts/top_artists.html',
        chart=enumerate(chart, start=1),
        max_count=chart[0][1] if chart else 0,
        **params
    )


@blueprint.route("/top/tracks/")
@blueprint.route("/top/tracks/<period>/")
@login_required
def top_tracks(period=None):
    params = get_chart_params(period)

    scrobbles = func.count(Scrobble.artist).label('count')
    chart = (
        db.session.query(Scrobble.artist, Scrobble.track, scrobbles)
        .group_by(Scrobble.artist, Scrobble.track, Scrobble.user_id == current_user.id)
        .filter(
            Scrobble.played_at >= params['time_from'],
            Scrobble.played_at <= params['time_to'],
        )
        .order_by(scrobbles.desc())
        .limit(params['count'])
        .all()
    )

    return render_template(
        'charts/top_tracks.html',
        chart=enumerate(chart, start=1),
        max_count=chart[0][2] if chart else 0,
        **params
    )


@blueprint.route("/top/yearly/tracks/")
@login_required
def top_yearly_tracks():
    scrobbles = func.count(Scrobble.artist).label('count')
    charts = {}

    col_year = func.extract('year', Scrobble.played_at)
    year_from, year_to = db.session.query(func.min(col_year), func.max(col_year)).first()
    year_from, year_to = int(year_from), int(year_to)

    stat_count = 10000
    show_count = 100

    for year in range(year_from, year_to + 1):
        time_from = datetime.datetime(year, 1, 1)
        time_to = datetime.datetime(year, 12, 31, 23, 59, 59, 999999)
        charts[year] = (
            db.session.query(Scrobble.artist, Scrobble.track, scrobbles)
            .filter(
                Scrobble.user_id == current_user.id,
                Scrobble.played_at >= time_from,
                Scrobble.played_at <= time_to
            )
            .group_by(Scrobble.artist, Scrobble.track)
            .order_by(scrobbles.desc())
            .limit(stat_count)
            .all()
        )

    position_changes = {}

    for year in range(year_from + 1, year_to + 1):
        chart = {
            '{} – {}'.format(artist, track): position
            for position, (artist, track, scrobbles) in enumerate(charts[year], 1)
        }

        prev_chart = {
            '{} – {}'.format(artist, track): position
            for position, (artist, track, scrobbles) in enumerate(charts[year - 1], 1)
        }

        prev_charts = (
            chart for chart_year, chart in charts.items() if chart_year < year
        )

        prev_tracks = {
            '{} – {}'.format(artist, track)
            for chart in prev_charts
            for (artist, track, scrobbles) in chart
        }

        if year not in position_changes:
            position_changes[year] = {}

        for title in chart:
            if title in prev_chart:
                position_changes[year][title] = prev_chart[title] - chart[title]
            elif title not in prev_tracks:
                position_changes[year][title] = 'new'

    charts = sorted(charts.items())

    return render_template(
        'charts/top_yearly_tracks.html',
        charts=charts,
        position_changes=position_changes,
        show_count=show_count
    )


@blueprint.route("/top/yearly/artists/")
@login_required
def top_yearly_artists():
    scrobbles = func.count(Scrobble.artist).label('count')
    charts = {}

    col_year = func.extract('year', Scrobble.played_at)
    year_from, year_to = db.session.query(func.min(col_year), func.max(col_year)).first()
    year_from, year_to = int(year_from), int(year_to)

    stat_count = 1000
    show_count = 100

    for year in range(year_from, year_to + 1):
        time_from = datetime.datetime(year, 1, 1)
        time_to = datetime.datetime(year, 12, 31, 23, 59, 59, 999999)
        charts[year] = (
            db.session.query(Scrobble.artist, scrobbles)
            .filter(Scrobble.user_id == current_user.id)
            .filter(Scrobble.played_at >= time_from, Scrobble.played_at <= time_to)
            .group_by(Scrobble.artist)
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
        'charts/top_yearly_artists.html',
        charts=charts,
        position_changes=position_changes,
        show_count=show_count
    )
