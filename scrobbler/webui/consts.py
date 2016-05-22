from collections import OrderedDict


PERIODS = OrderedDict([
    ('1w', ('last week', 7)),
    ('1m', ('last month', 30)),
    ('3m', ('last 3 months', 30 * 3)),
    ('6m', ('last 6 months', 30 * 6)),
    ('1y', ('last year', 365)),
    ('all', ('overall', 99999)),
])
