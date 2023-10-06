from artists.klee.svgc import SVGCoordinates

from golf.live import LiveRound

rnd = LiveRound('2022-10-23')

def fmt18(name, values):
    values = ' '.join(f'{v:2d}' for v in values)
    return f'{name + ":":>11s} {values}'


print(fmt18('HOLE', range(1, 19)))
print(fmt18('PAR', rnd.course.par))
for p, r in rnd.rounds.items():
    print(fmt18(f'{p} SCORE', r.score_list()))
print()
for p, r in rnd.rounds.items():
    print(fmt18(f'{p} POINTS', r.nett_points_list()))



