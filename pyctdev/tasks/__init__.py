"""
The basic types of task that pyctdev knows about.

E.g. building docs, generating packages, running tests
"""

import os

import param

from ..util import log_message, log_warning
from ..util.faketox import TOX_INI
from ..util.setuptools import SETUP_CFG

task_handlers = {}
support_tasks = {}

##################################################

# Interface? And where to put it? This and the register
# stuff should be elsewhere. task.py?


class PyctdevTask:
    params = []
    required_files = []


class ProjectTask(PyctdevTask):
    """
    Requires project-specific files.
    """
    required_files = [TOX_INI, SETUP_CFG]


def concrete_tasks():
    d = param.concrete_descendents(PyctdevTask)
    del d['PyctdevTask']
    del d['ProjectTask']
    return d.values()

##################################################


# TODO: these params are probably specific to nbsite
class build_docs(ProjectTask):
    """Build project's docs."""
    params = ['org', 'repo']


class list_test_envs(ProjectTask):
    """List all available test envs"""


class env_capture(PyctdevTask):
    """Report all information required to recreate current environment"""


# class ecosystem_setup(PyctdevTask):
#    """Whatever's required to configure build tools etc so they are in expected state. Build tools etc are optional dependencies of pyctdev, so depending what happened at install time..."""


class develop_test(ProjectTask):
    """Run specified tests in current environment"""
    params = ['test_group', 'test_requires', 'test_what']


class develop_install(ProjectTask):
    """python develop install with specified optional groups of dependencies.

    Typically ``pip install -e .[tests]`` but where dependencies are installed with ecosystem's package manager (e.g. conda).

    E.g.

    ``doit develop_install --channel conda-forge``

    ``doit develop_install --extra examples --extra tests``
    ``doit develop_install --all-extras``

    """
    params = ['extra', 'channel', 'all_extras']


class env_dependency_graph(PyctdevTask):
    """Write out dependency graph of named environment"""
    params = ['env_name', 'with_graphviz']


class env_export(PyctdevTask):
    """Turn an existing, installed environment into an environment specification, filtering against project's specified dependencies"""
    # TODO: filtering doc/param?
    # TODO required_params = ['env_name']


class env_file_generate(ProjectTask):
    """Create an environment specification from info declared in project's setup.py/setup.cfg"""
    # TODO required params?


# TODO: conda is missing a create env command that's ok with an env
# existing ? what about pip?
class env_create(PyctdevTask):
    """create named environment if it doesn't already exist.

    env will be empty except for python and pyctdev+deps.
    """


class package_test(ProjectTask):
    params = ['channel',
              'test_python',
              'test_group',
              'test_requires']


class package_build(ProjectTask):
    params = ['channel',
              'pin_deps',
              'pin_deps_as_env']


class package_upload(ProjectTask):
    params = ['password', 'user']


############################################################
############################################################

# TODO register/register_support was an experiment. Needs cleaning
# up/replacing in future.

# TODO: repeated code register vs register_support

def register_support(ecosystem, x):
    if ecosystem not in support_tasks:
        #log_message("New ecosystem registered: %s", ecosystem)
        support_tasks[ecosystem] = {}

    assert x.__name__ not in support_tasks[ecosystem]
    support_tasks[ecosystem][x.__name__] = x
    # hmm
    x._ecosystem = ecosystem


def register(ecosystem, x):
    # or however I should do file exists
    missing_files = [
        f for f in x.task_type.required_files if not os.path.exists(f)]
    if missing_files:
        log_warning(
            "Task type '%s' not available because the following files are missing in %s: %s",
            x.task_type.__name__,
            os.getcwd(),
            missing_files)
        return

    if ecosystem not in task_handlers:
        log_message("New ecosystem registered: %s", ecosystem)
        task_handlers[ecosystem] = {}
    if x.task_type in task_handlers[ecosystem]:
        log_message("Replacing %s's existing handler for %s (%s -> %s)",
                    ecosystem,
                    x.task_type.__name__,
                    task_handlers[ecosystem][x.task_type],
                    x.task_type)
    task_handlers[ecosystem][x.task_type] = x

    # hmm
    x._ecosystem = ecosystem


def get_task(ecosystem, task_type):
    tname = task_type.__name__
    ecosystem_available = ecosystem in task_handlers
    if not ecosystem_available:
        log_message(
            "Requested ecosystem %s but not available (forgot to load it?)" %
            ecosystem)
    # TODO: refactor a bit
    if ecosystem_available and task_type in task_handlers[ecosystem]:
        log_message("Task '%s' supplied by ecosystem '%s'", tname, ecosystem)
        return tname, task_handlers[ecosystem][task_type]
    elif ecosystem_available and task_type in task_handlers['universal']:
        log_message("Task '%s' supplied by ecosystem '%s'", tname, 'universal')
        return tname, task_handlers['universal'][task_type]
    else:
        log_message("Task '%s' not available from ecosystems %s",
                    tname, list(task_handlers.keys()))
        return tname, None


def get_tasks(ecosystem):
    t = dict(support_tasks.get(ecosystem, {}))
    for task_type in concrete_tasks():
        tname, tfn = get_task(ecosystem, task_type)
        if tfn is not None:
            t[tname] = tfn
    return t
