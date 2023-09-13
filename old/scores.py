from __future__ import print_function

import os
import re

from collections import OrderedDict

DATE_RE = re.compile(r'^.*(\d{2}/\d{2}/\d{4}).*$')
INT_RE = re.compile(r'^.*</span>(\d{1,3})<span.*$')
REAL_RE = re.compile(r'^.*</span>(\d{1,2}\.\d)<span.*$')


class Round:
    def __init__(self, date):
        self.date = date
        self.scores = []
        self.out9 = 0
        self.in9 = 0
        self.tot = 0
        self.hcap = 0

    def __str__(self):
        return '%s: %s: %3s (%s)' % (self.date, self.scorestr(),
                                     self.tot, self.hcap)

    __repr__ = __str__

    def scorestr(self):
        return ' '.join('%2d' % s for s in self.scores)

    def csv_score(self):
        return ','.join(str(s) for s in self.scores)

    def rdt(self):
        return '%s-%s-%s' % (self.date[-4:], self.date[3:5], self.date[:2])

    def csv_line(self):
        return ','.join(str(s) for s in (self.rdt(), self.csv_score(),
                                         self.tot, self.hcap,
                                         self.out9, self.in9))


class Scores:
    def __init__(self, inpath):
        self.rounds = OrderedDict()
        with open(inpath) as f:
            text = f.read()
        self.lines = lines = text.splitlines()
        N = len(self.lines)
        self.line_no = 0
        while self.line_no < N:
            line = lines[self.line_no]
            m = re.match(DATE_RE, line)
            if m:
                date = m.group(1)
                self.rounds[date] = r = Round(date)
                self.line_no += 2  # skip separator and Out
                for j in range(9):
                    r.scores.append(self.get_int())
                r.out9 = self.get_int()
                self.line_no += 1  # skip In
                for j in range(9):
                    r.scores.append(self.get_int())
                r.in9 = self.get_int()
                r.tot = self.get_int()
                r.hcap = self.get_real()
            self.line_no += 1
        for date, round in self.rounds.items():
            print(round)
        self.write_csv(inpath)

    def write_csv(self, inpath):
        outpath = os.path.splitext(inpath)[0] + '.csv'
        with open(outpath, 'w') as f:
            f.write('date,%s,total,handicap,out,in\n'
                    % ','.join('hole%s' % i for i in range(1, 19)))
            f.write('\n'.join(r.csv_line() for r in self.rounds.values()))
            f.write('\n')
        print('Written %s.' % outpath)


    def get_int(self):
        m = re.match(INT_RE, self.lines[self.line_no])
        assert m
        self.line_no += 1
        return(int(m.group(1)))

    def get_real(self):
        m = re.match(REAL_RE, self.lines[self.line_no])
        assert m
        self.line_no += 1
        return(float(m.group(1)))





scores = Scores('njr-stats-2018-04-21.html')



