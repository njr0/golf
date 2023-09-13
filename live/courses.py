import json
import os
import sys

from golf.live.round import Tee

THISDIR = os.path.dirname(__file__)
COURSES_PATH = os.path.join(THISDIR, 'courses.json')

def load_courses(path):
    with open(path) as f:
        courses = {
            k: Tee(**v) for k, v in json.load(f).items()
        }
    return courses

Courses = load_courses(COURSES_PATH)


