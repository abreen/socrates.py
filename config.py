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
        util.sprint("warning: found config file, but it looks incomplete")

hooks_dir = _parser.get('socrates', 'hooks_dir',
                        fallback=SOCRATES_DIR + os.sep + 'hooks')
scripts_dir = _parser.get('socrates', 'scripts_dir',
                          fallback=SOCRATES_DIR + os.sep + 'scripts')
static_dir = _parser.get('socrates', 'static_dir',
                         fallback=SOCRATES_DIR + os.sep + 'static')
dropbox_dir = _parser.get('socrates', 'dropbox_dir',
                          fallback=SOCRATES_DIR + os.sep + 'dropbox')
criteria_dir = _parser.get('socrates', 'criteria_dir',
                           fallback=SOCRATES_DIR + os.sep + 'criteria')

from datetime import timedelta as _td
if _parser.has_option('socrates', 'grace_period'):
    _grace_str = _parser.get('socrates', 'grace_period')
    grace_period = _td(seconds=int(_grace_str))

else:
    grace_period = _td(seconds=0)


_f = False
if not os.path.isdir(hooks_dir):
    _f = True
    util.sprint("hooks directory does not exist or cannot be accessed",
                error=True)

if not os.path.isdir(scripts_dir):
    _f = True
    util.sprint("scripts directory does not exist or cannot be accessed",
                error=True)

if not os.path.isdir(static_dir):
    _f = True
    util.sprint("static directory does not exist or cannot be accessed",
                error=True)

if not os.path.isdir(dropbox_dir):
    _f = True
    util.sprint("dropbox directory does not exist or cannot be accessed",
                error=True)

if not os.path.isdir(criteria_dir):
    _f = True
    util.sprint("criteria directory does not exist or cannot be accessed",
                error=True)

if _f: sys.exit(util.ERR_BAD_CONFIG)
