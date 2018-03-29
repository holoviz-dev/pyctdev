# Note: work in progress. Contains history of learning dodo. Many
# tasks need improving. Just trying to collect/support everything
# in one place to start off with...


from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

from .util import get_tox_cmds
# TODO: consider having conda and pip backends, allowing someone to
# specify/set which one they want to use.
from ._conda import *  # noqa: api


DOIT_CONFIG = {
    'verbosity': 2,
    'backend': 'sqlite3',
}


########## MISC ##########

def task_env_capture():
    """Report all information required to recreate current environment."""
    return {'actions':["pip freeze"]} # TODO: and...


########## PACKAGING ##########


def task_package_build():
    """TODO: currently using travis integration"""
    return {'actions':[]}

def task_package_upload():
    """TODO: currently using travis integration"""
    return {'actions':[]}    


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

## groups of tests

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


########## FOR DEVELOPERS ##########


def task_env_create():
    """TODO: create named environment if it doesn't already exist.

    Note: environment will be created in empty state; use
    develop_install_... commands to update it.

    """
    return {'actions':[]}

# TODO: will become options of one task

def task_develop_install():
    """python develop install (pip install -e .[tests])"""
    return {'actions':["pip install -e .[tests]"]}

def task_develop_install_examples():
    """develop install with dependencies for examples"""
    return {'actions':["pip install -e .[tests, examples]"]}

def task_develop_install_docs():
    """develop install with dependencies for building docs"""
    return {'actions':["pip install -e .[docs, examples]"]}

def task_develop_install_all():
    """develop install with all dependencies"""
    return {'actions':["pip install -e .[all]"]}


## TODO: keep?
#
#py = {
#    'name':'py',
#    'long':'py',
#    'type':str,
#    'default':'36'
#}
#
#def task_test_develop():
#    """Test ``pip install -e .``"""
#    return {
#        'actions': ['tox -vv -e py%(py)s --develop'],
#        'params': [py]
#    }
