import datetime
import json
import os
import re
import sys

from collections import namedtuple

if sys.platform == 'ios':
    from fixpath import fixpath
    fixpath(__file__)

from artists.giacometti.csn import CSReal, CSInt, CSVal
from artists.giacometti.table import Table, Cell

if sys.platform == 'ios':
    from courses import Courses
    from live import LiveRound
    from round import fromisoformat
    from config import (
        TRACKER_DIR,
        ROUND_DATA_DIR,
        INDEX_TEMPLATE_PATH,
        INDEX_PATH,
    )
    from players import KnownPlayers

from golf.live.courses import Courses
from golf.live.live import LiveRound
from golf.live.round import fromisoformat
from golf.live.config import (
    TRACKER_DIR,
    ROUND_DATA_DIR,
    INDEX_TEMPLATE_PATH,
    INDEX_PATH,
)
from golf.live.players import KnownPlayers

RE = r'^(\d{4}-\d{2}-\d{2})\.json$'


START_OF_RACE_STR = '2023-04-01'

BASE_SLOPE = 113
POUNDS = '£'
#POUNDS = '￡'
NBSP = chr(0xA0)

GROUP_HEADERS = (
    'GROSS SCORE',
    'NETT SCORE',
    'STABLEFORD POINTS',
    'GROSS STABLEFORD',
)

BOGEY_GROUP_HEADERS = (
    'GROSS SCORE',
    'NETT SCORE',
    'BOGEY POINTS',
    'GROSS BOGEY',
)

RESULT = {
    None: 'blob',
    0: 'doublebogey',
    1: 'bogey',
    2: 'par',
    3: 'birdie',
    4: 'eagle',
    5: 'albatros'
}

BOGEY_RESULT = {
    -1: 'bogey',
    0: 'par',
    1: 'birdie',
}


BLUE = '#4169E1'
RED = 'red'


RESULT_CSS_MAP = {
     'doublebogey': {'background-color': '#FF8A7C'},  # red
     'bogey': {'background-color': '#FFE2DE'},        # pink
     'par': {'background-color': '#FFFFFF'},          # white
     'birdie': {'background-color': '#CAE5FF'},       # pale blue
     'eagle': {'background-color': '#5AB2FF'},  # dark blue
     'albatros': {'background-color': '#0000A0'},     # bright red
}

SHAPE_RESULT_CSS_MAP1 = {
     'doublebogey span': {
        'border': f'2px {RED} solid',
        'padding': '0 0.25em 0 0.25em',
        'background-color': RED,
        'color': 'white',
     },
     'bogey span': {
        'border': f'2px {RED} solid',
        'padding': '0 0.25em 0 0.25em',
     },
     'par span': {
        'background-color': '#FFFFFF',
     },
     'birdie span': {
        'border': f'2px {BLUE} solid',
        'padding': '0 0.25em 0 0.25em',
        'border-radius': '10px',
     },
     'eagle span': {
        'border': f'2px {BLUE} solid',
        'padding': '0 0.25em 0 0.25em',
        'border-radius': '12px',
        'background-color': BLUE,
        'color': 'white',
     },
     'albatros span': {
        'border': '2px blue solid',
        'padding': '0 0.25em 0 0.25em',
        'border-radius': '10px',
     },
}


Sixes = namedtuple('Sixes', 'front middle back overall')
RaceStatus = namedtuple('RaceStatus',
                        'date player game played staked won profit')


class ROW:
    DATE = 1
    GAME = 1
    GROUP_HEADER = 1
    MAIN_HEADER = 2
    EXACT = 3
    HANDICAP = 4
    HOLE1 = 5
    FRONT9_SUMMARY = HOLE1 + 9
    BACK9_SUMMARY = HOLE1 + 19
    TOTAL = BACK9_SUMMARY + 1
    ADJUSTED = TOTAL + 1
    DIFFERENTIAL = ADJUSTED + 1
    COMPETITION = DIFFERENTIAL + 2

    SIX_1_6 = COMPETITION + 1
    SIX_7_12 = SIX_1_6 + 1
    SIX_13_18 = SIX_7_12 + 1
    SIX_OVERALL = SIX_13_18 + 1
    SIX_TOTAL = SIX_OVERALL + 1
    SIX_STAKED = SIX_TOTAL + 1
    SIX_NET = SIX_STAKED + 1

    EAGLES = SIX_NET + 4
    BIRDIES = EAGLES + 1
    PARS = BIRDIES + 1
    BOGEYS = PARS + 1
    DOUBLES = BOGEYS + 1

    RTG = EAGLES - 1


ANALYSIS_NAMES = [
    'Doubles & worse',
    'Bogeys',
    'Pars',
    'Birdies',
    'Eagles & better',
]


class COL:
    HOLE = 0
    GROSS = 1
    NETT = 2
    STABLEFORD = 3
    GROSS_STABLEFORD = 4
    HOLE_NAME = 5

    P1S = ('GROSS',
           'NETT',
           'STABLEFORD',
           'GROSS_STABLEFORD')


class C:
    YEAR = 2023
#    STAKE = 5.0


def num_formatter(v):
    return CSVal(v, null='⚫️')  # ●
num_fmt = num_formatter


NameCell = lambda v, **kw: Cell(v, header=1, styles=['name'])
BCell = lambda v, **kw: Cell(v, styles=['b'], **kw)
SICell = lambda v, **kw: Cell(v, styles=['si'] + pad(v), **kw)

NumCell = lambda s, **kw: Cell(s, styles=pad(s), formatter=num_fmt, **kw)
BNumCell = lambda s, **kw: Cell(s, styles=['b'] + pad(s), **kw)
PlainScoreCell = lambda s, r, b, **kw: Cell(s, styles=[result(r, b)] + pad(s),
                                         formatter=num_fmt,
                                         **kw)
ShapeScoreCell = lambda s, r, b, **kw: Cell(s, styles=[result(r, b)] + pad(s),
                                         formatter=num_fmt, shape=True, **kw)
TotScoreCell = lambda s, **kw: Cell(s, styles=pad(s), formatter=num_fmt,
                                    header=1, **kw)
BTotScoreCell = lambda s, **kw: Cell(s, styles=pad(s),
                                     formatted=CSReal(s, prefix='[', suffix=']',
                                                      dps=0),
                                     header=1, **kw)
WinningTotScoreCell = lambda s, **kw: Cell(s, styles=pad(s) + ['W'],
                                           header=1, **kw)
WinningScoreCell = lambda s, **kw: Cell(s, styles=pad(s) + ['W'], **kw)
TopHeaderCell = lambda s, **kw: Cell(s, styles=['tophead'], header=1, **kw)




class Tracker:
    def __init__(self, theround, race, shapes=True):
        self.theround = theround
        self.race = race
        self.course = theround.course
        self.n_players = len(theround.players)
        self.n_racers = self.count_racers()
        self.shapes = shapes
        self.any_holes = bool(self.course.names)
        self.n_cols = self.col('HOLE_NAME', 1) - (0 if self.any_holes else 2)
        self.table = Table(n_rows=45, n_cols=self.n_cols)
        self.pcc = getattr(theround, 'pcc', 0)
        self.stake = self.theround.sixes[0] * 3 + self.theround.sixes[1]

        self.set_heading_and_rtg()
        self.add_top_header()
        self.add_date()
        self.add_course()
        self.add_handicaps()
        self.add_group_headers()
        self.add_player_info()
        self.calculate_match_results()
        self.add_scores()
        self.add_comp_headers()
        self.add_money()

        self.add_analysis()
        self.add_race()
        self.add_css()

    def count_racers(self):
        return sum(p in ('NJR', 'KS', 'AM') for p in self.theround.players)

    def add_css(self):
        table = self.table
        table.cell_styles['si'] = {'color': 'red', 'font-weight': 'bold'}
        table.cell_styles['p2'] = {'padding-right': '0.7em'}
        table.cell_styles['p3'] = {'padding-right': '1.4em'}
        table.cell_styles['W'] = {'border': f'2px {BLUE} solid'}
        table.cell_styles['neg'] = {'color': 'red'}
        table.cell_styles['name'] = {'min-width': '3.5em'}
        css_map = SHAPE_RESULT_CSS_MAP1 if self.shapes else RESULT_CSS_MAP
        table.cell_styles.update(css_map)
        table.css_map['body'] = {
            'font-family': 'Helvetica Neue, Helvetica, Arial, Sans'
        }
        table.css_map['td, th'] = {
            'text-align': 'center',
            'border': '1px solid #A6A6A6',
            'padding': '4px',
        }
        table.css_map['td.tophead, th.tophead'] = {
            'text-align': 'center',
            'border': 'none',
            'padding': '4px',
        }

    def set_heading_and_rtg(self):
        heading = self.theround.desc
        if not heading:
            if self.course.allowance < 1:
                kind = 'Bogey Medal' if self.theround.bogey else 'Medal'
            else:
                kind = 'Bounce Game'
            heading = f'{kind} @ {self.course.name}'
            self.theround.desc = heading
        self.rtg = 1 if (
                        'Bounce' in self.theround.desc
                        or 'Medal' in self.theround.desc
                        or 'Spoon' in self.theround.desc
                   ) else 0

    def add_top_header(self):
        self.table[0][0] = TopHeaderCell(self.theround.desc,
                                         colspan=self.table.n_cols)

    def add_date(self):
        d = self.theround.date
        self.table[1][0] = BCell(d.strftime('%d/%m/%Y'))

    def add_handicaps(self):
        players = self.theround.players
        course = self.course
        n = self.n_players
        self.table[ROW.EXACT][0] = BCell('Exact HI')
        self.table[ROW.HANDICAP][0] = BCell('Handicap')
        fmtd = CSReal(course.allowance, pc=True, dps=0)
        self.table[ROW.HANDICAP][1] = Cell(course.allowance, fmtd, colspan=2)

        for i, p in enumerate(players.values()):
            c = self.col('GROSS')
            self.table[ROW.EXACT][c + i] = Cell(p.HI, CSReal(p.HI, dps=1))
            hcap = course.hcap(p.HI)
            self.table[ROW.HANDICAP][c + i] = BCell(hcap)

    def add_course(self):
        table = self.table
        course = self.course

        table[ROW.MAIN_HEADER][COL.HOLE:COL.HOLE+3] = [
            Cell(f'GAME #{self.game}', header=1),
            Cell('SI', header=1, styles=['si']),
            Cell('Par', header=1),
        ]

        for h in range(1, 10):
            table[hole_row(h)][COL.HOLE:COL.HOLE+3] = [
                BCell(h),
                SICell(course.SI[h - 1]),
                course.par[h - 1]
            ]
        table[ROW.FRONT9_SUMMARY][COL.HOLE:COL.HOLE+3] = [
            BCell('OUT'),
            '',
            BNumCell(sum(course.par[:9]))
        ]
        for h in range(9, 19):
            table[hole_row(h)][COL.HOLE:COL.HOLE+3] = [
                BCell(h),
                SICell(course.SI[h - 1]),
                course.par[h - 1]
            ]

        table[ROW.BACK9_SUMMARY][COL.HOLE:COL.HOLE+3] = [
            BCell('IN'),
            '',
            BNumCell(sum(course.par[9:])),
        ]
        table[ROW.TOTAL][COL.HOLE:COL.HOLE+3] = [
            BCell('TOTAL'),
            '',
            BNumCell(sum(course.par)),
        ]
        table[ROW.ADJUSTED][COL.HOLE] = BCell('ADJUSTED')
        table[ROW.DIFFERENTIAL][COL.HOLE] = BCell('DIFFERENTIAL')
        cr = CSReal(self.course.course_rating, dps=1)
        table[ROW.DATE][1] = Cell(f'CR\n{cr}')
        sr = CSInt(self.course.slope_rating)
        table[ROW.DATE][2] = Cell(f'SLOPE\n{sr}')

        if self.any_holes:
            for i, name in enumerate(self.course.names, 1):
                row = ROW.HOLE1 + i - (i < 10)
                table[row][self.n_cols - 1] = BCell(name)

    def add_group_headers(self):
        headers = BOGEY_GROUP_HEADERS if self.theround.bogey else GROUP_HEADERS
        for c, head in zip(COL.P1S, headers):
            col = self.col(c)
            self.table[ROW.GROUP_HEADER][col] = Cell(head,
                                                     colspan=self.n_players,
                                                     header=1,
                                                     styles=['c'])

    def add_player_info(self):
        players = self.theround.players
        n = self.n_players
        for c in COL.P1S:
            col = self.col(c)
            self.table[ROW.MAIN_HEADER][col:col + n] = [
                NameCell(p.name)
                for p in players.values()
            ]

    def add_scores(self):
        table = self.table
        ScoreCell = ShapeScoreCell if self.shapes else PlainScoreCell
        for i, r in enumerate(self.theround.rounds_list):
            if self.theround.bogey:
                nett_results = [r.holes[n - 1].nett_bogey
                                for n in range(1, 19)]
                gross_results = [r.holes[n - 1].gross_bogey
                                 for n in range(1, 19)]
            else:
                nett_results = [r.holes[n - 1].nett_stableford
                                for n in range(1, 19)]
                gross_results = [r.holes[n - 1].gross_stableford
                                 for n in range(1, 19)]
            for n in range(1, 19):
                table[hole_row(n)][self.col('GROSS', i)] = ScoreCell(
                    r.holes[n - 1].gross or None,
                    blobify(gross_results[n - 1], r.holes[n - 1].gross),
                    self.theround.bogey
                )
                table[hole_row(n)][self.col('NETT', i)] = ScoreCell(
                    r.holes[n - 1].nett,
                    blobify(nett_results[n - 1], r.holes[n - 1].nett),
                    self.theround.bogey
                )
                a = 'nett_bogey' if self.theround.bogey else 'nett_stableford'
                table[hole_row(n)][self.col('STABLEFORD', i)] = ScoreCell(
                    getattr(r.holes[n - 1], a),
                    nett_results[n - 1],
                    self.theround.bogey
                )
                col = self.col('GROSS_STABLEFORD', i)
                a = 'gross_bogey' if self.theround.bogey else 'gross_stableford'
                table[hole_row(n)][col] = ScoreCell(
                    getattr(r.holes[n - 1], a),
                    gross_results[n - 1],
                    self.theround.bogey
                )
            rows = (ROW.FRONT9_SUMMARY, ROW.BACK9_SUMMARY, ROW.TOTAL)
            tots = (
                r.combined_gross(1, 9, null_to_adj=True),
                r.combined_gross(10, 9, null_to_adj=True),
                r.combined_gross(1, 18, null_to_adj=True),
            )
            ntots = (
                r.combined_gross(1, 9),
                r.combined_gross(10, 9),
                r.combined_gross(1, 18),
            )
            for (row, tot, ntot) in (zip(rows, tots, ntots)):
                TheCell = BTotScoreCell if ntot is None else TotScoreCell
                table[row][self.col('GROSS', i)] = TheCell(tot)
            tots = (
                r.combined_nett(1, 9, null_to_adj=True),
                r.combined_nett(10, 9, null_to_adj=True),
                r.combined_nett(1, 18, null_to_adj=True),
            )
            ntots = (
                r.combined_nett(1, 9),
                r.combined_nett(10, 9),
                r.combined_nett(1, 18),
            )
            for (row, tot, ntot) in (zip(rows, tots, ntots)):
                TheCell = BTotScoreCell if ntot is None else TotScoreCell
                table[row][self.col('NETT', i)] = TheCell(tot)

            f = (r.combined_nett_bogey if self.theround.bogey
                                       else r.combined_nett_stableford)
            tots = (
                f(1, 9),
                f(10, 9),
                f(1, 18),
            )
            for (row, tot) in (zip(rows, tots)):
                table[row][self.col('STABLEFORD', i)] = TotScoreCell(tot)

            f = (r.combined_gross_bogey if self.theround.bogey
                                        else r.combined_gross_stableford)
            tots = (
                f(1, 9),
                f(10, 9),
                f(1, 18),
            )
            for (row, tot) in (zip(rows, tots)):
                table[row][self.col('GROSS_STABLEFORD', i)] = TotScoreCell(tot)

            # SIXES (STABLEFORD)
            rows = (ROW.SIX_1_6, ROW.SIX_7_12, ROW.SIX_13_18)
            sixes = ('front', 'middle', 'back')
            for j, (row, six) in enumerate((zip(rows, sixes))):
                tot = getattr(self.six_totals[i], six)
                winner = getattr(self.is_six_winner[i], six)
                TheCell = WinningScoreCell if winner else NumCell
                table[row][self.col('STABLEFORD', i)] = TheCell(tot)
            tot = self.six_totals[i].overall
            winner = self.is_six_winner[i].overall
            TheCell = WinningTotScoreCell if winner else TotScoreCell
            table[ROW.SIX_OVERALL][self.col('STABLEFORD', i)] = TheCell(tot)


            adj = r.combined_adj(1, 18)
            table[ROW.ADJUSTED][self.col('GROSS', i)] = TotScoreCell(adj)

            net_adj = r.combined_adj_nett(1, 18)
            table[ROW.ADJUSTED][self.col('NETT', i)] = TotScoreCell(net_adj)

            diff = self.differential(adj)
            fmtd = CSReal(diff, dps=1)
            table[ROW.DIFFERENTIAL][self.col('GROSS', i)] = Cell(diff, fmtd)

    def calculate_match_results(self):
        """
        Calculates the match results:

            self.six_totals:
                gets one row per player, with that players
                scores for the front, middle and back six and for the match

            self.six_winning_scores:
                gets the winning number of points in for each of
                the front, middle and back six and for the match

            self.n_winners:
                gets the winning players in for each six among
                front, middle and back six and overall.

        """
        if self.theround.bogey:
            self.six_totals = [
                # one  row per player withb
                # front, middle, back, overall total
                Sixes(
                    r.combined_nett_bogey(1, 6),
                    r.combined_nett_bogey(7, 6),
                    r.combined_nett_bogey(13, 6),
                    r.combined_nett_bogey(1, 18),
                )
                for r in self.theround.rounds_list
            ]
        else:
            self.six_totals = [
                # one  row per player withb
                # front, middle, back, overall total
                Sixes(
                    r.combined_nett_stableford(1, 6),
                    r.combined_nett_stableford(7, 6),
                    r.combined_nett_stableford(13, 6),
                    r.combined_nett_stableford(1, 18),
                )
                for r in self.theround.rounds_list
            ]

        self.six_winning_scores = Sixes(
            # winning score for each six and overall
            *(max(score[i] for score in self.six_totals)
              for i in range(4)))
        self.is_six_winner = [
            Sixes(*(scores[i] == self.six_winning_scores[i]
                  for i in range(4)))
            for scores in self.six_totals
        ]
        self.n_winners = Sixes(*(sum(winner[i]
                                     for winner in self.is_six_winner)
                                 for i in range(4)))


    def add_comp_headers(self):
        table = self.table
        hole_col = self.col('HOLE')
        six_col = self.col('STABLEFORD') - 2
        table[ROW.COMPETITION - 1][0] = TopHeaderCell(NBSP,
                                                      colspan=self.n_cols)
        table[ROW.COMPETITION][hole_col] = BCell('COMPETITION')
        table[ROW.COMPETITION][six_col] = BCell('SIXES')
        table[ROW.COMPETITION+1][hole_col] = BCell('1–6')
        table[ROW.COMPETITION+1][six_col] = BCell('1–6')
        table[ROW.COMPETITION+2][hole_col] = BCell('7–12')
        table[ROW.COMPETITION+2][six_col] = BCell('7–12')
        table[ROW.COMPETITION+3][hole_col] = BCell('13–18')
        table[ROW.COMPETITION+3][six_col] = BCell('13–18')
        table[ROW.COMPETITION+4][hole_col] = BCell('OVERALL')
        table[ROW.COMPETITION+4][six_col] = BCell('1–18')
        for i, p in enumerate(self.theround.players.values()):
            table[ROW.COMPETITION][self.col('GROSS', i)] = NameCell(p.name)
            table[ROW.COMPETITION][self.col('STABLEFORD', i)] = NameCell(p.name)
        table[ROW.COMPETITION+5][hole_col] = BCell('TOTAL')
        table[ROW.COMPETITION+6][hole_col] = BCell('STAKED')
        table[ROW.COMPETITION+7][hole_col] = BCell('NET')
        table[ROW.COMPETITION+8][hole_col] = BCell('RACE WEIGHT')
        table[ROW.COMPETITION+8][hole_col + 1] = Cell(self.rtg)

    def add_money(self):
        table = self.table
        self.winnings = {}
        for i, p in enumerate(self.theround.players):
            # SIXES (STABLEFORD)
            rows = (ROW.SIX_1_6, ROW.SIX_7_12, ROW.SIX_13_18, ROW.SIX_OVERALL)
            sixes = ('front', 'middle', 'back', 'overall')
            col = self.col('GROSS', i)
            for j, (row, six) in enumerate((zip(rows, sixes))):
                winner = getattr(self.is_six_winner[i], six)
                money = (self.n_players
                         * winner / getattr(self.n_winners, six)
                         * self.theround.sixes[1 if six == 'overall' else 0]
                         * (self.rtg if self.rtg else 1))
                fmtd = CSReal(money, prefix=POUNDS) if money else ''
                table[row][col] = Cell(money, fmtd, styles=['b'])
            tot = self.six_totals[i].overall
            winner = self.is_six_winner[i].overall
            TheCell = WinningTotScoreCell if winner else TotScoreCell
            table[ROW.SIX_OVERALL][self.col('STABLEFORD', i)] = TheCell(tot)
            money = sum(table[row][col].value for row in rows)
            self.winnings[p] = money
            fmtd = CSReal(money, prefix=POUNDS)
            table[ROW.SIX_TOTAL][col] = BCell(money, formatted=fmtd)
            fmtd = CSReal(self.stake, prefix=POUNDS)
            table[ROW.SIX_STAKED][col] = Cell(self.stake, formatted=fmtd)
            net = money - self.stake
            fmtd = CSReal(net, prefix=POUNDS, long_minus=True)
            styles = ['b'] + (['neg'] if net < 0 else [])
            table[ROW.SIX_NET][col] = Cell(net, formatted=fmtd, styles=styles)

    def add_analysis(self):
        table = self.table
        table[ROW.RTG - 1][0] = TopHeaderCell(NBSP, colspan=self.n_cols)
        col = self.col('NETT')
        table[ROW.RTG][col] = TopHeaderCell('ANALYSIS', colspan=self.n_players)
        for i, r in enumerate(self.theround.rounds_list):
            for points in range(0, 5):
                if points == 4:
                    net = sum(hole.nett_stableford >= points
                              for hole in r.holes)
                    gross = sum(hole.gross_stableford >= points
                                for hole in r.holes)
                else:
                    net = sum(hole.nett_stableford == points
                              for hole in r.holes)
                    gross = sum(hole.gross_stableford == points
                                for hole in r.holes)
                row = ROW.DOUBLES - points
                table[row][self.col('STABLEFORD', i)] = Cell(net)
                table[row][self.col('GROSS_STABLEFORD', i)] = Cell(gross)
                if i == 0:
                    cat = ANALYSIS_NAMES[points]
                    table[row][self.col('NETT')] = BCell(cat, colspan=3)
        row = ROW.EAGLES - 1
        table[row][self.col('STABLEFORD')] = BCell('NET',
                                                   colspan=self.n_players)
        table[row][self.col('GROSS_STABLEFORD')] = BCell('GROSS',
                                                         colspan=self.n_players)

    def add_race(self):
        if self.n_racers < 2:
            return
        table = self.table
        short = 1 if (self.n_players < 3) else 0
        table[ROW.RTG][0] = Cell(f'RACE TO GULLANE {C.YEAR}', header=1,
                                 colspan=7 - short * 2)
        table[ROW.RTG + 2][0] = Cell(f'Played', header=1, styles=['l'])
        table[ROW.RTG + 3][0] = Cell(f'Staked', header=1, styles=['l'])
        table[ROW.RTG + 4][0] = Cell(f'Won', header=1, styles=['l'])
        table[ROW.RTG + 5][0] = Cell(f'Profit', header=1, styles=['l'])

        date = self.theround.date
        for i, initials in enumerate(['NJR', 'AM', 'KS']):
            p = KnownPlayers[initials]
            col = self.col('GROSS', i) - short
            table[ROW.RTG + 1][col] = NameCell(p.name)
            status = self.get_prev_race_status(initials)
            rp = self.theround.players.get(initials, None)
            rtg = self.rtg
            if rp is None or rtg == 0:  # This player not playing in this
                new_status = status          # round, or not a counter
            else:
                new_status = RaceStatus(date, initials, self.game,
                                        status.played + 1,
                                        status.staked + self.stake * rtg,
                                        status.won
                                        + self.winnings[initials],
                                        status.profit + self.winnings[initials]
                                        - self.stake * rtg)
            s = new_status
            table[ROW.RTG + 2][col] = BCell(s.played)
            fmtd = CSReal(s.staked, prefix=POUNDS, long_minus=True)
            styles = ['b', 'r']
            table[ROW.RTG+3][col] = Cell(s.staked, formatted=fmtd,
                                         styles=styles)
            fmtd = CSReal(s.won, prefix=POUNDS, long_minus=True)
            styles = ['b', 'r']
            table[ROW.RTG+4][col] = Cell(s.won, formatted=fmtd, styles=styles)
            fmtd = CSReal(s.profit, prefix=POUNDS, long_minus=True)
            styles = ['b', 'r'] + (['neg'] if s.profit < 0 else [])
            table[ROW.RTG+5][col] = Cell(s.profit, formatted=fmtd,
                                         styles=styles)
            if new_status is not status and new_status.date:
                self.race.append(new_status)

    @property
    def game(self):
        if self.race:
            r = self.race[-1]
            return r.game + (r.date < self.theround.date)
        else:
            return 1

    def differential(self, adj):
        r = self.theround
        c = self.course
        slope = c.slope_rating / BASE_SLOPE
        diff = (adj - c.course_rating - self.pcc) / slope
        if 0:
            print(f'>>> adj: {adj}  '
                  f'cr {c.course_rating}  '
                  f'pcc: {self.pcc}  '
                  f'slope: {slope}  '
                  f'diff: {diff}')
        return diff

    def col(self, kind, i=0):
        return (self.n_players + 1) * getattr(COL, kind) + i

    def get_prev_race_status(self, player):
        for row in reversed(self.race):
            if row.player == player and row.date < self.theround.date:
                return row
        else:
            return RaceStatus(None, player, 0, 0, 0.0, 0.0, 0.0)



def hole_row(hole):
    return ROW.HOLE1 + hole - (1 if hole < 10 else 0)


def result(stab, bogey=False):
    return BOGEY_RESULT[stab] if bogey else RESULT[stab] 


def pad(s):
    L = len(str(s))
    if L == 1:
        return []
    else:
        return [f'p{L}']


def blobify(fmt, score):
    return fmt if score else None


def round_link(datestr):
    return f'''     <tr><td colspan="4" class="c">
<a href="Tracker-{datestr}.html">Tracker {datestr}</a></td></tr>'''


def write_index(dates):
    with open(INDEX_TEMPLATE_PATH) as f:
        template = f.read().replace('%;', '%%;')
    rounds = '\n'.join(round_link(d) for d in dates)
    with open(INDEX_PATH, 'w') as f:
        f.write(template % locals())  # uses rounds
    print('index.html', INDEX_PATH)



def update_tracker(**kwargs):
    race = [
    ]
    files = os.listdir(ROUND_DATA_DIR)
    if not os.path.isdir(TRACKER_DIR):
        os.makedirs(TRACKER_DIR)
        print(f'Created {TRACKER_DIR}.')
    round_files = [f for f in sorted(files) if re.match(RE, f)]
    dates = [re.match(RE, f).group(1) for f in round_files]
    rounds = {
        date: f
        for f, date in sorted(zip(round_files, dates))
        if date >= START_OF_RACE_STR
    }

    for k, v in rounds.items():
        d = fromisoformat(k)
        theround = LiveRound(d, icloud=True)
        tracker = Tracker(theround, race)
        stem = 'Tracker' if tracker.n_racers > 1 else 'Round'
        outpath = os.path.join(TRACKER_DIR, f'{stem}-{k}.html')
        print(d, outpath)
        with open(outpath, 'w') as f:
            f.write(tracker.table.toHTML())
    dates = list(sorted({str(r.date) for r in race}))

    write_index(dates)


if __name__ == '__main__':
     update_tracker()
