import os
import sys

if sys.platform == 'ios':
    try:
        from round import Player
        import jsonl
    except ImportError:
        from golf.live.round import Player
        from golf.live import jsonl
else:
    from golf.live.round import Player
    from golf.live import jsonl

THISDIR = os.path.dirname(__file__)
PLAYERS_PATH = os.path.join(THISDIR, 'players.jsonl')

KnownPlayers = {
    p['initials']: Player(**p) for p in jsonl.load(PLAYERS_PATH)
}


def is_known(player):
    return player in KnownPlayers


def update_known_players(players_list):
    for p in players_list:
        KnownPlayers[p.initials] = p
