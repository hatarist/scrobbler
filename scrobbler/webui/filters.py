import datetime

from scrobbler import app


@app.template_filter('timesince')
def timesince(time, now=None):
    chunks = (
        (60 * 60 * 24 * 365, 'year'),
        (60 * 60 * 24 * 30, 'month'),
        (60 * 60 * 24 * 7, 'week'),
        (60 * 60 * 24, 'day'),
        (60 * 60, 'hour'),
        (60, 'minute'),
        (1, 'second')
    )

    if not now:
        now = datetime.datetime.now().replace(tzinfo=time.tzinfo)

    delta = now - (time - datetime.timedelta(0, 0, time.microsecond))
    since = delta.days * 24 * 60 * 60 + delta.seconds
    if since <= 0:
        return 'in the future'
    for i, (seconds, name) in enumerate(chunks):
        count = since // seconds
        if count != 0:
            break

    if count > 1:
        name += 's'

    return '%(number)d %(type)s ago' % {'number': count, 'type': name}


@app.template_filter('bignum')
def bignum(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '%.2f%s' % (num, ['', 'K', 'M'][magnitude]) if magnitude > 0 else num
