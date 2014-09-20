import configparser
import os
import sys
import inspect

import util


# the current working directory at the time socrates started
_cwd = os.getcwd()

# the absolute path to this config.py file while running
_conf = os.path.abspath(inspect.getfile(inspect.currentframe()))

# SOCRATES_DIR should contain the running socrates.py file
SOCRATES_DIR, _ = os.path.split(_conf)
SOCRATES_CONFIG = SOCRATES_DIR + os.sep + 'socrates.ini'

_parser = configparser.ConfigParser()

if os.path.isfile(SOCRATES_CONFIG):
    _parser.read(SOCRATES_CONFIG)
    if len(_parser) < 2:
        util.sprint("warning: found config file, but it looks empty")

static_dir = _parser.get('socrates', 'static_dir',
                         fallback=SOCRATES_DIR + os.sep + 'static')
dropbox_dir = _parser.get('socrates', 'dropbox_dir',
                          fallback=SOCRATES_DIR + os.sep + 'dropbox')


_f = False
if not os.path.isdir(static_dir):
    _f = True
    util.sprint("config file specifies nonexistent static directory",
                error=True)

if not os.path.isdir(dropbox_dir):
    _f = True
    util.sprint("config file specifies nonexistent dropbox directory",
                error=True)

if _f: sys.exit(util.ERR_BAD_CONFIG)
