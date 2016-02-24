import os.path
import sys


def get_sieglib_dir():
    if getattr(sys, "frozen", False):
        sieglib_dir = os.path.dirname(sys.executable)
    else:
        sieglib_dir = os.path.dirname(os.path.dirname(__file__))
    return sieglib_dir

SIEGLIB_DIR = get_sieglib_dir()


def get_resources_dir(sieglib_dir):
    return os.path.join(sieglib_dir, "resources")

RESOURCES_DIR = get_resources_dir(SIEGLIB_DIR)
