from flask import abort, flash, redirect, render_template, request, url_for
from flask.ext.login import current_user, login_required
from sqlalchemy import desc, func

from scrobbler import app, db, meta
from scrobbler.models import Artist, Scrobble
from scrobbler.webui.helpers import get_argument
from scrobbler.webui.views import blueprint


@blueprint.route("/artist/<path:name>/")
@login_required
def artist(name=None):
    sync_meta = get_argument('sync_meta')
    count = get_argument('count', default=app.config['RESULTS_COUNT'])

    if sync_meta:
        result = meta.artist.sync(name, sync_meta)
        if not result:
            flash("Couldn't retrieve information from Last.fm :(", category='error')

        return redirect(url_for('webui.artist', name=name))

    # Meta data
    artist = db.session.query(Artist).filter(Artist.name == name).first()

    # Stats
    scrobbles = func.count(Scrobble.id).label('count')
    first_time = func.min(Scrobble.played_at).label('first_time')

    total_scrobbles, first_time_heard = (
        db.session.query(scrobbles, first_time)
        .filter(Scrobble.user_id == current_user.id)
        .filter(Scrobble.artist == name)
        .order_by(scrobbles.desc()).first()
    )

    if total_scrobbles == 0:
        abort(404)

    year = func.extract('year', Scrobble.played_at).label('year')

    scrobbles_per_year = (
        db.session.query(year, scrobbles)
        .filter(Scrobble.artist == name)
        .group_by(Scrobble.artist, 'year')
        .order_by(year).all()
    )

    max_scrobbles_per_year = max(x[1] for x in scrobbles_per_year)

    # Fill with zeroes if years skipped
    min_year = int(min(x[0] for x in scrobbles_per_year))
    max_year = int(max(x[0] for x in scrobbles_per_year))
    scrobbles_per_year = dict(scrobbles_per_year)
    scrobbles_per_year = {y: scrobbles_per_year.get(y, 0) for y in range(min_year, max_year + 1)}
    scrobbles_per_year = sorted(scrobbles_per_year.items())

    top_albums = (db.session
                  .query(scrobbles, Scrobble.album)
                  .filter(Scrobble.user_id == current_user.id)
                  .filter(Scrobble.artist == name)
                  .group_by(Scrobble.album)
                  .order_by(scrobbles.desc())
                  .limit(count)
                  .all())

    top_tracks = (db.session
                  .query(scrobbles, Scrobble.track)
                  .filter(Scrobble.user_id == current_user.id)
                  .filter(Scrobble.artist == name)
                  .group_by(Scrobble.track)
                  .order_by(scrobbles.desc())
                  .limit(count)
                  .all())

    max_album_scrobbles = top_albums[0][0]
    max_track_scrobbles = top_tracks[0][0]

    top_albums = enumerate(top_albums, start=1)
    top_tracks = enumerate(top_tracks, start=1)

    return render_template(
        'meta/artist.html',
        artist=artist,
        total=total_scrobbles,
        top_albums=top_albums,
        top_tracks=top_tracks,
        max_album_scrobbles=max_album_scrobbles,
        max_track_scrobbles=max_track_scrobbles,
        scrobbles_per_year=scrobbles_per_year,
        max_scrobbles_per_year=max_scrobbles_per_year,
    )


@blueprint.route("/tag/<path:name>/")
@login_required
def tag(name=None):
    sort_by = request.args.get('sort_by')

    if sort_by == 'play_count':
        sort_by = [Artist.playcount.desc()]
    elif sort_by == 'tag_strength':
        sort_by = [desc('strength')]
    else:
        sort_by = [desc('strength'), Artist.playcount.desc()]

    name = name.lower()

    top_artists = (
        db.session.query(
            Artist.name, Artist.tags[name].label('strength'), Artist.playcount)
        .filter(Artist.tags.has_key(name))
        .order_by(*sort_by)
        .all()
    )
    # top_artists = [(name, str) for (name, str, ) in top_artists]

    top_artists = enumerate(top_artists, start=1)

    return render_template(
        'meta/tag.html',
        tag=tag,
        top_artists=top_artists,
    )


@blueprint.route("/search/")
@login_required
def search():
    search_query = request.args.get('q')
    count = get_argument('count', default=app.config['RESULTS_COUNT'])

    if not search_query:
        abort(404)  # :D

    artists = (db.session.query(Scrobble.artist)
               .filter(Scrobble.user_id == current_user.id)
               .filter(Scrobble.artist.ilike('%{}%'.format(search_query))).distinct()
               .limit(count).all())
    tracks = (db.session.query(Scrobble.artist, Scrobble.track)
              .filter(Scrobble.user_id == current_user.id)
              .filter(Scrobble.track.ilike('%{}%'.format(search_query))).distinct()
              .limit(count).all())

    if not artists and not tracks:
        abort(404)

    artists = enumerate(artists, start=1)
    tracks = enumerate(tracks, start=1)

    return render_template('search.html', artists=artists, tracks=tracks)
