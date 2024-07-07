import os
import sys

# Fixed

THISDIR = os.path.dirname(__file__)
INDEX_TEMPLATE_PATH = os.path.join(  # all platforms
    THISDIR,
    'templates',
    'index-template.html'
)
COURSES_PATH = os.path.join(THISDIR, 'courses.json')

# Platform Specific:

MAC_ICLOUD_BASE_DIR = '/Users/njr/Library'
IOS_ICLOUD_BASE_DIR = '/private/var/mobile/Library/'
DATA_SUBDIR = os.path.join('Mobile Documents',
                           'iCloud~com~omz-software~Pythonista3',
                           'Documents',
                           'data')

ICLOUD_TRACKER_DIR = '/Users/njr/iNJR/golf/microdb'
MAC_TRACKER_DIR = '/Users/njr/root/microdb/static/golf'
MAC_ROUND_DATA_DIR = '/Users/njr/root/microdb/static/golf/data'

MICRODB_TRACKER_DIR = '/microdb/static/golf'
MICRODB_ROUND_DATA_DIR = '/microdb/static/golf/data'
NJR_TRACKER_DIR = '/home/njr/tracker'

# Platform Dependent

ICLOUD_DIR = (IOS_ICLOUD_BASE_DIR if sys.platform == 'ios'
                                  else MAC_ICLOUD_BASE_DIR)
ICLOUD_ROUND_DATA_DIR = os.path.join(ICLOUD_DIR, DATA_SUBDIR)

if 'linux' in sys.platform:
    TRACKER_DIR = MICRODB_TRACKER_DIR
    ROUND_DATA_DIR = MICRODB_ROUND_DATA_DIR
    LOCAL_ROUND_DATA_DIR = MICRODB_ROUND_DATA_DIR
else:
    TRACKER_DIR = ICLOUD_TRACKER_DIR
    # TRACKER_DIR = MAC_TRACKER_DIR  # for now
    ROUND_DATA_DIR = ICLOUD_ROUND_DATA_DIR
    LOCAL_ROUND_DATA_DIR = os.path.expanduser('~/Documents/golf')


class Config:
    def __init__(self, mac_microdb=False, njr=False):
        # If mac_microdb is set to true, building the tracker
        # on the mac reads from the mac tracker data dir
        # and writes to the mac tracker dir
        if mac_microdb and 'linux' not in sys.platform:
            self.tracker_dir = MAC_TRACKER_DIR
            self.round_data_dir = MAC_ROUND_DATA_DIR
        else:
            self.tracker_dir = NJR_TRACKER_DIR if njr else TRACKER_DIR
            self.round_data_dir = ROUND_DATA_DIR
        self.index_template_path = INDEX_TEMPLATE_PATH
        self.index_path = os.path.join(self.tracker_dir, 'index.html')
        self.local_round_data_dir = LOCAL_ROUND_DATA_DIR

    def __str__(self):
        return 'Config(\n%s\n)' % '\n'.join(
                   f'    {k}: {v}' for (k, v) in self.__dict__.items())


if __name__ == '__main__':
    from pprint import pprint as pp
    if len(sys.argv) != 1:
        if not len(sys.argv) == 2 or not sys.argv[1] in ('-m', '-n'):
            print('USAGE: python config.py [-m] [-n]', file=sys.stderr)
            sys.exit(1)
        mac_microdb = True
    else:
        mac_microdb = False
    config = Config(mac_microdb=mac_microdb)
    pp(config.__dict__)
