import util
import config

_triggers = ['before_file_search', 'before_exit']
_hooks = {}

for t in _triggers:
    _hooks[t] = []


def load_from_dict(dict_):
    from os.path import isfile, sep
    global _triggers, _hooks

    if 'hooks' not in dict_:
        return

    for trigger, fnames in dict_['hooks'].items():
        if trigger not in _triggers:
            raise ValueError("unknown trigger: '" + str(trigger) + "'")

        for fname in fnames:
            if not isfile(config.hooks_dir + sep + fname):
                raise ValueError("could not find hook file: '" + \
                                 str(fname) + "'")

            _hooks[trigger].append(fname)


def run_hooks_for(trigger):
    from sys import exit
    from os.path import sep
    from subprocess import call
    global _triggers

    if trigger not in _triggers:
        raise ValueError("unknown trigger: '" + str(trigger) + "'")

    num_hooks = len(_hooks[trigger])

    if num_hooks > 0:
        util.info("running hooks for trigger '" + str(trigger) + "'...")

        for fname in _hooks[trigger]:
            if call(config.hooks_dir + sep + fname, env=_create_env()) != 0:
                util.error("hook '" + str(fname) + "' exited abnormally")
                util.exit(util.ERR_ABNORMAL_HOOK_EXIT)

        util.info("successfully ran " + str(num_hooks) + " " + \
                    util.plural('hook', num_hooks))


def _create_env():
    return {'SOCRATES_DIR': config.SOCRATES_DIR,
            'SOCRATES_CONFIG_PATH': config.SOCRATES_CONFIG,
            'SOCRATES_HOOKS_DIR': config.hooks_dir,
            'SOCRATES_STATIC_DIR': config.static_dir,
            'SOCRATES_DROPBOX_DIR': config.dropbox_dir,
            'SOCRATES_CRITERIA_DIR': config.criteria_dir}
