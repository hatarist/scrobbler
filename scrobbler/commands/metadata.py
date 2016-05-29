from sqlalchemy import desc, func

from scrobbler import db
from scrobbler.meta.helpers import n_i_fast_comp, n_i_levenshtein
from scrobbler.models import DiffArtists, Scrobble


def find_similar_artists(field_name, chunks, start_from):
    """
        `field_name` is a column name in the DiffArtists table ('D1', 'D1L', 'D2', 'D2L', etc.)
    """
    artists = db.session.query(
        func.count(Scrobble.artist).label('cnt'), Scrobble.artist.label('artist')
    ).group_by('artist').order_by(desc('cnt')).all()

    artists = artists[start_from::chunks]

    artists_only = [artist[1] for artist in artists]
    already_compared = []

    for i, artist in enumerate(artists_only):
        lowercase = field_name[-1] == 'L'
        # D1: distances = n_i_fast_comp(artist, artists_only)
        # D1L: distances = n_i_fast_comp(artist, artists_only, lowercase=True)
        # D2: distances = n_i_levenshtein(artist, artists_only, max_dist=10)
        # D2L: distances = n_i_levenshtein(artist, artists_only, max_dist=10, lowercase=True)

        if field_name[1] == '1':
            # Fastest
            distances = n_i_fast_comp(artist, artists_only, lowercase=lowercase)
        elif field_name[1] == '2':
            # very slow
            distances = n_i_levenshtein(artist, artists_only, lowercase=lowercase)

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
                            ((func.lower(DiffArtists.artist1) == artist.lower()) & (func.lower(DiffArtists.artist2) == artist2.lower())) |
                            ((func.lower(DiffArtists.artist1) == artist2.lower()) & (func.lower(DiffArtists.artist2) == artist.lower()))
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
