from artists.miro.office.excel import SpreadsheetReader
from artists.giacometti.utils import nvl, DQuote

TEES = 'C2'
DATE = 'A2'
HCAP_ROW = 4


def player_col(player):
    assert player in ('Nick', 'Andy', 'Kenny')
    return ('D' if player == 'Nick'
                else 'E' if player == 'Andy'
                else 'F')

def cells(player):
    rows = [i for i in range(6, 25) if i != 15]
    col = player_col(player)
    return [f'{col}{row}' for row in rows]


class Scores:
    def __init__(self, sheet):
        self.name = sheet.name
        self.nick = check([sheet.sheet[v].value for v in cells('Nick')])
        self.andy = check([sheet.sheet[v].value for v in cells('Andy')])
        self.kenny = check([sheet.sheet[v].value for v in cells('Kenny')])
        self.tees = sheet.sheet[TEES].value.lower()
        self.nPlayers = (int(self.nick is not None)
                         + int (self.andy is not None)
                         + int (self.kenny is not None))
        self.date = sheet.sheet[DATE].value.strftime('%Y-%m-%d')
        if self.date > '2020-04-01':
            self.tees += '-new'
        self.handicaps = [sheet.sheet[f'{col}{HCAP_ROW}'].value
                          for col in 'DEF']

    def line(self, player):
        scores = self.__dict__[player.lower()]
        if scores is None:
            return ''
        pc = 0 if player == 'Nick' else 1 if player == 'Andy' else 2
        handicap = str(self.handicaps[pc])
        vals = [self.date, player, handicap, self.tees, DQuote(self.name),
                '1']  # stake
        vals.extend(str(s) for s in scores)
        return ','.join(vals) + '\n'


def check(scores):
    return None if all(v is None or v == 0 for v in scores) else scores



def main(tracker2020path, scores2019path, outpath):
    reader = SpreadsheetReader(tracker2020path)
    scores = [
        Scores(sheet) for sheet in reader.sheetdata[::-1]
    ]

    with open(outpath, 'w') as f:
        with open(scores2019path) as fr:
            f.write(fr.read())
        for score in scores:
            if score.nPlayers > 1:
                f.write(score.line('Nick'))
                f.write(score.line('Andy'))
                f.write(score.line('Kenny'))



if __name__ == '__main__':
    main('/Users/njr/iNJR/golf/2020/Tracker2020.xlsx',
         '/Users/njr/iNJR/golf/scores2019.txt',
         '/Users/njr/iNJR/golf/scores.txt')


