from __future__ import division  # in case ever run with Python2

import os
import sys

from collections import defaultdict
from artists.miro.session import TestSession


DIR = '/Users/njr/iNJR/golf'
DEFAULT_SLOPE = 113
BROOMIEKNOWE_SLOPE = 122


class Handicaps:
    """
    Handicap calculations.

      - Base card uses the actual playing handicap as it was

      - "CONGU" handicaps are those counting every round and using
        the CONGU CONGU handicap rules (i.e. +.1 for outside buffer,
        and a multiplier of the amount under if under handicap).
        NOTE: CSS adjustments are being used for medals but not bounce games.

      - "WHS" handicaps are those adjusting handicaps based on
        the WHS handicapping system, i.e. the best 8 adjusted scores
        out of the last 20. Again, no adjustments for conditions.
    """
    def __init__(self, medals):
        self.session = TestSession()
        self.medals = medals
        prefix = 'medal' if medals else 'enhanced'
        self.session.Do(f'load golf/{prefix}scores')

        if not medals:
            self.session.Do('select (>= Date (date "2019-01-01"))')

        d = self.session.dataset
        nRows = d.nRecords

        rounds = defaultdict(list)
        player = None

        for i in d.SelectedIndexIterator():
            round = Round(d, i, d['Handicap'].PythonVal(i), 'actual')
            rounds[round.player].append(round)
            prounds = rounds[round.player]  # this player's rounds
            if len(prounds) > 1:
                round.roundCONGU = Round(d, i, prounds[-2].newHandicapCONGU,
                                        'CONGU')
            if len(prounds) > 20:
                round.roundWHS = Round(d, i, prounds[-2].newWHS.index,
                                        'WHS')
            round.newHandicapCONGU = (prev_handicapCONGU(rounds[round.player])
                                     + round.adjustment)
#            round.newHandicapWHS, counters = handicapWHS(rounds[round.player])
#            round.countersWHS = counters
            round.newWHS = handicapWHS(rounds[round.player])
#            round.countersWHS = counters
            if player != round.player:  # New player
                player = round.player
                print('**%s\n' % player)
            print(round)
        self.rounds = rounds

    def report(self, outpath):
        with open(outpath, 'w') as f:
            f.write(filecontents('handicaptemplateheader.tex'))

            for p, (player, rounds) in enumerate(self.rounds.items()):
                if p:
                    f.write('\\newpage\n')
                f.write('\\section*{%s: Handicap Analysis based on %s}\n'
                        % (player,
                           'medals' if self.medals else 'bounce games'))
                f.write(tableheader())
                for i in range(20, len(rounds) + 1):
                    if i % 10 == 0 and i != 20:
                        f.write(tablefooter())
                        f.write('\\newpage\n')
                        f.write(tableheader())
                    group = rounds[i - 20:i]
                    first_round = group[0]
                    last_round = group[-1]
                    first_date = first_round.date.strftime('%Y-%m-%d')
                    last_date = last_round.date.strftime('%Y-%m-%d')
                    dates = r'\dt{%s}{%s} &' % (first_date, last_date)
                    ctrs = last_round.newWHS.counters
                    cells = ' &\n'.join(r.latex(ctrs[i][1])
                                        for i, r in enumerate(group))
                    handicap = last_round.newWHS.index
                    bexact = last_round.newWHS.bexact
                    bhandicap = last_round.newWHS.broomieknowe
                    handicapcell = r'& \hcap{%s}' % handicap
                    becell = r'& \bcap{%s}' % bexact
                    bcell = r'& \bcap{%s} \\ \hline' % bhandicap
                    f.write('\n'.join((dates, cells, handicapcell,
                            becell, bcell, '')))
                f.write(tablefooter())

            f.write(filecontents('handicaptemplatefooter.tex'))
        print('Handicap analysis written to %s' % outpath)

    def save_handicaps(self, outpath):
        with open(outpath, 'w') as f:
            f.write('Date,Player,Description,OfficialHandicapOut,'
                    'Handicap2020Out\n')
            for player, player_rounds in self.rounds.items():
                N = len(player_rounds)
                for i, rd in enumerate(player_rounds):
                    f.write('%s,%s,"%s",%s,%s\n'
                            % (rd.date.strftime('%Y-%m-%d'),
                               player,
                               rd.kind,
                               ('%.1f' % player_rounds[i+1].exactHandicap)
                                    if i + 1 < N else '',
                               '%.1f' % rd.newWHS.index
                               if rd.newWHS.index is not None else ''))
        print(f'Handicap data written to {outpath}.')


def tableheader():
    return r'''\begin{tabular}{|r|c|c|c|c|c|c|c|c|c|c|c|c|c|c|c|c|c|c|c|c|c|c|c|}
   \hline
'''


def tablefooter():
    return '\\end{tabular}\n'


def filecontents(filename):
    with open(os.path.join(DIR, filename)) as f:
        return f.read()


def prev_handicapCONGU(rounds):
    """
    Gets the previous (adjusted) CONGU handicap from a list of rounds.
    If this is the first round, this is the input handicap for that round;
    otherwise it is the "newHandicapCONGU" for the penultimate round.
    """
    if len(rounds) == 1:
        return rounds[-1].exactHandicap
    else:
        return rounds[-2].newHandicapCONGU


def handicapWHS(rounds):
    if len(rounds) < 20:
        return WHSHandicap(None, None)
    scores = [score_to_css(r) for r in rounds[-20:]]
    bestScores = list(sorted(scores))[:8]
    maxScore = max(bestScores)
    countingScores = [[score, score <= maxScore] for score in scores]
    nCounters = sum(pair[1] for pair in countingScores)
    if nCounters > 8:
        for pair in countingScores:
            if pair[1] and pair[0] == maxScore:
                pair[1] = False
                nCounters -= 1
                if nCounters == 8:
                    break
    index = round(sum(bestScores) / 8 * DEFAULT_SLOPE / BROOMIEKNOWE_SLOPE, 1)
    return WHSHandicap(index, countingScores)


def score_to_css(r):
    if hasattr(r, 'roundWHS'):
        return r.roundWHS.scoreToCSS
    else:
        return r.scoreToCSS


def adjusted_total(r):
    if hasattr(r, 'roundWHS'):
        return r.roundWHS.adjustedTotal
    else:
        return r.adjustedTotal


class WHSHandicap:
    def __init__(self, index, counters):
        self.index = index
        self.counters = counters

    @property
    def broomieknowe(self):
        return intround(self.bexact)

    @property
    def bexact(self):
        return round(self.index * BROOMIEKNOWE_SLOPE / DEFAULT_SLOPE, 1)


def intround(v):
    if v - int(v) == 0.5:
        return int(v + 1)
    else:
        return int(round(v))



class Round:
    """Container for a Golf Round as a function of a given (exact) handicap"""
    def __init__(self, d, row, handicap, kind):
        self.exactHandicap = handicap
        assert kind in ('actual', 'CONGU', 'WHS')
        self.kind = kind
        self.playingHandicap = playing = round(handicap)
        self.player = d['Player'].PythonVal(row)
        self.tee = d['Tee'].PythonVal(row)
        self.date = d['Date'].PythonVal(row, datesAsDates=True)
        self.scores = [d['H' + str(i)].PythonVal(row) for i in range(1, 19)]
        self.pars = [d['Par' + str(i)].PythonVal(row) for i in range(1, 19)]
        self.si = [d['SI' + str(i)].PythonVal(row) for i in range(1, 19)]
        self.effectivePars = [self.pars[i]
                              + (1 if self.si[i] <= playing else 0)
                              + (1 if self.si[i] <= playing - 18 else 0)
                              for i in range(18)]
        self.adjScores = [(score if score is not None
                                    and score > 0
                                    and score <= ep + 2
                                 else ep + 2)
                          for (score, ep) in zip(self.scores,
                                                 self.effectivePars)]
        self.stablefords = [max(2 + ep - adj, 0)
                            for (adj, ep) in zip(self.adjScores,
                                                 self.effectivePars)]

        self.coursePar = sum(self.pars)
        self.grossScore = total(self.scores)
        self.targetScore = sum(self.effectivePars)
        self.stablefordTotal = sum(self.stablefords)
        self.adjustedTotal = sum(self.adjScores)
        self.netScore = self.adjustedTotal - self.targetScore
        self.adjustment = self.calc_adjustment()
        self.css = nvl(d['CSS'].PythonVal(row) if d.isFieldname('CSS')
                                               else None, self.coursePar)
        self.scoreToCSS = self.adjustedTotal - self.css

    def calc_adjustment(self):
        cat = Category(self.playingHandicap)
        if self.netScore < 0:
            return self.netScore * cat.adjustment

        if self.netScore > cat.buffer:
            return 0.1

        return 0

    @property
    def score_to_par(self):
        return total(self.adjScores) - self.css


    def __str__(self):
        header = (str(self.date)[:10] + ' '
                  + self.player + ' '
                  + '(Handicap %.1f %dp)' % (self.exactHandicap,
                                             self.playingHandicap)
                  + '  Net: %s' % pm(self.netScore)
                  + '  Adj: %s' % pm(self.adjustment)
                  + '  (%s)' % self.kind
                  + '\n')

        holes = line(list(range(1, 19)), 'Hole', header=True)
        pars = line(self.pars, 'Par')
        scores = line(self.scores, 'Score')
        adjs = line(self.adjScores, 'Adj')
        stabs = line(self.stablefords, 'Stab')
        if hasattr(self, 'newHandicapCONGU'):
            adjCONGU = ('\nNew handicap CONGU: %s'
                        % round(self.newHandicapCONGU, 1))
        else:
            adjCONGU = ''
        if hasattr(self, 'newHandicapWHS'):
            adjWHS = ('\nNew handicap WHS: %s%s\n\n'
                       % (round(self.newHandicapWHS, 1)
                          if self.newHandicapWHS is not None
                          else '-',
                          '\n[%s]' % format_counters(self.countersWHS)
                          if self.newHandicapWHS is not None
                          else ''))
        else:
            adjWHS = ''
        out = header + holes + pars + scores + adjs + stabs + adjCONGU + adjWHS
        if hasattr(self, 'roundCONGU'):
            out += str(self.roundCONGU)
        if hasattr(self, 'roundWHS'):
            out += '\n' + str(self.roundWHS)
        if hasattr(self, 'roundCONGU') or hasattr(self, 'roundWHS'):
            out = '\n---------------------\n\n' + out
        return out

    def latex(self, inBest8):
        return r'\%s{%s}{%s}{%s}{%s}' % (
            'i' if inBest8 else 'e',
            score_to_css(self),
            self.css,
            adjusted_total(self),
            str(self.grossScore) if self.grossScore is not None else 'NR'
        )




def format_counters(scorePairs):
    """
    Given a list of pairs of the form (score, counts), where counts is
    a boolean, returns the space-separated scores with a * after those
    that count (those for which counts is True).

    So given input [(4, True), (8, False), (3, True), (7,False)],
    this would return

        4* 8 3* 7

    """
    return ' '.join(f'{p[0]}{"*" if p[1] else ""}' for p in scorePairs)


def total(vals):
    return sum(vals) if all(v is not None for v in vals) else None


def line(vals, name, header=False):
    outtot = total(vals[:9])
    intot = total(vals[9:])
    tot = total(vals)
    return ('%7s' % name
            + ' '.join([fmt(v) for v in vals[:9]]) + ' '
            + ' ' + ('OUT' if header else fmt(outtot, 3)) + '  '
            + ' '.join([fmt(v) for v in vals[9:]])
            + ' ' + (' IN' if header else fmt(intot, 3)) + ' '
            + ' ' + ('TOT' if header else fmt(tot, 3))
            + '\n')


def fmt(v, width=2):
    f = '%' + str(width) + 'd'
    return (' ' * (width - 1) + '-') if v is None else f % v


def pm(v):
    return ('+' if v > 0 else '') + ('%.1f' % v)


def nvl(v, default):
    return default if v is None else v


class Category:
    def __init__(self, handicap):
        if handicap < 6:  # category 1
            self.category = 1
            self.adjustment = 0.1
            self.buffer = 1
        elif handicap < 13:
            self.category = 2
            self.adjustment = 0.2
            self.buffer = 2
        elif handicap < 21:
            self.category = 3
            self.adjustment = 0.3
            self.buffer = 3
        elif handicap < 29:
            self.cateogry = 4
            self.adjustment = 0.4
            self.buffer = 4
        else:
            self.category = 5
            self.adjustment = 1.0
            self.buffer = 1.0


if __name__ == '__main__':
    medals = len(sys.argv) > 1
    if medals and sys.argv[1].lower() not in ('m', 'medal', 'medals'):
        print('Usage: python3 adjust.py [medals]', file=sys.stderr)
        sys.exit(1)
    prefix = 'medal' if medals else 'combined'
    h = Handicaps(medals)
    h.report(os.path.join(DIR, f'{prefix}handicaps.tex'))
    h.save_handicaps(os.path.join(DIR, f'{prefix}handicaps.csv'))
