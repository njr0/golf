from artists.miro.session import QuietSession

def load_rounds(inpath):
    s = QuietSession()
    s.Do(f'load -null NR {inpath}')
    d = s.dataset
    return d.toRecords(dates=True)






