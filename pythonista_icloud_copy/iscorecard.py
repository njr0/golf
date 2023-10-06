import datetime
import time
import ui
import sys
import os

from golf.live.live import LiveRound, KnownPlayers

WIDTH, HEIGHT = ui.get_screen_size()
WIDTH, HEIGHT = int(WIDTH), int(HEIGHT)
if WIDTH > 450:
    WIDTH, HEIGHT = 375, 812
HEIGHT = int(HEIGHT * 0.8)
LABEL_WIDTH = int(0.16 * WIDTH)
LABEL_HEIGHT = int(0.0625 * HEIGHT)
LABEL_ROW_HEIGHT = int(LABEL_HEIGHT * 1.2)
HOLE_SCORE_HEIGHT = LABEL_WIDTH
HOLE_SCORE_TEXT_SIZE = LABEL_ROW_HEIGHT
HOLE_NUMBER_TEXT_SIZE = int(LABEL_ROW_HEIGHT / 2)

DEFAULT_VAL_COLOUR = 'lightgrey'

DEFAULT_PLAYERS = 3

def py(prop, row=0):
    return int(HEIGHT * prop) + row * LABEL_ROW_HEIGHT
    
def px(prop):
    return int(WIDTH * prop)
    
def nvl(v, default):
    return default if v is None else v

Y = {
    'next_prev': py(20/480),
    'player_initials': py(.1),
    'hole_number': py(.02),
    'hole_score': py(.16),
    'input': py(.32),
    'stab1_6':  py(.44),
    'stab7_12': py(.44, 1),
    'stab13_18': py(.44, 2),
    'stab_total': py(.44, 3),
    'front9': py(.75),
    'back9': py(.75, 1),
    'total_strokes': py(.75, 2),
}

ROW_LABELS = {
    'stab1_6':  '1–6',
    'stab7_12': '7–12',
    'stab13_18': '12–18',
    'stab_total': 'POINTS',
    'front9': 'OUT',
    'back9': 'IN',
    'total_strokes': 'TOTAL'
}

class UIView(ui.View):
    def __init__(self, state=None):
        self.state = state
        self.items = []
        self.tint_color = 'darkred'
        
    def add_subviews(self):
        for item in self.items:
            self.add_subview(item)
        
    def add_button(self, title, cx, cy, action, width=None, flex='LRTB', size=24, control_id=None,
                   border_width=0):
        button = ui.Button(title=title)
        button.center = (cx, cy)
        button.flex = flex
        button.action = action
        button.font = (f'<system>', size)
        button.size_to_fit()
        self.items.append(button)
        if control_id is not None:
            button.control_id = control_id
        button.border_width = border_width
        return button
        
    def add_label(self, text, x, y, width=LABEL_WIDTH, height=LABEL_HEIGHT,
                  bold=False, size=24, colour='black', border=0, align=ui.ALIGN_CENTER):
        label = ui.Label(text=text)
        as_bold = '-bold' if bold else ''
        label.font = (f'<system{as_bold}>', size)
        label.frame = (x, y, width, height)
        self.items.append(label)
        label.alignment = align
        label.border_width = border
        label.border_color = 'black'
        label.text_color = colour
        return label
        
    def add_input(self, placeholder, action, x, y, width, height, colour='black', align=ui.ALIGN_LEFT):
        field = ui.TextField(placeholder=placeholder)
        field.text = ''
        field.frame = (x, y, width, height)
        self.items.append(field)
        field.action = action
        field.text_color = colour
        field.autocapitalization_type = ui.AUTOCAPITALIZE_NONE
        field.autocorrection_type = False
        field.alignment = align
        return field
        
    def add_date_picker(self, action, y):
        d = ui.DatePicker(action)
        d.date = datetime.datetime.now()
        d.center = (px(0.2), y)
        d.mode = ui.DATE_PICKER_MODE_DATE
        self.items.append(d)
        return d


class Scorecard(UIView):
    def __init__(self, state):
        super().__init__(state)
        self.state = state
        self.n_players = state.n_players
        self.frame=(0, 0, WIDTH, HEIGHT)
        self.name = 'Scorecard'
        self.background_color = 'white'
        
        self.scores = [[i + 2] * 18 for i in range(self.n_players)]
        self.stablefords = [[4 - i] * 18 for i in range(self.n_players)]
        self.current_hole = 1
        self.cols = self.n_players + 1
        self.col_width = int(WIDTH) / self.cols
        self.col_lefts = [i * self.width / self.cols for i in range(self.n_players + 1)]
        self.score_cols = self.col_lefts[1:]
        self.prev_button = self.add_button('◀︎', self.width * 0.1, self.y('next_prev'), self.prev_hole)
        self.next_button = self.add_button('▶︎', self.width * 0.9, self.y('next_prev'), self.next_hole)
        self.add_score_labels()

        self.add_subviews()
        self.present('fullscreen') # sheet, popover, fullscreen
        
    def y(self, row):
        return Y[row]
        
    def add_score_labels(self, update=True):
        state = self.state
        hole = state.next_hole
        self.hole_number_label = self.add_label(f'HOLE {hole}', px(0.36),
                                           self.y('hole_number'), width=int(.28 * WIDTH), bold=True,
                                           size=HOLE_NUMBER_TEXT_SIZE, align=ui.ALIGN_LEFT)
        self.player_initials = [self.add_label(p, x + LABEL_WIDTH/2, self.y('player_initials'), size=14, bold=True)
                                for p, x in zip(list(state.players.keys()), self.score_cols)]
        self.hole_scores = [self.add_label(strokes_str(r, hole), x, self.y('hole_score'),
                                           height=HOLE_SCORE_HEIGHT, bold=True,
                                           colour='orange', # strokes_colour(r, hole),
                                           size=HOLE_SCORE_TEXT_SIZE, border=1)
                            for r, x in zip(state.rounds_list, self.score_cols)]
        self.input = self.add_input('', self.process_input, self.score_cols[0], self.y('input'),
                                    int(self.col_width * (self.n_players - 1) + LABEL_WIDTH), 40)
        self.stab6labels = []
        for row in ['stab1_6', 'stab7_12', 'stab13_18']:
            self.stab6labels.append([self.add_label(str(r.combined_nett_stableford(i*6 + 1, 6)),
                                                    x, self.y(row))
                                     for i, (r, x) in enumerate(zip(state.rounds_list, self.score_cols))])
        y = self.y('stab_total')
        self.stab_total_labels = [self.add_label(str(r.combined_nett_stableford(1, 18)), x, y, bold=True)
                                  for (r, x) in zip(state.rounds_list, self.score_cols)]
        self.scores9labels = []
        for row in ['front9', 'back9']:
            self.scores9labels.append([self.add_label(str(r.combined_gross(i * 9 + 1, 9,
                                                                           null_to_zero=True)), 
                                                      x, self.y(row))
                                      for i, (r, x) in enumerate(zip(state.rounds_list, self.score_cols))])
        y = self.y('total_strokes')
        self.total_score_labels = [self.add_label(str(r.combined_gross(1, 18, null_to_zero=True)),
                                                  x, y, bold=True)
                                   for (r, x) in zip(state.rounds_list, self.score_cols)]

        self.row_labels = [
            self.add_label(label, 0, self.y(k), size=12, align=ui.ALIGN_RIGHT)
                           for (k, label) in ROW_LABELS.items()
        ]
            
        self.update_ui()

    def update_score_labels(self):
        for p in range(self.n_players):
            for nine in range(2):
                self.scores9labels[nine][p].text = str(sum(self.scores[p][nine*9 : nine*9 + 9]))
            self.total_score_labels[p].text = str(sum(self.scores[p]))
        
    def stableford_total(self, p, start, n):
        return sum(self.stablefords[p][start:start+n])

    def total_strokes(self, p, start, n):
        return sum(self.scores[p][start:start+n])
        
    def next_hole(self, sender):
        self.state.get_command('')
        self.update_ui()
    
    def prev_hole(self, sender):
        self.state.get_command('p')
        self.update_ui()
        
    def update_current_hole(self, hole_number):
        self.current_hole = hole_number
        self.hole_number_label.text = f'HOLE {self.current_hole}'
                
    def update_ui(self):
        state = self.state
        hole = state.next_hole
        rounds = state.rounds_list
        self.hole_number_label.text = f'HOLE {state.next_hole}'
        for label, initials in zip(self.player_initials, state.players.keys()):
            label.text = initials
        for label, r in zip(self.hole_scores, rounds): 
             label.text = strokes_str(r, hole)
             label.text_color = strokes_colour(r, hole)
        for six in range(3):
            for r, points in zip(rounds, self.stab6labels[six]):
                points.text = str(r.combined_nett_stableford(six * 6 + 1, 6))
        for r, points  in zip(rounds, self.stab_total_labels):
            points.text = str(r.combined_nett_stableford(1, 18))
        for nine in range(2):
            for r, strokes in zip(rounds, self.scores9labels[nine]):
                strokes.text = str(r.combined_gross(nine * 9 + 1, 9, null_to_zero=True))
        for r, strokes  in zip(rounds, self.total_score_labels):
            strokes.text = str(r.combined_gross(1, 18, null_to_zero=True))

        self.input.text = ''
        state.save_all()
        
    def process_input(self, v):
        self.state.get_command(v.text.strip())
        self.update_ui()
 
    
    def set_score(self, p, hole, score):
        old_score = self.scores[p][hole - 1]
        self.scores[p][hole - 1] = score
        self.update_score_labels()
        

def strokes_str(r, n):
    """Number of strokes for this round for hole n"""
    hole = r.holes[n - 1]
    return str((hole.par + hole.strokes) if hole.gross is None else hole.gross)
    

def strokes_colour(r, n):
    """Returns grey if hole not played, otherwise number of strokes."""
    hole = r.holes[n - 1]
    return DEFAULT_VAL_COLOUR if hole.gross is None else 'black'


class LiveRoundUI(LiveRound):
    def launch(self):
        """Launches the main screen where scores are entered"""
        self.ui = Scorecard(self)
        
    def setup_match(self):
        """Launches the setup screen"""
        self.match = Match(self)
        

class Match(UIView):
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.frame=(0, 0, WIDTH, HEIGHT)
        self.name = 'Round'
        self.background_color = 'white'
        self.n_players = 1
        state.set_date(datetime.datetime.now())

        self.date_control = self.add_date_picker(self.set_date, LABEL_HEIGHT)
        self.course_control = self.add_label('Broomieknowe White', px(.0), py(0.2), px(1), LABEL_HEIGHT,
                                             align=ui.ALIGN_CENTER)
        self.cr_sr_label = self.add_label('CR 69.7  SR 123', px(.3), py(0.24), px(.4), LABEL_HEIGHT,
                                          size=14, align=ui.ALIGN_CENTER)
        self.allowance_label = self.add_label('ALLOWANCE:', px(.08), py(0.3), px(.4), LABEL_HEIGHT,
                                          size=14, align=ui.ALIGN_RIGHT)                            
        self.allowance_control = self.add_input('100%', self.set_allowance, px(.5), py(0.3), px(.2),
                                                LABEL_HEIGHT, colour=DEFAULT_VAL_COLOUR)
        
        self.players_label = self.add_label('PLAYERS', px(.38), py(0.39), px(.24), LABEL_HEIGHT,
                                            size=18, bold=True, align=ui.ALIGN_CENTER)
        self.remove_player_button = self.add_button('–', px(.33), py(.4), size=30,
                                                    action=self.remove_player, border_width=0)
        self.add_player_button = self.add_button('+', px(.7), py(.4), size=30, action=self.add_player,
                                                 border_width=0)
        defaults = list(KnownPlayers.keys())[:self.n_players]
        self.player_controls = []
        for i, initials in enumerate(defaults):
            self.player_controls.append(self.add_button(initials, px(.18 + i * .2), py(0.45),
                                                        self.set_player, control_id=f'p{i + 1}'))
        defaults = ['19.1', '14.4', '14.6', '']
        self.hi_label = self.add_label('HI', px(.02), py(0.52), px(.10), LABEL_HEIGHT, size=14)
        self.hi_controls = [self.add_input(defaults[i], self.set_hi,
                                           px(.12 + i * .2), py(0.52), px(.18), LABEL_HEIGHT)
                                for i in range(self.n_players)]
        defaults = ['21', '16', '16', '']
        # self.strokes_label = self.add_label('H', px(.02), py(0.6), px(.1), LABEL_HEIGHT, size=14)
        self.strokes_controls = [self.add_label(defaults[i],
                                                px(.12 + i * .2), py(0.6), px(.18), LABEL_HEIGHT)
                                for i in range(self.n_players)]
        self.description_control = self.add_input('Bounce Game @ Broomieknowe', self.set_description,
                                                  px(.05), py(0.7), px(.9), LABEL_HEIGHT)
                                                  
        self.go_button = self.add_button('PLAY', px(.5), py(0.8), self.go)
        self.debug = self.add_label('DEBUG', px(.02), py(0.9), px(.96), LABEL_HEIGHT, size=14)

        self.update_ui()        
        self.add_subviews()
        self.present('sheet') # sheet, popover, fullscreen
        
    def update_ui(self):
        # self.debug.text = str(self.date_control.date)
        state = self.state
        allowance = state.allowance
        control = self.allowance_control
        control.text = f'{int(allowance * 100)}%' if allowance is not None else ''
        control.text_color = DEFAULT_VAL_COLOUR if allowance is None else 'black'
        
        control = self.description_control
        control.text = state.desc if state.desc else ''
        self.n_players = getattr(state, 'n_players', 1)
        self.debug.text = str(f'control_ids: {[c.control_id for c in self.player_controls]}')
        

    def set_date(self, source):
        self.state.set_date(source.date)
        self.update_ui()
        
    def set_player(self, source):
        picker = PlayerPicker(self.state, int(source.control_id[1:]))
        
    def set_allowance(self, source):
        self.state.set_allowance_str(source.text.strip() or source.placeholder)            
        self.update_ui()
        
    def set_description(self, source):
        self.state.desc = source.text.strip() or source.placeholder
        self.update_ui()
        
    def set_hi(self, source):
        pass
        
    def add_player(self, source):
        pass

    def remove_player(self, source):
        pass     
        
    def go(self, source):
        if self.state.ready():
            self.launch()
            

class PlayerPicker(UIView):
    def __init__(self, state, player_number):
        super().__init__()
        self.state = state
        self.player_number = player_number # indexed from 1
        data = ui.ListDataSource(items=[
            {'title': p.name}
            for p in KnownPlayers.values()
        ])        
        data.action = self.chosen
            
        self.table = table = ui.TableView()
        self.frame = table.frame = (0, 0, WIDTH, HEIGHT)
        table.data_source = table.delegate = data
        self.add_subview(table)
        self.present('sheet')
        
    def chosen(self, source):
        index = source.selected_row
        knowns = KnownPlayers
        if 0 <= index < len(KnownPlayers):
            initials = list(KnownPlayers.keys())[index]
            self.state.set_player(self.player_number, initials)
        self.close()


def main():
    r = LiveRoundUI(gui=True)
    if r.saved and os.path.exists(r.path()):
        print(f'Saved as {r.path()}.')
    # card = Scorecard(3)
    # for h in range(1, 19):
        # time.sleep(1)
        # card.set_score(0, h, 1)
        # card.set_stab(0, h, 5)
    
if __name__ == '__main__':
    main()

