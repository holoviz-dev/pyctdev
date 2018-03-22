# Note: work in progress. Contains history of learning dodo. Many
# tasks need improving. Just trying to collect/support everything
# in one place to start off with...

# TODO: decide what to do about config. E.g. could use individual tool
# bits from setup.cfg, could have own config, could have no config,
# ...

# TODO: add docs about tasks that must be run with the python you
# intend...

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

import platform
import os
import sys
try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve

DOIT_CONFIG = {
    'verbosity': 2,
    'backend': 'sqlite3',
}


from _conda import *


def task_build_pip_package():
    """(not yet implemented; currently using travis integration)"""
    return {'actions':[]}
    
def task_capture_env():
    """ """
    return {'actions':["pip freeze"]}

def task_develop_install():
    """Python develop install"""
    return {'actions':["pip install -e ."]}


# TODO: merge with tox? can't use tox alone because of conda. Or drop tox?
def task_unit_tests():
    def thing(testrunner):
        if testrunner == 'nose':
            # TODO: should be nosetests (with options in project setup.cfg)
            cmd = 'nosetests --verbose --nologcapture --with-doctest'
        elif testrunner == 'pytest':
            cmd = 'pytest'
        else:
            raise ValueError("Need to add support for %s in pyct"%testrunner)
        return cmd

    testrunner = {
        'name':'testrunner',
        'long':'testrunner',
        'short':'t',
        'type':str,
        'default':'pytest'}

    return {'actions': [CmdAction(thing)],
            'params': [testrunner]}

#def task_all_tests():
#    return {'actions': [],
#            'task_dep': ['unit_tests','lint']}

def task_lint():
    return {'actions': ['flake8']}


# TODO: -k examples is to avoid running all the other tests as well if
# --pyargs module is used as the default action (via setup.cfg)
# because passing explicit list of files does not override that
# option. Might be better to do use pytest markers?  I.e. to have
# groups of tests, like "unit", "slow", maybe, or
# "examples"/"notebooks". Need to investigate.
def task_nb_lint():
    return {'actions': ['pytest --nbsmoke-lint -k "examples" examples/**/*.ipynb']}

def task_nb_tests():
    return {'actions': ['pytest --nbsmoke-run -k "examples" examples/**/*.ipynb']}

# TODO: 'nb verify' (links? see datashader and/or bokeh)
