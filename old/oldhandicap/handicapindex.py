import datetime
import os
import re
import sys

from collections import namedtuple

NOW = datetime.datetime.now()
TODAY = datetime.datetime(NOW.year, NOW.month, NOW.day)
TOMORROW = TODAY + datetime.timedelta(days=1)

STANDARD_COURSE_RATING = 113

EXPECTED_FIELDS = {'date', 'course', 'tee', 'adjusted_score', 'pcc'}

FIELD_MAP = {'adjusted_score': 'adjusted_strokes'}

ISO_DATE_RE = r'^(\d{4})-(\d{1,2})-(\d{1,2})$'


HandicapIndex = namedtuple('HandicapIndex', 'date handicap_index')


class Round:
    def __init__(self, date, handicap_index=None, course=None, tee=None,
                 stableford=None, strokes=None, discards=None,
                 pcc=0, adjusted_strokes=None, differential=None):

        self.date = as_datetime(date)
        self.course = course
        self.tee = tee
        self.rating = get_rating(course, tee, date)
        self.pcc = pcc

        self.handicap_index = handicap_index
        self.antihandicap_index8 = None
        self.antihandicap_index12 = None
        self.course_handicap = self.rating.calc_handicap(handicap_index)

        self.raw_stableford = stableford
        self.raw_strokes = strokes
        self.raw_discards = discards
        self.raw_adjusted_strokes = adjusted_strokes
        self.raw_differential = differential

        (self.stableford,
         self.strokes,
         self.discards,
         self.adjusted_strokes,
         self.differential,
         self.nett_strokes) = self.compute_and_check(stableford,
                                                     strokes,
                                                     discards,
                                                     adjusted_strokes,
                                                     differential)
        self.old_handicap = None

    def compute_and_check(self, stableford, strokes, discards,
                          adjusted_strokes, differential):
        nett_strokes = differential = None
        r = self.rating

        # Compute adjusted strokes if not known
        if not adjusted_strokes:
            if discards is not None and strokes:
                adjusted_strokes = strokes - discards

        # Stableford and adjusted strokes contain the same information,
        # so figure one out from the other
        if self.course_handicap:
            if stableford and not adjusted_strokes:
                adjusted_strokes = (r.par
                                    + self.course_handicap
                                    + (36 - stableford))
            if adjusted_strokes and not stableford:
                stableford = (36
                              + r.par + self.course_handicap
                              - adjusted_strokes)

        # If (gross) stroke not provided, calculate from adjusted strokes
        # which will have been set by now if unset but stableford is available
        if not strokes:
            if adjusted_strokes and discards is not None:
                strokes = adjusted_strokes + discards

        if strokes:
            nett_strokes = strokes - self.course_handicap

        if adjusted_strokes:   # Will have been set by now if possible
            d = r.differential_from_adjusted_strokes(adjusted_strokes)
            differential = d + self.pcc

        self.validate(stableford, self.raw_stableford, 'stableford')
        self.validate(strokes, self.raw_strokes, 'strokes')
        self.validate(discards, self.raw_discards, 'discards')
        self.validate(adjusted_strokes, self.raw_adjusted_strokes,
                      'adjusted_strokes')
        self.validate(differential, self.raw_differential, 'differential')

        return (stableford,
                strokes,
                discards,
                adjusted_strokes,
                differential,
                nett_strokes)

    def fmt(self, attr):
        v = getattr(self, attr, None)
        return '' if v is None else f'{attr}={repr(v)}'

    def validate(self, final, raw, attr):
        """Checks for inconsistencies between input and calculated values."""
        if raw is not None:
            if round(final, 2) != round(raw, 2):
                raise Exception(f'Inconsistent values for {attr}: '
                                f' raw: {raw} vs. calculated {final}.')

    def has_differential(self):
        return self.differential is not None

    def __repr__(self):
        parts = (
            f'date={self.date.isoformat()[:10]}',
            self.fmt('course'),
            self.fmt('tee'),
            self.fmt('stableford'),
            self.fmt('adjusted_strokes'),
            self.fmt('differential'),
            self.fmt('handicap_index'),
            self.fmt('strokes'),
            self.fmt('discards'),
            self.fmt('nett_strokes'),
            f'antihandicap_index={self.antihandicap_index12}',
#            f'antihandicap_index8={self.antihandicap_index8}',
            self.fmt('old_handicap'),
        )
        return 'Round(%s)' % ',\n      '.join(p for p in parts if p)

    def __eq__(self, other):
        keys = {k for k in set(self.__dict__.keys())
                           .union(set(other.__dict__.keys()))
                if not k.startswith('raw_')}
        return all(getattr(self, k, None) == getattr(other, k, None)
                   for k in keys)

    def diffs(self, other):
        keys = {k for k in set(self.__dict__.keys())
                           .union(set(other.__dict__.keys()))
                if not k.startswith('raw_')}
        return {k for k in keys
                if not(getattr(self, k, None) == getattr(other, k, None))}


class Tee:
    def __init__(self, course, tee, par, course_rating, slope_rating,
                 until=None):
        self.course = course
        self.tee = tee
        self.par = par
        self.course_rating = course_rating
        self.slope_rating = slope_rating
        self.until = as_date(until) if until else until

    def __str__(self):
        return (f'Tee(course={repr(self.course)}, '
                f'tee={repr(self.tee)}, '
                f'par={self.par}, '
                f'course_rating={self.course_rating}, '
                f'slope_rating={self.slope_rating})')


class Rating:
    def __init__(self, par, course, slope):
        self.par = par
        self.course = course
        self.slope = slope

    def differential_from_stableford(self, stableford, handicap_index):
        handicap = self.calc_handicap(handicap_index)
        to_rating = handicap + 36 - stableford + self.par - self.course
        return round1(to_rating * STANDARD_COURSE_RATING / self.slope)

    def differential_from_adjusted_strokes(self, adjusted_strokes):
        to_rating = adjusted_strokes - self.course
        return round1(to_rating * STANDARD_COURSE_RATING / self.slope)

    def calc_handicap(self, handicap_index):
        if handicap_index is None:
            return None
        return int(round(handicap_index * self.slope / STANDARD_COURSE_RATING))

    def __eq__(self, other):
        return all((self.par == other.par,
                    self.course == other.course,
                    self.slope == other.slope))


class History:
    def __init__(self, rounds, hcap_date=None, dated_hcap=None):
        rounds.sort(key=lambda r: r.date)
        self.rounds = rounds
        if hcap_date is not None:
            hcap_date = typed_value('date', hcap_date)
        for r in rounds:
            if not r.has_differential():
                print('No differential:')
                print(r)
                print('\n\n')
        if len(rounds) >= 20:
            for i in range(19, len(rounds)):
                diffs = [r.differential for r in rounds[i-19:i+1]]
                diffs.sort()
                rnd = rounds[i]
                rnd.handicap_index = round1(sum(diffs[:8]) / 8)
                rnd.antihandicap_index12 = round1(sum(diffs[-12:])/12)
                rnd.antihandicap_index8 = round1(sum(diffs[-8:])/8)
                rnd.median_adj_to_par = round1(sum(diffs[-11:-9])/2)
                if hcap_date:
                    if rnd.date == hcap_date:
                        rnd.old_handicap = dated_hcap
                    elif rounds[i-1].old_handicap:
                        prev_old_hcap = rounds[i-1].old_handicap
                        par = TeeMap[(rnd.course, rnd.tee)].par
                        delta = (rnd.adjusted_strokes
                                 - round(prev_old_hcap + .001, 0)
                                 - par)
                        rnd.old_handicap = prev_old_hcap
                        if delta > 4:
                            rnd.old_handicap += 0.1
                        elif delta < 0:
                            rnd.old_handicap += 0.4 * delta
                        rnd.old_handicap = round(rnd.old_handicap, 1)
    def write(self, path):
        with open(path, 'w') as f:
            f.write('date,handicap_index,antihandicap_index,'
                    'median_adj_to_par,old_handicap\n')
            for r in self.rounds:
                if r.handicap_index is not None:
                    parts = (r.date.isoformat()[:10],
                             str(r.handicap_index),
                             str(r.antihandicap_index12),
                             str(r.median_adj_to_par),
                             str(r.old_handicap or '')
                             )
                    f.write(','.join(parts) + '\n')


def get_rating(course, tee, date):
    tees = [t for t in TEES if t.course == course and t.tee == tee]
    if not tees:
        if any(t.course == course for t in TEES):
            raise Exception(f'No tee called "{tee}" for course "{course}".')
        else:
            raise Exception(f'No course called "{course}" in tees database.')
    if len(tees) > 1:
        tees.sort(key=lambda t: t.date if t.date else TOMORROW)
        for t in tees:
            if t.until is None or t.until > date:
                break
    else:
        t = tees[0]
    return Rating(t.par, t.course_rating, t.slope_rating)


def as_datetime(d):
    if isinstance(d, datetime.datetime):
        return d
    elif type(d) is str and re.match(ISO_DATE_RE, d):
        return datetime.date.fromisoformat(d)
    else:
        raise Exception('Bad date: {d}')


def calc_handicap_index(rounds):
    assert len(rounds) == 20
    date = rounds[-1].date
    rounds.sort(key=lambda r: r.differential)
    HI = round1(sum(r.differential for r in rounds[:8]) / 8)
    return HandicapIndex(date.date().isoformat(), HI)


def load_flat_file(path, sep='\t'):
    """
    Load flat file and return list of Rounds.
    """
    with open(path) as f:
        lines = [L.strip() for L in f.readlines() if L.strip()]
    header = lines[0]
    fields = header.split(sep)

    assert set(fields) == EXPECTED_FIELDS
    return [
         Round(**{FIELD_MAP.get(h, h): typed_value(h, v)
                  for (h, v) in zip(fields, line.split(sep))})
         for line in lines[1:]
    ]


def typed_value(field, v):
    if field == 'date':
        return datetime.datetime.strptime(v, '%Y-%m-%d')
    elif field in ('adjusted_score', 'pcc'):
        return int(v)
    elif field in ('course', 'tee'):
        return v
    else:
        print(f'Unknown field "{field}".', file=sys.stderr)
        sys.exit(1)


def round1(v):
    return round(v + .01, 1)


def nvl(v, default):
    return default if v is None else v



TEES = [
    Tee('Broomieknowe', 'white', 70, 69.9, 124),
    Tee('Broomieknowe', 'white70', 70, 70.0, 124),  # for old scores
    Tee('Broomieknowe', 'yellow', 69, 68.0, 120),
    Tee("King's Acre", 'white', 70, 68.8, 121),
    Tee("King's Acre", 'yellow', 70, 67.7, 119),
]


TeeMap = {
    (t.course, t.tee): t for t in TEES
}


if __name__ == '__main__':
    rounds = load_flat_file(os.path.expanduser('~/iNJR/golf/NickScores.tsv'))
    history = History(rounds, hcap_date='2020-10-03', dated_hcap=22.4)
    history.write(os.path.expanduser('~/iNJR/golf/NickHandicaps.csv'))
