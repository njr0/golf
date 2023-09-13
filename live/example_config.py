import os
import sys

MAC_ICLOUD_BASE_DIR = '/Users/njr/Library'
IOS_ICLOUD_BASE_DIR = '/private/var/mobile/Library/'
DATA_SUBDIR = os.path.join('Mobile Documents',
                           'iCloud~com~omz-software~Pythonista3',
                           'Documents',
                           'data')
ICLOUD_DIR = (IOS_ICLOUD_BASE_DIR if sys.platform == 'ios'
                                  else MAC_ICLOUD_BASE_DIR)

THISDIR = os.path.dirname('__file__')
ICLOUD_MDB_GOLF_DIR = os.path.join('/Users/njr/iNJR/golf/microdb')
COURSES_PATH = os.path.join(THISDIR, 'courses.json')
INDEX_TEMPLATE_PATH = os.path.join(THISDIR, 'templates', 'index-template.html')
INDEX_PATH = os.path.join(ICLOUD_MDB_GOLF_DIR, 'index.html')
