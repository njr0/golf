import sys
from artists.miro.session import QuietSession, MiroSession

Session = QuietSession
# Session = MiroSession

def calc_hi_old(values, adj, kind, reverse=False, N=8):
    assert kind in ('HI', 'AHI', 'HI20')
    assert N == (20 if kind == 'HI20' else 8)
    assert reverse == (kind != 'HI')
    N = (20 if kind == 'HI20' else 8)
    reverse = (kind != 'HI')

    if reverse:
        svals = list(sorted(values, key=lambda v: -v))[:N]
        return round(sum(svals) / N, 1)
    else:
        adjustments = [sum(a for a in adj[i:20]) for i in range(20)]
        effective = [v + a for (v, a) in zip(values, adjustments)]
        svals = list(sorted(effective))[:N]
        return round(sum(svals) / N, 1)


def calc_hi(values, adj, kind, reverse=False, N=8):
    assert kind in ('HI', 'AHI', 'HI20')
    N = 20 if kind == 'HI20' else 8
    reverse = (kind != 'HI')
    W = min(len(values), 20)  # window length
    rem = 0.0
    if len(values) == 0:
        return 0.0
    if W < 20 and kind != 'HI20':
        n = 0.4 * W
        if abs(n - round(n)) < 0.0001:
            N = N1 = int(round(n))
        else:
            N = int(n)
            N1 = N + 1
            rem = n - N
            weights = [1.0] * N + ([rem] if rem else [])
            totweight = sum(weights)
    else:
        N1 = N
    if reverse:
        svals = list(sorted(values, key=lambda v: -v))[:N1]
        if rem and kind != 'HI20':
            return round(sum((v * w) for (v, w) in zip(svals, weights))
                         / totweight, 1)
        else:
            return round(sum(svals) / len(svals), 1)
    else:
        adjustments = [sum(a for a in adj[i:W]) for i in range(W)]
        effective = [v + a for (v, a) in zip(values, adjustments)]
        svals = list(sorted(effective))[:N1]
        if rem:
            return round(sum((v * w) for (v, w) in zip(svals, weights))
                         / totweight, 1)
        else:
            return round(sum(svals) / N1, 1)


def main(player, s):
    player = player.lower()
    name = player.upper()
    s.Do(f'. -f handicap {player}')
    values = s.Do('(values differential)')
    adj = s.Do('(values Adj)')
    N = len(values)


    hi = [calc_hi(values[max(0, i-20):i], adj[max(0, i-20):i], 'HI') for i in range(1, N + 1)]
    ahi = [calc_hi(values[max(0, i-20):i], adj[max(0, i-20):i], 'AHI', reverse=True)
           for i in range(1, N + 1)]
    hi20 = [calc_hi(values[max(0, i-20):i], adj[max(0, i-20):i], 'HI20', reverse=True, N=20)
            for i in range(1, N + 1)]

    s.vars['hi_vals'] = hi
    s.vars['ahi_vals'] = ahi
    s.vars['hi20_vals'] = hi20

    s.Do(f'''
    def HI (eval hi_vals)
    def AHI (eval ahi_vals)
    def HI20 (eval hi20_vals)
    save njr/handicap-{player}
    select HI > 0
    compress
    format -datefmt r-d Date
    bin -d -LR Date
    x -r -D "v" any HI by Date
    D.def Kind "HI"
    x -r -R A -D "v" any AHI by Date
    A.def Kind "AHI"
    x -r -R B -D "v" any HI20 by Date
    B.def Kind "HI20"
    D.append $A
    D.append $B
    pushselect (= Date (max Date))
    set FinalHI any HI
    set FinalAHI any AHI
    set FinalHI20 any HI20
    set WhiteHI (int (round (/ (* FinalHI 124) 113)))
    set YellowHI (int (round (/ (* FinalHI 120) 113)))
    set WhiteHI95 (int (round (/ (* FinalHI 124 0.95) 113)))
    set YellowHI95 (int (round (/ (* FinalHI 120 0.95) 113)))
    popselect
    data D
    setq Kinds (list "AHI" "HI20" "HI")
    (tag (field "Kind") "B" Kinds)
    binsort -b  Kind
    bincolour Red Kind AHI
    bincolour Orange Kind HI
    bincolour indigo Kind HI20
    def date (date Date)
    tag L="Date" date
    format -datefmt r-d date
    bin -d date
    def label (string v dps: 1)
    tag L=" " Kind
    set expand (if (< (count) 60) 3 1)
    set hs (* 0.75 expand)
    set x2 (* 100 (/ (- (count) (* 3 9)) (count)))
    if (= expand 3)
        set x2 (+ x2 50)
    fi
    setq g x -L -G -line -ps .1 -grid -hscale $hs -vscale 2 -hover -clabels -la -1 -ym 0 -yM 36 -ny 36 -t "{name} Handicap Index, HI20, and AntiHandicap Index" -aggnames "HI" mean v any label by date Kind
    g.annotate -prb -textscale 2 98 96 (+ "AHI:  " (string FinalAHI dps: 1))
    g.annotate -prb -textscale 2 98 90 (+ "HI20:  " (string FinalHI20 dps: 1))
    g.annotate -prb -textscale 2 98 84 (+ "HI:  " (string FinalHI dps: 1))

    g.annotate -prb -textscale 2 $x2 96 (+ "White:  " (string WhiteHI))
    g.annotate -prb -textscale 2 $x2 90 (+ "Yellow:  " (string YellowHI))
    g.annotate -prb -textscale 2 $x2 84 (+ "White @ 95%:  " (string WhiteHI95))
    g.annotate -prb -textscale 2 $x2 78 (+ "Yellow @ 95%:  " (string YellowHI95))
    g.save (join-path SVG-DIR "{player}-handicap.svg")
    (setq (eval player) g)
    set title (+ player " Handicap")
    set content (eval g)
    set path (join-path GOLF-MDB-DIR (+ player "-handicap" ".html"))
    template templates/golf-template.html $path
    ''')
    print(f'Saved {player}-handicap.svg & {player}-handicap.html')


if __name__=='__main__':
    knowns = players = ('njr', 'am', 'ks', 'kd')
    if len(sys.argv) == 2:
        players = []
        for p in sys.argv[1:]:
            player = p.lower()
            if not player in players:
                print(f'Unknown player {player}.')
                sys.exit(1)
        players.append(player)
    s = Session()
    s.Do('require paths')
    for player in players:
        main(player, s)
    s.Do('. handicap-counters')
    for player in players:
        print(f'Saved {player}-counters.html')
    s.Do('''
    set content "More to come . . ."
    set title "Index"
    set path (join-path GOLF-MDB-DIR "index.html")
    template templates/golf-template.html $path
    ''')
    print(f'Saved index.html')
