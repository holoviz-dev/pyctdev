import warnings
import configparser

toxconf = configparser.ConfigParser()
toxconf.read('tox.ini')

if len(toxconf.sections()) == 0:
    warnings.warn("Could not read tox.ini; will use defaults (some commands may be unavailable and/or incorrect for your project).")
    # TODO: actually, things just won't work. Should we have a default
    # tox.ini in pyct? Or require projects to have a tox.ini (which
    # would force them to declare what tests there are, and how to run
    # them).

def get_tox_cmds(env):
    return toxconf[env]['commands'].splitlines()
