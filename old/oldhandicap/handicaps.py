from handicapindex import Round, handicap_index
from load import load_rounds

def main():
    raw_rounds = load_rounds('~/iNJR/golf/handicap_rounds.csv')
    raw_rounds.sort(key=lambda r: r.Date)

    rounds = [Round(r.Date.date().isoformat(), course=r.Course,
                    tee=r.Tee, differential=r.differential)
              for r in raw_rounds]
    N = len(rounds)
    for i in range(0, N - 19):
        print(handicap_index(rounds[i:i + 20]))



if __name__ == '__main__':
    main()

