DOIT_CONFIG = {
    'verbosity': 2,
    'backend': 'sqlite3',
}

import os

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

from doit import get_var

from .util import get_tox_cmds

# doit bug in 0.29, which is last version to support py27
try:
    get_var("ecosystem")
except AttributeError:
    from doit import doit_cmd
    doit_cmd.reset_vars()
    del doit_cmd

# TODO: one day might have more sophisticated backend management...
ecosystem = get_var("ecosystem",os.getenv("PYCT_ECOSYSTEM","pip"))
if ecosystem == 'pip':
    from ._pip import * # noqa: api
elif ecosystem == 'conda':
    from ._conda import * # noqa: api


############################################################
# COMMON TASKS


########## TESTING ##########

def task_test_flakes():
    """Check for flakes (typically python module and notebooks)."""
    return {'actions': get_tox_cmds("testenv:flakes")}

def task_test_unit():
    """Run core unit tests; should always pass everywhere."""
    return {'actions': get_tox_cmds("testenv")}

def task_test_examples_quick():
    """Run quick examples.

    'quick' examples usually specified in project's
    examples/conftest.py.

    """
    return {'actions': get_tox_cmds("testenv:examples_quick")}

def task_test_examples():
    """Run examples (likely to be time/memory consuming)

    'examples' usually defined in project's examples/conftest.py.

    """
    # TODO: depend on download data task
    return {'actions': get_tox_cmds("testenv:examples")}


# TODO: add support for testing different environments e.g.  different
# sets of dependencies (envs read from tox)

## groups of tests (TODO: duplicating tox.ini)

def task_test_quick():
    """Run quick tests"""
    return {'actions': [],
            'task_dep': ["test_flakes","test_unit","test_examples_quick"]}


def task_test_all():
    """flake tests, unit tests, examples"""
    return {'actions': [],
            'task_dep': ['test_flakes','test_unit','test_examples']}



########## DOCS ##########

def task_build_docs():
    """build docs"""

    # TODO: these should be required when figure out dodo params
    org = { 'name':'org',
            'long':'org',
            'type':str,
            'default':'' }
    repo = { 'name':'repo',
             'long':'repo',
             'type':str,
             'default':'' }

    return {
        'params': [org, repo],
        'actions': [
            'nbsite_nbpagebuild.py %(org)s %s(repo)s ./examples ./doc',
            'sphinx-build -b html ./doc ./doc/_build/html',
            'nbsite_fix_links.py ./doc/_build/html',
            'touch ./doc/_build/html/.nojekyll',
            'nbsite_cleandisthtml.py ./doc/_build/html take_a_chance'
        ]
    }
