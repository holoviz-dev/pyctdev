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

# TODO: what to call it? (match 'ecosystem' argument)
def task_ecosystem_setup():
    """Common pip setup

    Updates to latest pip; adds tox, twine, and wheel.
    """
    return {'actions': ["pip install --upgrade pip",
                        "pip install tox twine wheel"]}


########## PACKAGING ##########



def task_package_build():
    """Build pip package, then install and test all_quick in venv"""

    formats_param = {
        'name':'formats',
        'long':'formats',
        'type':str,
        'default':'sdist --formats=zip bdist_wheel'
    }
    
    # TODO: would be able to use the packages created by tox if
    # https://github.com/tox-dev/tox/issues/232 were done    
    return {'actions': ['tox -e all_quick',
                        'python setup.py %(formats)s'],
            'params': [formats_param]}

def task_package_upload():
    """Upload pip packages to pypi"""

    # TODO: make required
    username = {
        'name':'username',
        'long':'username',
        'short': 'u',
        'type':str,
        'default':''
    }
    password = {
        'name':'password',
        'long':'password',
        'short': 'p',
        'type':str,
        'default':''
    }

    repository_url = {
        'name':'repository-url',
        'long':'repository-url',
        'short': 'r',
        'type':str,
        'default':'https://test.pypi.org/legacy/'
    }

    # TODO: uploading everything in dist is a bad idea; fix with tox
    # #232 (mentioned above).
    return {'actions':['twine upload -u %(username)s -p %(password)s --repository-url=%(repository-url)s dist/*'],
            'params': [username,password,repository_url]}




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
