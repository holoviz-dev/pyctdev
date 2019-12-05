"""
parameters/options that apply to multiple tasks

Notes:

  * default of NotImplemented means a value is required at the command line

"""

from .util.setuptools import SETUP_CFG
from .util.faketox import TOX_INI

# TODO: why've you used NotImplemented rather than None?
# (Because None could be a valid default.)

##################################################
# common options

# TODO: rename?
env_file = {
    'name': 'env_file',
    'long': 'env-file',
    'type': str,
    'default': NotImplemented,
    'help': 'Path to environment file (e.g. environment.yaml).'
}


extra = {
    'name': 'extra',
    'long': 'extra',
    'type': list,
    'default': [],
    'help': 'Name of optional extra (i.e. group of optional dependencies). Extras are defined in %s. Specify multiple times for multiple extras.' % SETUP_CFG
}

all_extras = {
    'name': 'all_extras',
    'long': 'all-extras',
    'type': bool,
    'default': False,
    'help': 'Specify all extras (see "extra" for more info).'
}

# TODO: should make python & test-python simpler/clearer.

python = {'name': 'python',
          'long': 'python',
          'type': str,
          'default': NotImplemented,
          'help': 'Specify a version of python. E.g. for a conda-based command, might be "3.6".'}


# TODO: could do with renaming. And simplifying. Are they all necessary. At least make it clear what they are all for.
# ? test_group:
# ? test_requires: --test-in-presence-of ?? (this is names of packages...does it get translated to conda too?)
# ? test_what:
_test_matrix = 'Forms part of "test matrix": test_python, test_group, test_requires, test_what.'

test_python = {
    'name': 'test_python',
    'long': 'test-python',
    'type': list,
    'default': [],
    'help': 'Version of python with which to run tests. Must be as listed in %s, e.g. likely to be py27 or py36 etc. Specify multiple times for multiple pythons.' % TOX_INI + _test_matrix
}

test_group = {
    'name': 'test_group',
    'long': 'test-group',
    'type': list,
    'default': [],
    'help': 'Which group of tests to run. Must be as listed in %s, e.g. likely to include "unit", "flakes", etc. Specify multiple times for multiple groups.' % TOX_INI + _test_matrix
}

test_requires = {
    'name': 'test_requires',
    'long': 'test-requires',
    'type': list,
    'default': [],
    'help': 'Additional packages that should be present during testing, e.g. to check there is no conflict/malfunction when that package is present. Must be listed in %s. Specify multiple times for multiple packages.' % TOX_INI + _test_matrix
}

test_what = {
    'name': 'test_what',
    'long': 'test-what',
    'type': list,
    'default': [],
    'help': 'Optional extra test specifications, e.g. commands to run. Must be defined and used in %s. E.g. "pkg" might be extra commands that apply to packages only. Can specify multiple times.' % TOX_INI + _test_matrix
}


user = {
    'name': 'user',
    'long': 'user',
    'type': str,
    'default': NotImplemented,
    'help': 'Task requires a user name.'
}

password = {
    'name': 'password',
    'long': 'password',
    'type': str,
    'default': NotImplemented,
    'help': 'Task requires a password or token. Note: for anconda.org, supply the token here.'
}

force = {
    'name': 'force',
    'long': 'force',
    'type': bool,
    'default': False,
    # TODO: tasks could copy param defn and update help
    'help': "Will overwrite existing things - be careful. To see exactly what it does for a particular command, you'll have to check the task source :("
}


channel = {
    'name': 'channel',
    'long': 'channel',
    'short': 'c',
    'type': list,
    # TODO: probably drop channels for pypi or make configurable for people
    # using their own server
    'help': 'One or more conda channels (or pip pypi server names) to use beyond the default. conda channels are things like conda-forge, pyviz, etc. pip "channels" are are pypi or testpypi.',
    'default': []
}


##################################################
##################################################

env_name = {
    'name': 'env_name',
    'long': 'env-name',
    'type': str,
    'default': NotImplemented,
    'help': "Name of environment (required)."}

env_name_override = {
    'name': 'env_name_override',
    'long': 'env-name-override',
    'type': str,
    'default': None,
    'help': "Typically the active environment is used, but supply a different name here if desired"}

advert = {
    'name': 'advert',
    'long': 'advert',
    'type': bool,
    'default': True,
    'inverse': 'no-advert',
    'help': 'Whether to inject advert for pyctdev into generated files.'
}


package = {'name': 'package',
           'long': 'package',
           'type': list,
           'default': [],  # hmm, default=[] means all
           'help': 'Which package definitions (from %s) to use. If not specified, defaults to all available. Specify multiple times for multiple packages.' % SETUP_CFG}


pin_deps = {
    'name': 'pin_deps',
    'long': 'pin-deps',
    'type': bool,
    'default': False,
    'help': 'Pin dependencies to the versions specified in %s.' % SETUP_CFG
}

pin_deps_as_env = {
    'name': 'pin_deps_as_env',
    'long': 'pin-deps-as-env',
    'type': str,
    'default': None,
    'help': 'Pin dependencies to the versions currently installed in the specified environment.'}

add_pyctdev = {
    'name': 'add_pyctdev',
    'long': 'add-pyctdev',
    'type': bool,
    'default': False,
    'help': 'Also install pyctdev into env (could be useful for stacked envs)'}

##################################################
##################################################


sdist = {
    'name': 'sdist',
    'long': 'sdist',
    'type': bool,
    'default': False,
    'inverse': 'no-sdist',
    'help': 'Do sdist rather than wheel (e.g. during build, test, or upload). Note: it is wheel OR sdist in any run (i.e. mutually exclusive). Only tar.gz currently supported fo rsdist.'
}


##################################################
##################################################


# TODO: figure out what to do about these

purge = {
    'name': 'purge',
    'long': 'purge',
    'type': bool,
    'default': False,
    'help': 'Whether to clean up work and intermediate files (e.g. for conda: conda build purge).'
}

cleanup_param = {
    'name': 'cleanup',
    'long': 'cleanup',
    'type': bool,
    'default': True,
    'inverse': 'no-cleanup'
}

cleanup_meta_param = {
    'name': 'cleanup_meta',
    'long': 'cleanup-meta',
    'type': bool,
    'default': True,
    'inverse': 'no-cleanup-meta'
}
