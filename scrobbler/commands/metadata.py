from sqlalchemy import desc, func, text

from scrobbler import db
from scrobbler.meta.artist import sync
from scrobbler.meta.helpers import n_i_fast_comp, n_i_levenshtein
from scrobbler.models import Artist, DiffArtists, DiffTracks, Scrobble


def find_similar_artists(field_name, chunks, start_from):
    """
        `field_name` is a column name in the DiffArtists table ('D1', 'D1L', 'D2', 'D2L', etc.)
    """
    artists = (
        db.session.query(Scrobble.artist.label('artist'))
        .group_by('artist')
        .order_by(desc(func.count(Scrobble.artist)))
        .all()
    )

    artists = list(zip(*artists[start_from::chunks]))[0]  # flatten the results
    already_compared = []

    lowercase = field_name[-1] == 'L'

    for i, artist in enumerate(artists):
        # D1: distances = n_i_fast_comp(artist, artists)
        # D1L: distances = n_i_fast_comp(artist, artists, lowercase=True)
        # D2: distances = n_i_levenshtein(artist, artists, max_dist=10)
        # D2L: distances = n_i_levenshtein(artist, artists, max_dist=10, lowercase=True)
        if field_name[1] == '1':
            # Fastest
            distances = n_i_fast_comp(artist, artists, lowercase=lowercase)
        elif field_name[1] == '2':
            # very slow
            distances = n_i_levenshtein(artist, artists, lowercase=lowercase)

        for D, artist2 in distances:
            if not (0.0 < D < 0.3):
                continue

            if not lowercase:
                pair1 = (artist, artist2)
                pair2 = (artist2, artist)
            else:
                pair1 = (artist.lower(), artist2.lower())
                pair2 = (artist2.lower(), artist.lower())

            if pair1 not in already_compared or pair2 not in already_compared:

                if not lowercase:
                    diff_artist = (
                        db.session.query(DiffArtists)
                        .filter(
                            ((DiffArtists.artist1 == artist) & (DiffArtists.artist2 == artist2)) |
                            ((DiffArtists.artist1 == artist2) & (DiffArtists.artist2 == artist))
                        )
                    ).first()
                else:
                    diff_artist = (
                        db.session.query(DiffArtists)
                        .filter(
                            (
                                (func.lower(DiffArtists.artist1) == artist.lower()) &
                                (func.lower(DiffArtists.artist2) == artist2.lower())
                            ) | (  # OR
                                (func.lower(DiffArtists.artist1) == artist2.lower()) &
                                (func.lower(DiffArtists.artist2) == artist.lower())
                            )
                        )
                    ).first()

                if not diff_artist:
                    # print('DiffArtist create:', artist, artist2)
                    diff_artist = DiffArtists(artist1=artist, artist2=artist2)
                    db.session.add(diff_artist)

                # print('[%d] find=%r   found=%r   D=%.5f' % (i, artist, artist2, D))
                already_compared.append(pair1)

                old_value = getattr(diff_artist, field_name)
                if old_value is None:
                    setattr(diff_artist, field_name, D)
                # else:
                #     print("SKIPPING", artist, artist2, 'old_value =', old_value, 'new_value =', D)

        db.session.commit()


def find_similar_tracks(field_name, top_artists_count, chunks, start_from):
    artists = (
        db.session.query(Scrobble.artist.label('artist'))
        .group_by('artist')
        .order_by(desc(func.count(Scrobble.artist)))[:top_artists_count]
    )

    artists = list(zip(*artists[start_from::chunks]))[0]  # flatten the results
    tracks = {}

    lowercase = field_name[-1] == 'L'
    already_compared = []

    for artist in artists:
        tracks[artist] = (
            db.session.query(Scrobble.track.label('track'))
            .filter(Scrobble.artist == artist)
            .group_by('track')
            .order_by(desc(func.count(Scrobble.track)))
            .all()
        )
        tracks[artist] = list(zip(*tracks[artist]))[0]

    for i, artist in enumerate(artists):
        for i, track in enumerate(tracks[artist]):
            if field_name[1] == '1':
                distances = n_i_fast_comp(track, tracks[artist], lowercase=lowercase)
            elif field_name[1] == '2':
                distances = n_i_levenshtein(track, tracks[artist], lowercase=lowercase)

            for D, track2 in distances:
                if not (0.0 < D < 0.3):
                    continue

                if not lowercase:
                    pair1 = (artist, track, track2)
                    pair2 = (artist, track2, track)
                else:
                    pair1 = (artist.lower(), track.lower(), track2.lower())
                    pair2 = (artist.lower(), track2.lower(), track.lower())

                if pair1 not in already_compared or pair2 not in already_compared:

                    if not lowercase:
                        diff_track = (
                            db.session.query(DiffTracks)
                            .filter(
                                DiffTracks.artist == artist,
                                ((DiffTracks.track1 == track) & (DiffTracks.track2 == track2)) |
                                ((DiffTracks.track1 == track2) & (DiffTracks.track2 == track))
                            )
                        ).first()
                    else:
                        diff_track = (
                            db.session.query(DiffTracks)
                            .filter(
                                func.lower(DiffTracks.artist) == artist.lower(),
                                (
                                    (func.lower(DiffTracks.track1) == track.lower()) &
                                    (func.lower(DiffTracks.track2) == track2.lower())
                                ) | (  # OR
                                    (func.lower(DiffTracks.track1) == track2.lower()) &
                                    (func.lower(DiffTracks.track2) == track.lower())
                                )
                            )
                        ).first()

                    if not diff_track:
                        # print('DiffTrack create:', artist, track, track2)
                        diff_track = DiffTracks(artist=artist, track1=track, track2=track2)
                        db.session.add(diff_track)

                    # print('[%d] artist=%r   find=%r   found=%r-%r   D=%.5f' % (i, artist, track, track2, D))
                    already_compared.append(pair1)

                    old_value = getattr(diff_track, field_name)
                    if old_value is None:
                        setattr(diff_track, field_name, D)
                    # else:
                    #     print("SKIPPING", 'artist=', artist, 'track=', track, 'new_track=', track2, 'old_value =', old_value, 'new_value =', D)

            db.session.commit()


def fix_scrobble_length():
    old_query = (
        db.session.query(Scrobble.artist, Scrobble.track)
        .filter(Scrobble.id < 134266)
        .group_by(Scrobble.artist, Scrobble.track)
    )

    new_query = (
        db.session.query(Scrobble.artist, Scrobble.track, func.avg(Scrobble.length))
        .filter(Scrobble.id >= 134266)
        .group_by(Scrobble.artist, Scrobble.track).all()
    )

    new_data = {'{0} - {1}'.format(*scrobble): int(scrobble[2]) for scrobble in new_query}

    for pair in old_query:
        name = '{0} - {1}'.format(*pair)
        length = new_data.get(name, 0)

        scrobbles = (
            db.session.query(Scrobble)
            .filter(Scrobble.id < 134266, Scrobble.artist == pair[0], Scrobble.track == pair[1])
        )

        scrobbles.update({'length': length})

    db.session.commit()


def download_artist_metadata(limit):
    artists = [obj[0] for obj in (
        db.session.query(Scrobble.artist).group_by(Scrobble.artist)
        .order_by(func.count(Scrobble.artist).desc())
        .limit(limit).all()
    )]

    for artist in artists:
        artist_obj = db.session.query(Artist).filter(Artist.name == artist).count()
        if not artist_obj:
            sync(artist)


def find_sequences():
    query = text('''
        SELECT
            *,
            EXTRACT(EPOCH FROM lag(scrobbles.ended_at) OVER w_s - scrobbles.played_at) AS time_delta,
            EXTRACT(EPOCH FROM lag(scrobbles.ended_at) OVER w_s - scrobbles.played_at) > -120 AS step
        FROM (
            SELECT
                id,
                played_at,
                played_at + length AS ended_at,
                length,
                artist || ' - ' || track AS track
            FROM scrobbles
            ORDER BY played_at
        ) AS scrobbles
        WINDOW w_s as (ORDER BY played_at)
        ORDER BY played_at
    ''')

    result = list(db.engine.execute(query))

    prev_step = None
    seq_count = 1
    seq_started_at = None
    seq_ended_at = None
    seq_tracks = []
    seq_list = []

    for track in result:
        pk, started_at, ended_at, length, name, count, step = track
        if step != prev_step:
            if step or step is None:
                seq_started_at = started_at
                seq_count = 1
                seq_tracks = [track]
            else:
                if seq_count > 1:
                    seq_list.append({
                        'started_at': seq_started_at.strftime('%F %H:%M:%S'),
                        'ended_at': seq_ended_at.strftime('%F %H:%M:%S'),
                        'count': seq_count,
                        'tracks': seq_tracks
                    })
                    # print('sequence ended, count={0}, daterange={1} - {2}'.format(seq_count, seq_started_at, seq_ended_at))
        else:
            if step or step is None:
                seq_count += 1
                seq_ended_at = ended_at
                seq_tracks.append(track)

        prev_step = step

    print("started_at\tended_at\tcount")
    for seq in sorted(seq_list, key=lambda x: -x['count']):
        print("{}\t{}\t{}".format(seq['started_at'], seq['ended_at'], seq['count']))
