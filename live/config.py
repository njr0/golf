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

INDEX_PATH = os.path.join(TRACKER_DIR, 'index.html')


