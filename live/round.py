import datetime
import re

BASE = 113

STABLEFORD_TO_DESC = {
    0: 'double',
    1: 'bogey',
    2: 'par',
    3: 'birdie',
    4: 'eagle',
    5: 'albatross',
    6: 'albatross',
}

DATE_RE = re.compile(r'^([0-9]{4})-?([0-9]{2})-?([0-9]{2})$')


class Tee:
    def __init__(self, course_name, tee_name, course_rating, slope_rating,
                 par=None, SI=None, allowance=1.0, names=None, lengths=None,
                 stroke_indexes=None, pars=None, colour=None):
        self.course_name = course_name
        self.tee_name = tee_name
        self.course_rating = course_rating
        self.slope_rating = slope_rating
        self.par = par or pars
        self.SI = SI or stroke_indexes
        if not self.par:
            raise Exception('No pars specified')
        if not self.SI:
            raise Excception('No stroke indexes specified')
        self.allowance = allowance
        self.names = names
        self.lengths = lengths

    def __str__(self):
        par = sum(self.par)
        holes = ''.join(f'{h:4d}' for h in range(1,19))
        pars = ''.join(f'{p:4d}' for p in self.par)
        SI = ''.join(f'{si:4d}' for si in self.SI)
        outpar = sum(self.par[:9])
        inpar = sum(self.par[9:])
        assert par == outpar + inpar
        return (f'{self.name}  '
                f'CR {self.course_rating}  SR {self.slope_rating}  Par {par}'
                f'  OUT {outpar}   IN {inpar}\n'
                f'Hole {holes}\n'
                f'SI   {SI}\n'
                f'Par  {pars}')

    @property
    def name(self):
        return f'{self.course_name} ({self.tee_name})'

    @property
    def allowancepc(self):
        return f'{self.allowance * 100:.0f}%'

    def hcap(self, exact):
        return int(round(exact * self.slope_rating / BASE * self.allowance))


    def to_dict(self):
        return self.__dict__


class Player:
    def __init__(self, name, initials, HI, round=None):  # round is ignored
        if name in('Nick Radcliffe', 'Andy McGlone', 'Kenny Sargent'):
            name = name.split(' ')[0]
        self.name = name
        self.initials = initials
        self.HI = HI

    def __str__(self):
        return f'{self.name} ({self.initials}):  HI {self.HI:.1f}'


    def summary(self, tee):
        return (str(self) + f'  Playing handicap @ {tee.allowancepc} '
                            f'({tee.name}): '
                            f'{tee.hcap(self.HI)}')

    def handicap(self, tee):
        return tee.hcap(self.HI)


class Hole:
    """
    NOTE: All lists have hole 1 as the first entry, i.e. hole n is at position (n - 1)

    Attributes:
        player:             The player
        tee:                Tee object, describing the course from a named set of tees (e.g. White)

        hole_number:        The number of the hole, 1-18
        par:                Par of the hole
        si:                 Stroke index of the hole
        strokes:            Number of strokes the player gets on this hole

        *: Items below marked * can be None, indicating a No Return (or possibly DNP)

        gross:*             Strokes taken on the hole
        nett:*              Net score on the hole (gross - strokes)
        adj:                Adjusted score after throwing away strokes over gross double bogey
        adj_nett:           Adjusted nett score after throwing away strokes over nett double bogey
        nett_stableford:    Stableford points (handicapped)
        gross_stableford:   Stableford points (gross, i.e. unhandicapped)
        gross_diff:*        Strokes over gross par (negative for birdies etc.)
        net_diff:*          Strokes over net par (negative for nett birdies etc.)
        adj_nett_diff:      Adjusted strokes over net par (2 if net diff is None)

        gross_bogey:        1 for birdies and better, 0 for par, -1 for bogeys and worse
        nett_bogey:         1 for nett birdies and better, 0 for nett par, -1 for nett bogeys and worse

    """
    SAVE_KEYS = ('hole_number', 'gross', 'nett', 'adj', 'adj_nett',
                 'nett_stableford', 'gross_stableford', 'gross_desc',
                 'gross_stableford', 'gross_diff', 'nett_diff',
                 'adj_nett_diff')
    def __init__(self, hole_number, gross, tee, player):
        self.hole_number = hole_number
        self.set_score(gross, tee, player)

    def set_score(self, gross, tee, player):
        h = self.hole_number - 1
        self.gross = gross
        gross = gross or None
        self.par = par = tee.par[h]
        self.si = si = tee.SI[h]
        hcap = player.handicap(tee)
        every_hole_strokes = 2 if hcap >= 36 else 1 if hcap >= 18 else 0
        self.strokes = strokes = every_hole_strokes + (si <= hcap % 18)
        if gross == None:  # DNP
            nett = None
        else:
            nett = gross - strokes
        self.nett = nett
        self.adj = adj = min(nvl(gross, 10), par + strokes + 2)
        self.adj_nett = adj - strokes
        if gross is None:
            self.nett_stableford = self.gross_stableford = 0
            self.gross_desc = self.nett_desc = None
        else:
            gstab = self.gross_stableford = max(2 + (par - gross), 0)
            stab = self.nett_stableford = max(2 + (par - nett), 0)
            self.gross_desc = STABLEFORD_TO_DESC[gstab]
            self.nett_desc = STABLEFORD_TO_DESC[stab]
        self.gross_diff = (gross - par) if gross else None
        self.nett_diff = (nett - par) if nett else None
        self.adj_nett_diff = (self.adj_nett - par)
        self.gross_bogey = sign(par - nvl(self.gross, 10))
        self.nett_bogey = sign(par - nvl(self.nett, 10))

    def recalc(self, tee, player):
        self.set_score(self.gross, tee, player)

    @property
    def net_par(self):
        return self.par + self.strokes

    def __str__(self):
        h = self.hole_number - 1
        si = self.si
        return (f'Hole {self.hole_number:2d}  '
                f'Par {self.par}  SI {si:2d}  '
                f'Gross {nvf(self.gross)}  '
                f'Adj {nvf(self.adj)}  '
                f'Nett {nvf(self.nett)}  '
                f'Adj Nett {nvf(self.adj_nett)}  '
                f'{plural(self.nett_stableford, "point")}')

    def short(self):
        """Returns summary in form
            gross/nett for points
           e.g.
               5 net 4 for 2
        """
        return (f'{nvs(self.gross)} net {nvs(self.nett)} '
                f'for {self.nett_stableford}')


class Round:
#    SAVE_KEYS = ('holes',)
    def __init__(self, player, tee, date, scores=None):
        self.player = player
        self.tee = tee
        self.date = (date if isinstance(date, datetime.date)
                          else fromisoformat(date))
        if scores is None:
            scores = [None] * 18
        elif len(scores) < 18:
            scores = scores + ([None] * (18 - len(scores)))
        self.holes = [Hole(hole, score, tee, player)
                      for hole, score in enumerate(scores, 1)]


    def update(self, hole, gross):
        self.holes[hole - 1] = Hole(hole, gross, self.tee, player)

    def holes_str(self):
        return '\n'.join(str(hole) for hole in self.holes)

    def holes_slice(self, starthole, n):
        return self.holes[starthole - 1:starthole -1 + n]

    def combined_gross(self, starthole, n, null_to_zero=False,
                       null_to_adj=False):
        grosses = [(hole.gross or None)
                   for hole in self.holes_slice(starthole, n)]
        if null_to_zero:
            return sum(g or 0 for g in grosses)
        elif null_to_adj and any(g is None for g in grosses):
            adjs = [hole.adj for hole in self.holes_slice(starthole, n)]
            grosses = [nvl(g, a) for (g, a) in zip(grosses, adjs)]
        return None if any(g is None for g in grosses) else sum(grosses)

    def combined_nett(self, starthole, n, null_to_zero=False,
                      null_to_adj=False):
        netts = [hole.nett  for hole in self.holes_slice(starthole, n)]
        if null_to_zero:
            return sum(n or 0 for n in grosses)
        elif null_to_adj and any(n is None for n in netts):
            adjs = [hole.adj_nett for hole in self.holes_slice(starthole, n)]
            netts = [nvl(n, a) for (n, a) in zip(netts, adjs)]
        return None if any(nett is None for nett in netts) else sum(netts)

    def combined_adj(self, starthole, n):
        adjusted = [hole.adj for hole in self.holes_slice(starthole, n)]
        return None if any(a is None for a in adjusted) else sum(adjusted)

    def combined_adj_nett(self, starthole, n):
        adjusted = [hole.adj_nett for hole in self.holes_slice(starthole, n)]
        return None if any(a is None for a in adjusted) else sum(adjusted)

    def combined_adj_nett_diff(self, starthole, n):
        return sum(hole.adj_nett_diff
                   for hole in self.holes_slice(starthole, n))

    def combined_nett_stableford(self, starthole, n):
        stabs = [hole.nett_stableford
                 for hole in self.holes_slice(starthole, n)]
        return sum(stabs)

    def combined_gross_stableford(self, starthole, n):
        stabs = [hole.gross_stableford
                 for hole in self.holes_slice(starthole, n)]
        return sum(stabs)

    def combined_gross_bogey(self, starthole, n):
        bogeys = [hole.gross_bogey
                 for hole in self.holes_slice(starthole, n)]
        return sum(bogeys)

    def combined_nett_bogey(self, starthole, n):
        bogeys = [hole.nett_bogey
                 for hole in self.holes_slice(starthole, n)]
        return sum(bogeys)

    def combined_str(self, first_hole, n, prefix=''):
        gross = self.combined_gross(first_hole, n, null_to_zero=True)
        nett = self.combined_nett(first_hole, n)
        adj = self.combined_adj(first_hole, n)
        adj_nett = self.combined_adj_nett(first_hole, n)
        stab = self.combined_nett_stableford(first_hole, n)
        start = f'{prefix}: ' if prefix else ''
        return (f'{start} Gross {nvf(gross)}  '
                f'Adj {nvf(adj)}  '
                f'Nett {nvf(nett)}  '
                f'Adj Nett {nvf(adj_nett)}  '
                f'Stab {nvf(stab)}')

    def __str__(self):
        return self.holes_str()

    def summary(self, holes=True, nines=True, sixes=True, scores=True,
                tight=False):

        out = []
        if holes:
            out.append(str(self))

        out.append(self.combined_str(1, 18,
                   f' {self.player.initials:>3} ROUND'))

        if nines:
            front = self.combined_str(1, 9,  'Front nine')
            back = self.combined_str(10, 9, ' Back nine')
            out.append(f'{front}\n{back}')

        if sixes:
            first = self.combined_str(1, 6,  ' Front six')
            middle = self.combined_str(7, 6,  'Middle six')
            last = self.combined_str(12, 6, '  Last six')
            out.append(f'{first}\n{middle}\n{last}')

        if scores:
            holes1 = ' '.join(f'{h:2d}' for h in range(1,10)) + ' OUT'
            scores1 = (' '.join(f'{nvf(h.gross)}' for h in self.holes[:9])
                       + nvf(self.combined_gross(1, 9, null_to_zero=True),
                             width=4))
            holes2 = ' '.join(f'{h:2d}' for h in range(10,19)) + '  IN TOT'
            scores2 = (' '.join(f'{nvf(h.gross)}' for h in self.holes[9:])
                       + nvf(self.combined_gross(10, 9, null_to_zero=True),
                             width=4)
                       + nvf(self.combined_gross(1, 18, null_to_zero=True),
                             width=4))
            out.append('\n'.join((holes1, scores1, holes2, scores2)))
        joint = '\n' if tight else '\n\n'
        return joint.join(out)

    def post_hole_summary(self, hole):
        sford1 = self.combined_nett_stableford(1, min(hole, 6))
        sford2 = (self.combined_nett_stableford(7, min(hole - 6, 6))
                  if hole > 6 else 0)
        sford3 = (self.combined_nett_stableford(13, min(hole - 12, 6))
                    if hole > 12 else 0)
        sford = sford1 + sford2 + sford3
        to_hcap = self.combined_adj_nett_diff(1, hole)
        sgn = '+' if to_hcap > 0 else ''
        return f'{sford1} + {sford2} + {sford3} = {sford} ({sgn}{to_hcap})'

    def to_dict2(self):
        return {
            k: odict(v)
        }

    def to_dict(self):
        keys = ('gross', 'nett', 'adj', 'adj_nett',
                'nett_stableford', 'gross_stableford',
                'gross_stableford')
        return {
            k: [getattr(h, k) for h in self.holes]
            for k in keys
        }

    def score_list(self):
        """Returns scores as a list"""
        return [h.gross for h in self.holes]

    def string_scores_list(self):
        """Returns scores as a list"""
        return [fmt_csv(h.gross) for h in self.holes]

    def nett_points_list(self):
        """Returns net stableford points as a list"""
        return [h.nett_stableford for h in self.holes]


def fmt_csv(v):
    return '' if v is None else str(v)


def nvl(v, default):
    return default if v is None else v


def nvf(v, null='-', zero='-', width=2):
    fmt = '%%%dd' % width
    return ((' ' * (width - 1) + null) if v is None
            else (' ' * (width - 1) + zero) if v == 0
            else (fmt % v))


def nvs(v):
    return nvf(v, width=1)


def plural(n, word):
    return f'{n} {word}{"" if n == 1 else "s"}'


def fromisoformat(datestr):
    m = re.match(DATE_RE, datestr)
    return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))


def flatten(v):
    if v is None or type(v) in (bool, int, float, str, datetime.datetime):
        return v
    elif type(v) in (tuple, list):
        return [flatten(w) for w in v]
    elif isinstance(v,  dict):
        return {flatten(key): flatten(value)
                for key, value in v.items()}
    elif hasattr(v, '__dict__') and hasattr(v, '__class__'):
        keys = getattr(v, 'SAVE_KEYS', v.__dict__.keys())
        return {flatten(key): flatten(getattr(v, key))
                for key in keys}
    else:
        return str(v)


def sign(v):
    return 1 if v > 0 else -1 if v < 0 else 0
