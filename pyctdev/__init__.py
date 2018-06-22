# TODO: various hacks to fix are && join cmds, quoting, default param
# value for list (or at least move to issues)

# TODO: whether to include any tests (and tests requires) in our projects'
# conda recipes (or just use package_build's testing).

DOIT_CONFIG = {
    'verbosity': 2,
    'backend': 'sqlite3',
}

import os
import configparser

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

from doit import get_var
from doit.action import CmdAction

###
# until https://github.com/tox-dev/tox/issues/850 is in a tox release, make
# sure we'll import our unreleased copy of tox.
import sys
sys.path.insert(1,os.path.join(os.path.dirname(__file__),"_vendor","tox-pep-518.zip"))
###

from .util import get_tox_cmds, test_requires, get_env, test_what

# doit bug in 0.29, which is last version to support py27
try:
    get_var("ecosystem")
except AttributeError:
    from doit import doit_cmd
    doit_cmd.reset_vars()
    del doit_cmd

# TODO: one day might have more sophisticated backend management...
ecosystem = get_var("ecosystem",os.getenv("PYCTDEV_ECOSYSTEM","pip"))
if ecosystem == 'pip':
    from ._pip import * # noqa: api
elif ecosystem == 'conda':
    from ._conda import * # noqa: api

# TODO: support some limited form of dry run (but should be at doit
# level)
# action that just prepends echo to command, does "echo calling fn %s"%fn_name for pyfunc, etc, ...
#dryrun = get_var("dryrun",False)


############################################################
# COMMON TASKS

def task_list_envs():
    return {'actions': ['tox -l']}

########## TESTING ##########

def task_test():
    class thing:
        def __init__(self,group):
            self.group=group
        def __call__(self,test_requires,test_what):
            cmds = []
            # TODO: use test_matrix
            for r in (test_requires if len(test_requires)>0 else ['default']):
                for w in (test_what if len(test_what)>0 else ['dev']):
                    environment = get_env('',self.group,r,w)
                    cmds += get_tox_cmds(environment)
            # hack to support multiple commands :(
            return " && ".join(cmds)

    # read the possibilities from tox.ini, but could instead have standard ones
    # as a way of suggesting what projects should make available 
    toxconf = configparser.ConfigParser()
    toxconf.read('tox.ini')
    # not sure how I was supposed to do this (gets all, flakes, unit, etc...)
    for t in toxconf['tox']['envlist'].split('-')[1][1:-1].split(','):
        doc = 'Run "%s" tests (see tox.ini for commands)'%t
        if '_'+t in toxconf:
            desc = toxconf['_'+t].get("description")
            if desc is not None:
                doc = desc
            
        yield {'actions':[CmdAction(thing(t))],
               'doc':doc,
               'basename': 'test_'+t,
               'params':[test_requires,test_what]}


# note: groups of tests with doit would be more flexible, but would
# duplicate tox


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
            'nbsite_nbpagebuild.py %(org)s %(repo)s ./examples ./docs',
            'sphinx-build -b html ./docs ./docs/_build/html',
            'nbsite_fix_links.py ./docs/_build/html',
            'touch ./docs/_build/html/.nojekyll',
            'nbsite_cleandisthtml.py ./docs/_build/html take_a_chance'
        ]
    }
