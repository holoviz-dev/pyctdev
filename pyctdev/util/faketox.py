"""tox.ini reading hacks

Can use this file even if tox cannot be installed (e.g. conda defaults
users).

"""

import sys
import os
try:
    import configparser
except ImportError:
    # python2 (also prevents dict-like access)
    import ConfigParser as configparser

from . import log_message, log_warning, getpy

# Fallbacks for conda, which can't install tox from defaults (at
# least, not as of June 2018). Allows to parse tox.ini (i.e. to use
# tox.ini as single place where all test cmds and envs are stored)
try:
    import tox.config as tox_config
    _tox = 'external'
except BaseException:
    for pkg in ('tox-3.0.0.zip', 'virtualenv-15.2.0.zip'):
        sys.path.append(os.path.join(
            os.path.dirname(__file__), '_vendor', pkg))
    import tox.config as tox_config
    _tox = 'internal'

log_message(
    "tox.config from %s (i.e. using %s tox)",
    tox_config.__file__,
    _tox)


TOX_INI = 'tox.ini'  # aka TEST_CONFIG or something like that


def get_conf(pre=False):
    """Read tox config.

    If pre is True, will read using config parser instead of the
    default tox parser (e.g. to allow some preprocessing).

    """
    if not os.path.isfile(TOX_INI):
        log_warning(
            "No tox.ini in %s; test commands will be unavailable",
            os.getcwd())
        return {}

    if pre is True:  # sigh
        # we later filter out any _onlytox commands...
        toxconf_pre = configparser.ConfigParser()
        toxconf_pre.read(TOX_INI)
        log_message("Using %s read via configparser", os.path.abspath(TOX_INI))
        return toxconf_pre
    else:
        toxconf = tox_config.parseconfig('tox')
        log_message("Using %s at %s read via tox.config", TOX_INI, toxconf.toxinipath)
        return toxconf


onlytox = '{[_onlytox]commands}'


def get_env(test_python, test_group, test_requires, test_what):
    if test_python == '':
        test_python = getpy()
    return "%s-%s-%s-%s" % (test_python, test_group, test_requires, test_what)

def get_python(env):
    toxconf = get_conf()
    if env in toxconf.envconfigs:
        # TODO really doubt this is the right way
        return toxconf.envconfigs[env].basepython.split("python")[1]
    else:
        raise ValueError("Could not find %s in %s" % (env, TOX_INI))


def get_cmds(env):
    toxconf = get_conf()
    toxconf_pre = get_conf(pre=True)
    if env in toxconf.envconfigs:
        toxpre = toxconf_pre['testenv']['commands'].splitlines()
        # skip all "onlytox" commands
        i = 0 if not toxpre[0].startswith(onlytox) else len(
            toxconf_pre['_onlytox']['commands'].splitlines())
        for c in toxpre[1::]:
            assert not c.startswith(
                onlytox), "Bad tox config: only first command can be 'onlytox' skipped"
        cmds = []
        for cmd in toxconf.envconfigs[env].commands[i::]:
            if len(cmd) > 0:
                # can't quote first on win (need to quote rest...a list would
                # be better than string - should clean up
                cmds.append(
                    "%s " % cmd[0] + " ".join(['"{0}"'.format(w) for w in cmd[1::]]))
        return cmds
    else:
        raise ValueError(
            "Could not find '%s' in %s" %
            (env, os.path.abspath(TOX_INI)))


def get_deps(env):
    """Return list of tox-only deps

    E.g. for  deps = .[tests,examples]
                     yaml

    would return just yaml
    """
    log_message(
        "Getting additional --test-requires dependencies from '%s' in %s...", env, TOX_INI)
    toxconf = get_conf()

    if env not in toxconf.envconfigs:
        raise ValueError("Could not find %s in %s" % (env, os.path.abspath(TOX_INI))) # can't i just abspath once at the beginning?
    
    deps = toxconf.envconfigs[env].deps
    deps2use = []
    for d in deps: # scary hacks...
        if '.[' in d.name:
            pass  # only tox dependencies - not from setup.py
        elif d.name == '.': # TODO
            assert False  # expecting this to never happen
        else:
            deps2use.append(d.name)
    log_message("...additional dependencies: %s", deps2use)
    return deps2use


def get_docs():
    things = {}
    toxconf = get_conf(pre=True)
    # not sure how I was supposed to do this (gets all, flakes, unit, etc...)
    if 'tox' not in toxconf:
        return ""  # TODO hack for supporting no tox.ini
    for t in toxconf['tox']['envlist'].split('-')[1][1:-1].split(','):
        doc = 'Run "%s" tests (see tox.ini for commands)' % t
        if '_' + t in toxconf:
            desc = toxconf['_' + t].get("description")
            things[t] = desc if desc else ""
    doc = "".join([" * %s: %s\n" % (t, v) for t, v in things.items()])
    return doc


def print_envs():
    """supposed to be like tox -l"""
    # TODO: don't know if tox -l does any ordering, etc
    for e in get_conf().envlist:
        print(e)
