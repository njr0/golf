from __future__ import print_function

"""
Collects all the scores for a medal (the HTML saved from howdidido.csv)
into a CSV file.
"""

import datetime
import os
import re
import sys

from collections import OrderedDict

INT_RE = re.compile(r'^.*</span>(\d{1,3})<span.*$')
REAL_RE = re.compile(r'^.*</span>(\d{1,2}\.\d)<span.*$')

DATE_RE = re.compile(r'^.*[^\d](\d{2} [A-Z][a-z]+ \d{4}).*$')
CSS_RE = re.compile(r'^.*CSS : (\d{2}).*$')
NAME_RE = re.compile(r'^.*data\-player\=\d+\]\">([^<]+).*$')
SCORE_RE = re.compile(r'^.*[^\d](\d+\s*\-\s*\-?\d+\s*\=\s*\d+|NR|DQ).*$')
#NR_RE = re.compile(r'^.*>(NR)<.*$')
HCAP_RE = re.compile(r'^.[^\d]*(\d+\.\d+|AWAY).*$')
PLACE_RE = re.compile(r'^\s*(\d+)\s*$')


class Round:
    def __init__(self, date, player, pos, tot, hcap, nett, new_hcap, css):
        self.date = date
        self.player = player
        self.pos = pos
        self.tot = tot or ''
        self.hcap = hcap or ''
        self.nett = nett or ''
        self.new_hcap = '' if new_hcap == 'AWAY' else new_hcap
        self.css = css

    def __str__(self):
        return '%s. %s: %s: %s - %s = %s  [%s] [%s]' % (self.pos,self.date,
                                                        self.player, self.tot,
                                                        self.hcap, self.nett,
                                                        self.new_hcap,
                                                        self.css)

    __repr__ = __str__

    def csv_line(self):
        return ','.join(str(s) for s in (self.pos, self.date, self.player,
                                         self.tot, self.hcap, self.nett,
                                         self.new_hcap, self.css))


class Scores:
    def __init__(self, inpath):
        self.rounds = OrderedDict()
        with open(inpath) as f:
            text = f.read()
        self.lines = lines = text.splitlines()
        N = len(self.lines)
        self.line_no = 0
        date = css = None
        RE = DATE_RE
        while self.line_no < N:
            line = lines[self.line_no]
            # First find date and CSS
            m = re.match(RE, line)
            if m:
                if date is None:
                    date = rdt_date(m.group(1))
                    RE = CSS_RE
                else:
                    css = m.group(1)
                    break
            self.line_no += 1
        RE, stage = PLACE_RE, 0
        while self.line_no < N:
            line = lines[self.line_no]
            m = re.match(RE, line)
            if m:
#                print(m.groups(), stage)
                if stage == 0:
                    tot = hcap = nett = new_hcap = 0
                    pos = m.group(1)
                    RE = NAME_RE
                    stage += 1
                elif stage == 1:
                    name = m.group(1)
                    name = name.replace(' (Non C)', '').replace(' (R)', '')
                    RE = SCORE_RE
                    stage += 1
                elif stage == 2:
                    s = m.group(1)
                    if s in ('NR', 'DQ'):
                        tot = hcap = nett = None
                    else:
                        parts = m.group(1).split()
                        tot = parts[0]
                        hcap = parts[2]
                        nett = parts[4]
                    RE = HCAP_RE
                    stage += 1
                elif stage == 3:
                    new_hcap = m.group(1)
                    round = Round(date, name, pos, tot, hcap, nett, new_hcap,
                                  css)
                    self.rounds[name] = round
                    print(round)
                    RE = PLACE_RE
                    stage = 0  # next player
            self.line_no += 1

        print(len(self.rounds))

        self.write_csv(inpath)

    def write_csv(self, inpath):
        outpath = os.path.splitext(inpath)[0] + '.csv'
        with open(outpath, 'w') as f:
            f.write('pos,date,player,tot,hcap,nett,new_hcap,css\n')
            f.write('\n'.join(r.csv_line() for r in self.rounds.values()))
            f.write('\n')
        print('Written %s.' % outpath)


def rdt_date(dt):
    d = datetime.datetime.strptime(dt, '%d %B %Y')
    return d.strftime('%Y-%m-%d')


if __name__ == '__main__':
    for f in os.listdir('data'):
        if f.endswith('.html') and f.startswith('medal-'):
            scores = Scores(os.path.join('data', f))

