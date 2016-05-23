import datetime

from flask import abort, Blueprint, flash, redirect, render_template, request, url_for
from flask import current_app as app
from flask.ext.login import current_user, login_required, login_user, logout_user
from sqlalchemy import func

from scrobbler import db
from scrobbler.models import NowPlaying, Scrobble, User
from scrobbler.webui.consts import PERIODS
from scrobbler.webui.forms import (
    LoginForm,
    RegisterForm,
    ChangeAPIPasswordForm,
    ChangeWebUIPasswordForm,
)
from scrobbler.webui.helpers import show_form_errors

blueprint = Blueprint('webui', __name__)


@blueprint.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403


@blueprint.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


@blueprint.route("/hello/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for('webui.dashboard'))
    else:
        return render_template('index.html')


@blueprint.route("/dashboard/")
@login_required
def dashboard():
    return render_template('dashboard.html')


@blueprint.route("/latest/")
@login_required
def last_scrobbles():
    scrobbles = (db.session
                 .query(Scrobble.id, Scrobble.artist, Scrobble.track, Scrobble.time)
                 .filter(Scrobble.user_id == current_user.id)
                 .order_by(Scrobble.time.desc())
                 .limit(request.args.get('count', app.config['RESULTS_COUNT']))
                 .all()
                 )

    nowplaying = (db.session
                  .query(NowPlaying.id, NowPlaying.artist, NowPlaying.track, NowPlaying.time)
                  .filter(NowPlaying.user_id == current_user.id)
                  .first()
                  )

    return render_template('latest.html', scrobbles=scrobbles, nowplaying=nowplaying)


@blueprint.route("/top/artists/")
@blueprint.route("/top/artists/<period>/")
@login_required
def top_artists(period=None):
    period, days = PERIODS.get(period, PERIODS['1w'])

    scrobbles = func.count(Scrobble.artist).label('count')
    time_from = datetime.datetime.now() - datetime.timedelta(days=days)
    chart = (db.session
             .query(Scrobble.artist, scrobbles)
             .group_by(func.lower(Scrobble.artist))
             .filter(Scrobble.user_id == current_user.id)
             .filter(Scrobble.time >= time_from)
             .order_by(scrobbles.desc())
             .limit(request.args.get('count', app.config['RESULTS_COUNT']))
             .all()
             )

    max_count = chart[0][1]
    chart = enumerate(chart, start=1)

    return render_template(
        'charts/top_artists.html',
        period=period,
        chart=chart,
        max_count=max_count
    )


@blueprint.route("/top/tracks/")
@blueprint.route("/top/tracks/<period>/")
@login_required
def top_tracks(period=None):
    period, days = PERIODS.get(period, PERIODS['1w'])

    scrobbles = func.count(Scrobble.artist).label('count')
    time_from = datetime.datetime.now() - datetime.timedelta(days=days)
    chart = (db.session
             .query(Scrobble.artist, Scrobble.track, scrobbles)
             .group_by(func.lower(Scrobble.artist), func.lower(Scrobble.track))
             .filter(Scrobble.user_id == current_user.id)
             .filter(Scrobble.time >= time_from)
             .order_by(scrobbles.desc())
             .limit(request.args.get('count', app.config['RESULTS_COUNT']))
             .all()
             )

    max_count = chart[0][2]
    chart = enumerate(chart, start=1)

    return render_template(
        'charts/top_tracks.html',
        period=period,
        chart=chart,
        max_count=max_count
    )


@blueprint.route("/top/tracks/yearly/")
@login_required
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
                        .filter(Scrobble.user_id == current_user.id)
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
        'charts/top_tracks_yearly.html',
        charts=charts,
        position_changes=position_changes,
        show_count=show_count
    )


@blueprint.route("/top/artists/yearly/")
@login_required
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
                        .filter(Scrobble.user_id == current_user.id)
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
        'charts/top_artists_yearly.html',
        charts=charts,
        position_changes=position_changes,
        show_count=show_count
    )


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
        'charts/unique_yearly.html',
        stats=stats
    )


@blueprint.route("/milestones/")
@login_required
def milestones():
    step = request.args.get('step', 10000)
    max_id = db.session.query(func.max(Scrobble.id).label('max_id')).first().max_id
    m_list = range(step, max_id, step)
    scrobbles = (db.session
                 .query(Scrobble)
                 .filter(Scrobble.user_id == current_user.id)
                 .filter(Scrobble.id.in_(m_list))
                 .order_by(Scrobble.id.desc())
                 )

    return render_template(
        'charts/milestones.html',
        scrobbles=scrobbles
    )


@blueprint.route("/artist/<name>/")
@login_required
def artist(name=None):

    scrobbles = func.count(Scrobble.track).label('count')
    first_time = func.min(Scrobble.time).label('first_time')
    query = (db.session
             .query(scrobbles, first_time, Scrobble.album, Scrobble.track)
             .filter(Scrobble.user_id == current_user.id)
             .filter(func.lower(Scrobble.artist) == name.lower())
             .order_by(scrobbles.desc())
             )

    total_scrobbles, first_time_heard, _, _ = query.first()

    top_albums = (query.group_by(func.lower(Scrobble.album))
                  .limit(request.args.get('count', app.config['RESULTS_COUNT']))
                  .all()
                  )

    top_tracks = (query.group_by(func.lower(Scrobble.track))
                  .limit(request.args.get('count', app.config['RESULTS_COUNT']))
                  .all()
                  )

    if not top_albums and not top_tracks:
        abort(404)

    max_album_scrobbles = top_albums[0][0]
    max_track_scrobbles = top_tracks[0][0]

    top_albums = enumerate(top_albums, start=1)
    top_tracks = enumerate(top_tracks, start=1)

    return render_template(
        'artist.html',
        total=total_scrobbles,
        top_albums=top_albums,
        top_tracks=top_tracks,
        max_album_scrobbles=max_album_scrobbles,
        max_track_scrobbles=max_track_scrobbles
    )


@blueprint.route("/search/")
@login_required
def search():
    search_query = request.args.get('q')

    if not search_query:
        abort(404)  # :D

    artists = (db.session.query(Scrobble.artist)
               .filter(Scrobble.user_id == current_user.id)
               .filter(Scrobble.artist.ilike('%{}%'.format(search_query))).distinct()
               .limit(request.args.get('count', app.config['RESULTS_COUNT'])).all())
    tracks = (db.session.query(Scrobble.artist, Scrobble.track)
              .filter(Scrobble.user_id == current_user.id)
              .filter(Scrobble.track.ilike('%{}%'.format(search_query))).distinct()
              .limit(request.args.get('count', app.config['RESULTS_COUNT'])).all())

    if not artists and not tracks:
        abort(404)

    artists = enumerate(artists, start=1)
    tracks = enumerate(tracks, start=1)

    return render_template('search.html', artists=artists, tracks=tracks)


@blueprint.route("/register/", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            api_password=form.password.data,
            webui_password=form.password.data,
            email=form.email.data
        )
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash('Happy scrobbling!', 'success')
        return redirect(url_for('webui.dashboard'))
    else:
        show_form_errors(form)

    return render_template('auth/register.html', form=form)


@blueprint.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = db.session.query(User).filter(
            User.username == form.username.data,
        ).first()

        if user is None or not user.validate_webui_password(form.password.data):
            abort(403)

        login_user(user, remember=form.remember_me.data)
        flash('Logged in successfully.')
        return redirect(url_for('webui.index'))
    else:
        show_form_errors(form)

    return render_template('auth/login.html', form=form)


@blueprint.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('webui.index'))


@blueprint.route("/settings/", methods=["GET", "POST"])
@login_required
def settings():
    form_api_pass = ChangeAPIPasswordForm()
    form_webui_pass = ChangeWebUIPasswordForm()

    if form_api_pass.validate_on_submit() and form_api_pass.api_pass.data:
        if not current_user.validate_api_password(form_api_pass.current_password.data):
            flash("Wrong current API password.", 'error')
        else:
            current_user.api_password = form_api_pass.password.data
            db.session.commit()
            flash("API password has been changed.", 'success')
    else:
        show_form_errors(form_api_pass)

    if form_webui_pass.validate_on_submit() and form_webui_pass.webui_pass.data:
        if not current_user.validate_webui_password(form_webui_pass.current_password.data):
            flash("Wrong current WebUI password.", 'error')
        else:
            current_user.webui_password = form_webui_pass.password.data
            db.session.commit()
            flash("WebUI password has been changed.", 'success')
    else:
        show_form_errors(form_webui_pass)

    return render_template(
        'settings.html',
        form_api_pass=form_api_pass,
        form_webui_pass=form_webui_pass,
    )
