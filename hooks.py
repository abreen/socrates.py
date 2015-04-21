import util
import config

_triggers = ['before_file_search', 'before_exit']
_hooks = {}
_hooks_done = {}

for t in _triggers:
    _hooks[t] = []
    _hooks_done[t] = []


def load_from_dict(dict_):
    from os.path import isfile, sep
    global _triggers, _hooks

    if 'hooks' not in dict_:
        return

    for trigger, fnames in dict_['hooks'].items():
        if trigger not in _triggers:
            raise ValueError("unknown trigger: '" + str(trigger) + "'")

        for fname in fnames:
            if fname in _hooks[trigger]:
                raise ValueError("duplicate hook: '" + str(fname) + "'")

            if not isfile(config.hooks_dir + sep + fname):
                util.warning("could not find hook file: '" + \
                             str(fname) + "'")

            _hooks[trigger].append(fname)


def run_hooks_for(trigger):
    from sys import exit
    from os.path import sep
    from subprocess import call
    global _triggers

    if trigger not in _triggers:
        raise ValueError("unknown trigger: '" + str(trigger) + "'")

    hooks = list(set(_hooks[trigger]) - set(_hooks_done[trigger]))
    num_done = 0

    if len(hooks) > 0:
        util.info("running hooks for trigger '" + str(trigger) + "'")

        for fname in hooks:
            rv = call(config.hooks_dir + sep + fname, env=_create_env())
            _hooks_done[trigger].append(fname)
            num_done += 1

            if rv != 0:
                util.error("hook '" + str(fname) + "' exited abnormally")
                util.exit(util.ERR_ABNORMAL_HOOK_EXIT)

        util.info("successfully ran " + str(num_done) + " " + \
                  util.plural('hook', num_done))


def _create_env():
    return {'SOCRATES_DIR': config.SOCRATES_DIR,
            'SOCRATES_CONFIG_PATH': config.SOCRATES_CONFIG,
            'SOCRATES_HOOKS_DIR': config.hooks_dir,
            'SOCRATES_STATIC_DIR': config.static_dir,
            'SOCRATES_DROPBOX_DIR': config.dropbox_dir,
            'SOCRATES_CRITERIA_DIR': config.criteria_dir}
