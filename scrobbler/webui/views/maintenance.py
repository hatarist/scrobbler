from flask import abort, flash, redirect, render_template, url_for
from flask.ext.login import login_required
from sqlalchemy import func

from scrobbler import db
from scrobbler.models import DiffArtists, Scrobble
from scrobbler.webui.helpers import get_argument
from scrobbler.webui.views import blueprint


@blueprint.route("/maintenance/artists/")
@login_required
def maintenance_artists():
    show_ignored = get_argument('show_ignored', arg_type=bool)

    artist_count = db.session.query(
        Scrobble.artist, func.count(Scrobble.artist).label('count')
    ).group_by(Scrobble.artist).all()

    artist_count = {artist: count for artist, count in artist_count}

    diffs = db.session.query(
        DiffArtists.id, DiffArtists.artist1, DiffArtists.artist2
    ).filter(DiffArtists.ignore == show_ignored).order_by(DiffArtists.id.asc()).all()

    # diffs = sorted(diffs, key=lambda x: artist_count.get(x[1], 0) + artist_count.get(x[2], 0))
    return render_template('maintenance/artists.html', diffs=diffs, artist_count=artist_count)


@blueprint.route("/maintenance/artists/<int:id>/<int:direction>/")
@login_required
def maintenance_artist_fix(id, direction):
    diff = db.session.query(DiffArtists).get(id)

    if not diff:
        abort(404)

    if direction == 0:  # toggle ignore
        diff.ignore = not diff.ignore
        db.session.commit()
        return redirect(url_for('webui.maintenance_artists'))
    elif direction == 1:  # artist1 -> artist2
        replace_what, replace_with = (diff.artist1, diff.artist2)
    elif direction == 2:  # artist2 -> artist1
        replace_what, replace_with = (diff.artist2, diff.artist1)

    scrobbles = db.session.query(Scrobble).filter(Scrobble.artist == replace_what)
    count_to_replace = scrobbles.count()

    for scrobble in scrobbles:
        print('[%d] %s -> %s' % (scrobble.id, scrobble.artist, replace_with))

    scrobbles.update({'artist': replace_with})
    db.session.delete(diff)
    db.session.commit()

    flash('{} scrobbles were replaced successfully!'.format(count_to_replace), category='success')
    return redirect(url_for('webui.maintenance_artists'))
