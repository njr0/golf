import ui

from console import hud_alert

shows_result = True
def prev_hole(sender):
	'@type sender: ui.Button'
	hole_label = sender.superview['hole_number_label'].text
	hole = int(hole_label[5:])
	if hole > 1:
		sender.superview['hole_number_label'].text = f'HOLE {hole - 1}'
			
def next_hole(sender):
	'@type sender: ui.Button'
	hole_label = sender.superview['hole_number_label'].text
	hole = int(hole_label[5:])
	if hole < 18:
		sender.superview['hole_number_label'].text = f'HOLE {hole + 1}'
			
def change_score(sender):
	'@type sender: ui.Button'
	name = sender.name
	player = int(name[6])
	up = name[7] =='u'
	tablename = f'player{player}scoretable'
	table = sender.superview[tablename].data_source
	score = table.items[2]
	if score.isdigit():
		score = int(score)
		if up:
			score += 1
		elif score > 0:
			score -= 1
		table.items[2] = str(score)

	

v = ui.load_view('GolfScores')
v.present('sheet')
