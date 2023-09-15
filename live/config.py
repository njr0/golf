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

# Platform Dependent

ICLOUD_DIR = (IOS_ICLOUD_BASE_DIR if sys.platform == 'ios'
                                  else MAC_ICLOUD_BASE_DIR)
ICLOUD_ROUND_DATA_DIR = os.path.join(ICLOUD_DIR, DATA_SUBDIR)

if sys.platform == 'linux':
    TRACKER_DIR = MICRODB_TRACKER_DIR
    ROUND_DATA_DIR = MICRODB_ROUND_DATA_DIR
else:
    TRACKER_DIR = ICLOUD_TRACKER_DIR
    # TRACKER_DIR = MAC_TRACKER_DIR  # for now
    ROUND_DATA_DIR = ICLOUD_ROUND_DATA_DIR



class Config:
    def __init__(self, mac_microdb=False):
        # If mac_microdb is set to true, building the tracker
        # on the mac reads from the mac tracker data dir
        # and writes to the mac tracker dir
        if mac_microdb:
            self.tracker_dir = MAC_TRACKER_DIR
            self.round_data_dir = MAC_ROUND_DATA_DIR
        else:
            self.tracker_dir = TRACKER_DIR
            self.round_data_dir = ROUND_DATA_DIR
        self.index_template_path = INDEX_TEMPLATE_PATH
        self.index_path = os.path.join(self.tracker_dir, 'index.html')

