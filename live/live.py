import datetime
import json
import os
import re
import shutil
import sys

if sys.platform == 'ios':
    from fixpath import fixpath
    fixpath(__file__)

from golf.live.courses import Courses
from golf.live.round import (
    Player, Round, Tee, flatten, DATE_RE, nvl, fromisoformat
)
from golf.live.courses import Courses
from golf.live.players import (
    KnownPlayers, is_known, update_known_players
)

from golf.live.config import Config
try:
    from microdb.shell import Shell
    from microdb.parser import Command
except ImportError:
    Shell = Command = None


HELP = '''Q:     Quit
P:     Prev
N:     Next
L:     Latest
?:     Help
H:     Help
Hn:    Goto Hole n
HIn i: Set HI for player n
S:     Summary (to now)
R:     Round Summary (18)
Pn:    Summary for player n
U:     Upload
T txt: Reset round title
A n:   Reset allowance
'''

JSON_FILE_RE = r'^[0-9]{4}-[0-9]{2}-[0-9]{2}.json$'
MIN_HCAP = -10.0
MAX_HCAP = 54.0

FIRST_CR_LESS_PAR_DATE = datetime.date(2024, 6, 1)


def get_line(prompt='', default='', square=True):
    prompt = f'{prompt} ' if prompt else ''
    L, R = ('[', ']') if square else ('<', '>')
    default_val = f'{L}{default}{R}' if default else ''
    cue = f'{prompt}{default_val}: '
    line = input(cue).strip()
    while line == default == '':
        line = input(cue).strip()
    return default if line == '' else line


def get_date(dir):
    today = datetime.date.today().isoformat()
    date = get_line('Date', today)
    while not re.match(DATE_RE, date):
        if date.strip().upper() in '?D':
            print(list_dates(dir))
        date = get_line('Date', today)
    return fromisoformat(date).isoformat()


def list_dates(dir):
    return '\n'.join(os.path.splitext(f)[0] for f in os.listdir(dir)
                     if re.match(JSON_FILE_RE, f))


def get_int(s):
    try:
        return int(s)
    except ValueError:
        return None


def get_real(s):
    try:
        return float(s)
    except ValueError:
        return None


def get_course():
    courses = list(Courses)
    default = courses[0]
    course_key = get_line('Course', default).upper()
    while not course_key in courses:
        print('  '.join(f'{i} {c}' for i, c in enumerate(courses, 1)))
        course_key = get_line('Course', default).upper()
        if course_key.isdigit() and int(course_key) <= len(courses):
            course_key = courses[int(course_key) - 1]
    return Courses[course_key]


def get_desc(course, s=None):
    if course.allowance == 1.0:
        kind = 'Bounce Game'
    else:
        kind = 'Medal'
    default = f'{kind} @ {course.name}'
    desc = get_line('Description', default) if s is None else s
    if '@' not in desc:
        desc += f' @ {course.name}'
    print(f'Title: {desc}')
    return desc, 'bogey' in desc.lower()


def get_players():
    knowns = list(KnownPlayers.keys())
    print(f'\nSelect players from: {knowns}')
    known = list(KnownPlayers.keys())
    default_players = ' '.join(known[:3])
    players = []
    while not (1 <= len(players) <= 4):
        players = get_line('Players', default_players).upper().split(' ')
        if not (1 <= len(players) <= 4):
            print(f'Need 1-4 players')
        if len(players) == 1 and players[0].isdigit():
            players = list(players[0])
        for i in range(len(players)):
            p = players[i]
            if p.isdigit() and int(p) <= len(knowns):
                players[i] = knowns[int(p) - 1]
        unknowns = set(players) - set(KnownPlayers)
        if unknowns:
            print('Unknown:', ' '.join(sorted(unknowns)))
            print('Known:', '  '.join(f'{i} {p}'
                  for i, p in enumerate(knowns, 1)))
            players = []
    return players


def get_player_details(initials):
    print(f'Details for {initials}:')
    return get_line(), get_hi()


def get_hi():
    HI = None
    while HI is None:
        index = get_line('HI')
        HI = get_real(index)
    return HI


def get_allowance(s=''):
    a = s.replace('%', '')
    allowance = (int(a) / 100) if a.isdigit() else 0
    while not (0 < allowance <= 1):
        a = get_line('Allowance', '100%').replace('%', '')
        if a.isdigit():
            allowance = int(a) / 100
    print(f'Allowance: {allowance * 100:.0f}%')
    return allowance


class LiveRound:
    """
        Attributes:

        next_hole:      next hole to be played or updated
        n_players:      number of players (1-4)
        saved:          whether has been saved to iCloud

        date:           round date (datetime.date)
        desc:           round description
        course:         Course object

        players:        dictionary keyed on player initials,
                        mapping to Player objects
        rounds:         dictionary keys on player initials,
                        mapping to Round objects

        players_list:   list of players. Same as list(rounds.values)
        rounds_list:    list of rounds. Same as list(rounds.values)


    """
    def __init__(self, date=None, icloud=False, desc='', bogey=False,
                 config=None):
        interactive = date is None
        self.icloud = icloud
        self.is_ios = sys.platform == 'ios'
        config = config or Config()
        self.iCloudRoundDataDir = config.round_data_dir
        self.dir = config.local_round_data_dir
        self.ensure_dir_exists()
        self.saved = False
        if type(date) == datetime.datetime:
            date = date.date  # extract date component
        self.date = date or get_date(self.dir)
        self.desc = desc
        self.bogey = bogey
        if os.path.exists(self.path()):
            self.load(require_today=interactive)
        else:
            self.course = get_course()
            self.course.allowance = get_allowance()
            player_initials = get_players()
            for p in player_initials:
                if not is_known(p):
                    name, HI = get_player_details(p)
                    KnownPlayers[p] = Player(name, p, HI)
            self.players_list = [KnownPlayers[p] for p in player_initials]
            self.rounds_list = [Round(player, self.course, self.date)
                                for player in self.players_list]
            self.make_dicts(player_initials)
            self.print_players_summary()

            self.next_hole = 1
            self.desc, self.bogey = get_desc(self.course)
            self.n_players = len(self.players_list)
        done = False
        while interactive and not done:
            done = self.get_command()
            self.save_all()

    def print_players_summary(self):
        print()
        for p in self.players.values():
            print(p.summary(self.course))

    def make_dicts(self, player_initials):
        update_known_players(self.players_list)  # in case loaded
        self.players = {p: KnownPlayers[p] for p in player_initials}
        self.rounds = {player.initials: self.rounds_list[i]
                       for i, player in enumerate(self.players_list)}
        self.n_players = len(self.players_list)

    def path(self, kind='json', icloud=None):
        icloud = nvl(icloud, self.icloud)
        if icloud and not 'linux' in sys.platform:
            # This expands to the data subdir of Pythonista 3
            # on both Mac and iOS
            directory = self.iCloudRoundDataDir
            if not os.path.exists(directory):
                os.mkdir(directory)
        else:
            directory =  self.dir
        if kind == 'json':
            return os.path.join(directory, f'{self.date}.json')
        else:
            return os.path.join(directory, f'{self.date}-{kind}.csv')

    def ensure_dir_exists(self):
        if self.dir and not os.path.isdir(self.dir):
            os.makedirs(self.dir)

    def save(self, kind='json', icloud=None):
        icloud = nvl(icloud, self.icloud)
        path = self.path(kind, icloud)
        backup_path = path + '.bak'
        if os.path.exists(path):
            shutil.move(path, backup_path)
        with open(path, 'w') as f:
            if kind == 'json':
                json.dump(self.to_dict(), f)
            elif kind == 'tall':
                f.write(self.scores_csv_tall())
            elif kind == 'wide':
                f.write(self.scores_csv_wide())
            else:
                raise Exception(f'Unknown kind {kind}')
            # print(f'Round written to {path}.')

    def save_all(self, icloud=None, microdb=False):
        icloud = nvl(icloud, self.icloud)
        self.save('json', icloud)
        # self.save('tall', icloud)
        # self.save('wide', icloud)
        self.saved = True
        msgs = ['Saved to iCloud.' if icloud else '']
        if microdb:
            if Shell:
                localpath = self.path('json', icloud=False)
                localfile = os.path.basename(localpath)
                shell = Shell('default')
                cmd = Command('rcp',
                              localpath=localpath,
                              remotepath=os.path.join('golf/data/',
                                                      localfile))
                r = shell.do_rcp(cmd)
                if r.status == 200:
                    msgs.append('Uploaded to MicroDB OK')
                    cmd = Command('act', action='tracker')
                    r = shell.do_act(cmd)
                    if r.status == 200:
                        msgs.append('Tracker regenerated.')
                    else:
                        msgs.append(f'*** Failed to regenerate tracker: {r}')
                else:
                    msgs.append(f'*** Failed to uploaded to MicroDB: {r}')
            else:
                msgs.append('*** No MicroDB shell available.')
        return '\n'.join(msgs)

    def load(self, require_today=True):
        with open(self.path()) as f:
            d = json.load(f)
            if type(d.get('date', None)) == datetime.datetime:  # Can't be,
                                                                # Can it?
                print(111)
                d['date'] = d['date'].date()
            elif type(d.get('date', None)) == str:
                try:
                    print(222)
                    dt = datetime.datetime.fromisoformat(d[date])
                    d['date'] = dt.date()
                except:
                    print(333)
                    pass
        print(444, d['date'], type(d['date']))
        if require_today:
            assert d['date'] == self.date
        course_dict = d.get('course', d.get('course_tee'))
        if 'allowance' in d:
            course_dict['allowance'] = d['allowance']
        course_dict['use_cr_less_par'] = d['date'] >= FIRST_CR_LESS_PAR_DATE
        self.course = Tee(**course_dict)
        self.rounds_list = rounds_list = []
        if 'players' in d:
            self.players_list = [Player(**p) for p in d['players']]
            p0 = d['players'][0]
            if 'round' in p0:
                # new format
                for i, player in enumerate(self.players_list):
                    rounds_list.append(
                            Round(player, self.course, self.date,
                                  scores=d['players'][i]['round']['gross']))
            else:
                # old format
                self.rounds_list = [Round(player, self.course, self.date,
                                          scores=rnd['gross'])
                                    for (player, rnd) in zip(self.players_list,
                                                             d['rounds'])]
        elif 'rounds' in d:
            self.players_list = [Player(**r['player']) for r in d['rounds']]
            for player, r in zip(self.players_list, d['rounds']):
                rounds_list.append(
                    Round(player, self.course, self.date,
                          scores=r['gross_scores']))
        else:
            raise Exception('No rounds')
        self.make_dicts([p.initials for p in self.players_list])
        self.next_hole = d.get('next_hole', d.get('current_hole'))
        self.desc = d.get('desc', d.get('description', ''))
        self.bogey = d.get('bogey', False)
        if d.get('competitions', False):
            self.bogey = 'bogey' in [c.lower() for c in d.get('competitions')]
        sixes = d.get('sixes', [1, 2])
        if not isinstance(sixes, list) or len(sixes) != 2:
            sixes = [1, 2]
        self.sixes = sixes

    def to_dict(self):
        players = flatten(self.players_list)
        rounds = [r.to_dict() for r in self.rounds_list]
        for (p, r) in zip(players, rounds):
            p['round'] = r
        return {
            'date': self.date,
            'course_tee': flatten(self.course),
            'desc': self.desc,
            'players': players,
            'next_hole': self.next_hole,
            'description': self.desc,
            'bogey': self.bogey,
        }

    def get_command(self):
        i = self.next_hole - 1
        actuals = [rnd.holes[i].gross for rnd in self.rounds.values()]
        if all(a is None for a in actuals):
            expected = [rnd.holes[i].net_par for rnd in self.rounds.values()]
            square = True
        else:
            expected = [nvl(a, '.') for a in actuals]
            square = False
        default = ' '.join(str(e) for e in expected)
        nl = '\n'
        try:
            line = get_line(f'{nl}Hole {self.next_hole}',
                            default, square).upper()
        except EOFError:
            sys.exit(0)
        if line in ('Q', 'P', 'N', 'L', 'S', 'R', 'H', '?', 'U', 'HELP'):
            if line == 'Q':
                return True
            elif line == 'P':
                self.next_hole = (self.next_hole - 2) % 18 + 1
            elif line == 'N':
                self.next_hole = self.next_hole % 18 + 1
            elif line in ('?', 'H', 'HELP'):
                print(HELP)
            elif line == 'L':
                self.next_hole = self.latest()
            elif line == 'S':
                self.print_summary()
            elif line == 'R':
                self.print_round_summary()
            elif line == 'U':
                msg = self.save_all(icloud=True, microdb=True)
                self.print_summary()
                print(msg)
            return False
        elif line.startswith('HI'):
            L = line[2:].strip()
            parts = L.split(' ')
            if len(parts) == 2:
                pn, HI = parts
                pn = get_int(pn) - 1
                if pn is not None and 0 <= pn < self.n_players:
                    HI = get_real(HI)
                    if HI is not None and MIN_HCAP <= HI <= MAX_HCAP:
                        player = self.players_list[pn]
                        player.HI = HI
                        print('>>>', player)
                        print('---', player.summary(self.course))
                        for hole in self.rounds_list[pn].holes:
                            hole.recalc(self.course, player)
            self.print_players_summary()
            return False
        elif line.startswith('H'):
            h = line[1:].strip()
            try:
                hole = int(h)
                if 1 <= hole <= 18:
                    self.next_hole = hole
            except ValueError:
                pass
            return False
        elif line.startswith('P'):
            p = line[1:].strip()
            try:
                player = int(p)
                if 1 <= player <= self.n_players:
                    n = player - 1
                else:
                    return False
            except:
                pass
            rnd = self.rounds_list[n]
            print(rnd.summary(holes=False, nines=False, sixes=False,
                              scores=True))
            return False
        elif line.startswith('A'):
            self.course.allowance = get_allowance(line[1:].strip())
            return False
        elif line.startswith('T'):
            self.desc, self.bogey = get_desc(self.course, line[1:].strip())
            return False

        s_scores = line.split()
        if len(s_scores) == 1 and self.n_players > 1:
            s_scores = list(line)
        s_scores = [v for v in s_scores if v]
        s_scores = [('0' if v in ('-', '.') else v) for v in s_scores]
        scores = None
        if (len(s_scores) == self.n_players
               and all(s.isdigit() for s in s_scores)):
            try:
                scores = [int(s) for s in s_scores]
            except ValueError:
                pass
        if scores:
            for p, rnd, score in zip(self.players.values(),
                                     self.rounds.values(),
                                     scores):
                rnd.holes[i].set_score(score, self.course, p)
            self.print_summary(i)
            self.next_hole += 1
            if self.next_hole == 19:
                self.next_hole = 1
        return False

    def print_summary(self, i=None):
        # i = i or (self.next_hole - 1) % 18
        joint = '\n' if self.is_ios else '  '
        if i is None:
            for k, r in self.rounds.items():
                print(r.summary(holes=False, nines=True, sixes=False,
                                scores=False, tight=True))
                print()
        else:
            print(joint.join(f'{k}: {r.holes[i].short()}'
                             for (k, r) in self.rounds.items()))
            print(joint.join(f'{k}: {r.post_hole_summary(self.next_hole)}'
                             for (k, r) in self.rounds.items()))

    def print_round_summary(self):
        joint = '\n' if self.is_ios else '  '
        print(joint.join(f'{k}: {r.post_hole_summary(18)}'
                         for (k, r) in self.rounds.items()))

    def latest(self):
        i = 0
        while i < 17:
            if all(r.holes[i].gross is None
                   for r in self.rounds.values()):
                return (i + 1) % 18
            i += 1
        return 1

    def scores_csv_tall(self):
        header = ','.join(['Hole',] + [p.initials for p in self.players_list])
        lines = [header]
        holes = [str(h) for h in range(1, 19)]
        score_lines = zip(holes, *(r.string_scores_list()
                            for r in self.rounds_list))
        lines.extend([','.join(line) for line in score_lines])
        lines.append('')
        return '\n'.join(lines)

    def scores_csv_wide(self):
        holes = ','.join([f'H{i}' for i in range(1, 19)])
        lines = ['Player,' + holes]
        z = zip([p.initials for p in self.players_list],
                [r.string_scores_list() for r in self.rounds_list])
        for (player, scores) in z:
            string_scores =  ','.join(scores)
            lines.append(f'{player},{string_scores}')
        lines.append('')
        return '\n'.join(lines)


if __name__ == '__main__':
    r = LiveRound()
    if r.saved and os.path.exists(r.path()):
        print(f'Saved as {r.path()}.'
)
