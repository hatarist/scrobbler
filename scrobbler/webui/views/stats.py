import calendar
import datetime

from json import dumps

from flask import render_template, request
from flask_login import current_user, login_required
from sqlalchemy import func, text

from scrobbler import app, db
from scrobbler.models import NowPlaying, Scrobble
from scrobbler.webui.helpers import get_argument
from scrobbler.webui.consts import PERIODS
from scrobbler.webui.views import blueprint


@blueprint.route("/ajax/dashboard/per-hour/")
def ajax_dashboard_per_hour():
    arg_year = request.args.get('year', 'all')
    arg_month = request.args.get('month', 'all')
    arg_artist = request.args.get('artist', '')

    count = func.count(Scrobble.id).label('count')
    time = Scrobble.played_at
    hour = func.extract('hour', time).label('hour')
    weekday = func.extract('isodow', time).label('weekday')
    year = func.extract('year', time).label('year')
    month = func.extract('month', time).label('month')

    year_filter = True if arg_year == 'all' else (year == arg_year)
    month_filter = True if arg_month == 'all' else (month == arg_month)
    artist_filter = True if arg_artist == '' else (Scrobble.artist == arg_artist)

    per_hour = (
        db.session.query(weekday, hour, count)
        .filter(Scrobble.user_id == current_user.id)
        .filter(year_filter, month_filter, artist_filter)
        .group_by('weekday', 'hour').all()
    )
    per_hour = [(d, h + 1, v) for d, h, v in per_hour]
    return dumps(per_hour)


@blueprint.route("/latest/")
@login_required
def last_scrobbles():
    count = get_argument('count', default=app.config['RESULTS_COUNT'])

    scrobbles = (
        db.session.query(Scrobble)
        .filter(Scrobble.user_id == current_user.id)
        .order_by(Scrobble.played_at.desc())
        .limit(count)
        .all()
    )

    nowplaying = (
        db.session.query(NowPlaying)
        .filter(NowPlaying.user_id == current_user.id,
                NowPlaying.played_at + NowPlaying.length >= func.now())
        .order_by(NowPlaying.played_at.desc())
        .first()
    )

    return render_template('latest.html', scrobbles=scrobbles, nowplaying=nowplaying)


@blueprint.route("/unique/monthly/")
@login_required
def unique_monthly():
    stats = {}

    col_year = func.extract('year', Scrobble.played_at)
    year_from, year_to = (
        db.session.query(func.min(col_year), func.max(col_year))
        .filter(Scrobble.user_id == current_user.id)
        .first()
    )

    if not year_from or not year_to:
        return render_template('stats/unique.html', stats=stats)

    year_from, year_to = int(year_from), int(year_to)

    for year in range(year_from, year_to + 1):
        for month in range(1, 13):
            time_from = datetime.datetime(year, month, 1)
            time_to = time_from + datetime.timedelta(days=calendar.monthrange(year, month)[1])

            scrobbles = (
                db.session.query(Scrobble)
                .filter(Scrobble.user_id == current_user.id)
                .filter(Scrobble.played_at >= time_from, Scrobble.played_at <= time_to)
                .count()
            )
            unique_artists = (
                db.session.query(Scrobble.artist)
                .filter(
                    Scrobble.user_id == current_user.id,
                    Scrobble.played_at >= time_from,
                    Scrobble.played_at <= time_to
                )
                .group_by(Scrobble.artist)
                .count()
            )
            unique_tracks = (
                db.session.query(Scrobble.artist, Scrobble.track)
                .filter(Scrobble.user_id == current_user.id)
                .filter(Scrobble.played_at >= time_from, Scrobble.played_at <= time_to)
                .group_by(Scrobble.artist, Scrobble.track)
                .count()
            )

            key = '{:d}-{:02d}'.format(year, month)
            stats[key] = (scrobbles, unique_artists, unique_tracks)

    stats = sorted(stats.items())

    return render_template(
        'stats/unique.html',
        stats=stats
    )


@blueprint.route("/unique/yearly/")
@login_required
def unique_yearly():
    stats = {}

    col_year = func.extract('year', Scrobble.played_at)
    year_from, year_to = (
        db.session.query(func.min(col_year), func.max(col_year))
        .filter(Scrobble.user_id == current_user.id)
        .first()
    )

    if not year_from or not year_to:
        return render_template('stats/unique.html', stats=stats)

    year_from, year_to = int(year_from), int(year_to)

    for year in range(year_from, year_to + 1):
        time_from = datetime.datetime(year, 1, 1)
        time_to = datetime.datetime(year, 12, 31, 23, 59, 59, 999999)
        # select extract(year from played_at) as year, count(id) from scrobbles group by year;
        scrobbles = (
            db.session.query(Scrobble)
            .filter(Scrobble.user_id == current_user.id)
            .filter(Scrobble.played_at >= time_from, Scrobble.played_at <= time_to)
            .count()
        )

        # select extract(year from played_at) as year, sum(1) from scrobbles group by year, artist;
        unique_artists = (
            db.session.query(Scrobble.artist)
            .filter(Scrobble.user_id == current_user.id)
            .filter(Scrobble.played_at >= time_from, Scrobble.played_at <= time_to)
            .group_by(Scrobble.artist)
            .count()
        )
        unique_tracks = (
            db.session.query(Scrobble.artist, Scrobble.track)
            .filter(Scrobble.user_id == current_user.id)
            .filter(Scrobble.played_at >= time_from, Scrobble.played_at <= time_to)
            .group_by(Scrobble.artist, Scrobble.track)
            .count()
        )

        stats[year] = (scrobbles, unique_artists, unique_tracks)

    stats = sorted(stats.items())

    return render_template(
        'stats/unique.html',
        stats=stats
    )


@blueprint.route("/milestones/")
@login_required
def milestones():
    step = get_argument('step', default=10000)

    query = text('SELECT * FROM scrobbles_seq WHERE user_id = :user_id AND seq_id % :step = 0')
    scrobbles = db.engine.execute(query, {'user_id': current_user.id, 'step': step})

    return render_template(
        'stats/milestones.html',
        scrobbles=scrobbles
    )


@blueprint.route("/dashboard/")
@blueprint.route("/dashboard/<period>/")
@login_required
def dashboard(period=None):
    period, days = PERIODS.get(period, PERIODS['1w'])

    col_year = func.extract('year', Scrobble.played_at)
    year_from, year_to = (
        db.session.query(func.min(col_year), func.max(col_year))
        .filter(Scrobble.user_id == current_user.id)
        .first()
    )

    if not year_from or not year_to:
        year_from, year_to = (datetime.date.today().year,) * 2
    else:
        year_from, year_to = int(year_from), int(year_to)

    return render_template(
        'dashboard.html',
        period=period,
        year_min=year_from,
        year_max=year_to,
    )
