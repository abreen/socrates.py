import configparser
import os
import inspect

import util


SOCRATES_CONFIG = 'socrates.ini'

# the current working directory at the time socrates started
_cwd = os.getcwd()

# the absolute path to this config.py file while running
_conf = os.path.abspath(inspect.getfile(inspect.currentframe()))

# SOCRATES_DIR should contain the running socrates.py file
SOCRATES_DIR, _ = os.path.split(_conf)


# set default values
static_dir = SOCRATES_DIR + os.sep + 'static'
dropbox_dir = SOCRATES_DIR + os.sep + 'dropbox'

if os.path.isfile(SOCRATES_CONFIG):
    _parser = configparser.ConfigParser()
    _parser.read(SOCRATES_CONFIG)

    if 'socrates' not in _parser:
        util.sprint("warning: found config file, but it seems empty")
    else:
        _opts = _parser['socrates']

        if 'static_dir' in _opts:
            static_dir = _opts['static_dir']
            dropbox_dir = _opts['dropbox_dir']


if not os.path.isdir(static_dir):
    util.sprint("creating empty static files directory "
                "at '{}'".format(static_dir))
    os.mkdir(static_dir)

if not os.path.isdir(dropbox_dir):
    util.sprint("creating empty dropbox directory "
                "at '{}'".format(dropbox_dir))
    os.mkdir(dropbox_dir)
