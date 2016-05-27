from flask import abort, flash, redirect, render_template, request, url_for
from flask.ext.login import current_user, login_required
from sqlalchemy import func

from scrobbler import app, db, meta
from scrobbler.models import Artist, ArtistTag, Scrobble
from scrobbler.webui.helpers import get_argument
from scrobbler.webui.views import blueprint


@blueprint.route("/artist/<name>/")
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
    artist = db.session.query(Artist).filter(func.lower(Artist.name) == name.lower()).first()

    # Stats
    scrobbles = func.count(Scrobble.track).label('count')
    first_time = func.min(Scrobble.played_at).label('first_time')

    total_scrobbles, first_time_heard = (
        db.session.query(scrobbles, first_time)
        .filter(Scrobble.user_id == current_user.id)
        .filter(func.lower(Scrobble.artist) == name.lower())
        .order_by(scrobbles.desc()).first()
    )

    top_albums = (db.session
                  .query(scrobbles, Scrobble.album)
                  .filter(Scrobble.user_id == current_user.id)
                  .filter(func.lower(Scrobble.artist) == name.lower())
                  .group_by(Scrobble.album)
                  .order_by(scrobbles.desc())
                  .limit(count)
                  .all())

    top_tracks = (db.session
                  .query(scrobbles, Scrobble.track)
                  .filter(Scrobble.user_id == current_user.id)
                  .filter(func.lower(Scrobble.artist) == name.lower())
                  .group_by(Scrobble.track)
                  .order_by(scrobbles.desc())
                  .limit(count)
                  .all())

    if not top_albums and not top_tracks:
        abort(404)

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
        max_track_scrobbles=max_track_scrobbles
    )


@blueprint.route("/tag/<name>/")
@login_required
def tag(name=None):
    scrobbles = func.count(Scrobble.artist).label('count')

    query = (db.session
             .query(ArtistTag)
             .filter(func.lower(ArtistTag.tag) == name.lower())
             .filter(Scrobble.artist == ArtistTag.artist.name)
             .order_by(scrobbles.desc())
             .all()
             )

    top_artists = [(artist_tag.artist, artist_tag.strength) for artist_tag in query]
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
