import distance


def n_i_fast_comp(value, array, lowercase=False):
    """ A wrapper for `distance.ifast_comp` that returns normalized values. """
    if lowercase:
        value = value.lower()
        array = (item.lower() for item in array)

    distances = distance.ifast_comp(value, array)

    for a_distance, item in distances:
        a_length = float(max(len(value), len(item)))
        yield (float(a_distance) / a_length, item)


def n_i_levenshtein(value, array, lowercase=False, max_dist=10):
    """ A wrapper for `distance.ilevenshtein` that returns normalized values. """
    if lowercase:
        value = value.lower()
        array = (item.lower() for item in array)

    distances = distance.ilevenshtein(value, array, max_dist=max_dist)

    for a_distance, item in distances:
        a_length = float(max(len(value), len(item)))
        yield (float(a_distance) / a_length, item)
