from doit.action import CmdAction

from .util import _options_param

# util stuff

def _pip_install_with_options(options):
    cmd = "pip install -e ."
    if len(options)>0:
        cmd+="[%s]"%(",".join(options))
    return cmd



############################################################
# TASKS...


########## MISC ##########

def task_env_capture():
    """Report all information required to recreate current environment."""
    return {'actions':["pip freeze"]} # TODO: and...


########## PACKAGING ##########


def task_package_build():
    """Build pip package, then install and test all_quick in venv"""
    return {'actions': ['tox -e all_quick']}

def task_package_upload():
    """TODO: currently using travis integration"""
    return {'actions':[]}    




########## FOR DEVELOPERS ##########


def task_env_create():
    """TODO: create named environment if it doesn't already exist.

    Note: environment will be created in empty state; use
    develop_install_... commands to update it.

    """
    return {'actions':[]}


def task_develop_install():
    """python develop install with specified optional groups of dependencies.
    
    Typically ``pip install -e .[tests]``. 

    Pass --options multiple times to specify other optional groups
    (see project's setup.py for available options).

    E.g. 

    ``doit develop_install -o examples -o tests``
    ``doit develop_install -o all``

    """
    return {'actions': [CmdAction(_pip_install_with_options)],
            'params':[_options_param]}

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
