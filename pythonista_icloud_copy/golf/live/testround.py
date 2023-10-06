from round import Player, Round
from courses import BroomieknoweWhite

if __name__ == '__main__':

    player1 = Nick = Player('Nick', 'NR', 17.9)
    player2 = Andy = Player('Andy', 'AM', 17.1)
    tee = BroomieknoweWhite
    date = '2022-10-07'
    njr_rnd = Round(Nick, tee, date,
                    [9, 5, 5, 5, 3, 6, 7, 6, 5, 5, 4, 6, 6, 7, 3, 6, 4, 4])
    am_rnd = Round(Andy, tee, date,
                   [5, 7, 8, 8, 4, 5, 5, 5, 5, 5, 4, 5, 6, 7, 4, 5, 6, 4])


    print(tee, end='\n\n')

    for (player, rnd) in ((Nick, njr_rnd), (Andy, am_rnd)):
        print(player.summary(tee), end='\n\n')
        print(rnd.summary(), end='\n\n')

