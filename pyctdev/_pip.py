# TODO: should probably use tox --recreate because currently
# pip+tox not necessarily sync'ing env changes properly.

from doit.action import CmdAction

from .util import _options_param, test_group, get_env, test_python, test_requires, pkg_tests, test_matrix, echo

# TODO: move tasks to pip.py and leave hacks here.

# util stuff

PYPI_CHANNELS = {
    'pypi': 'https://pypi.org/simple',
    'testpypi': 'https://test.pypi.org/simple'
}

_channel_param = {
    'name':'channel',
    'long':'channel',
    'short': 'c',
    'type':list,
    'default':[] # note: no channel means user's defaults (typically
                 # pypi.org)...is that what we want?
}

def _pip_install_with_options(options,channel):
    cmd = "pip install --upgrade " 

    if 'testpypi' in channel:
        # note: should pre always be used maybe? Or more likely,
        # should pre be separately configurable?
        cmd += "--pre "

    # note: like for conda, "defaults" is always there in a slightly
    # complicated way...we could change this to make it simpler
    # e.g. have [defaults] by default, and if you override you need to
    # specify all (including defalts somewhere, if you do want
    # that...) TODO: need to decide a policy
    if len(channel)==0:
        channel = ['pypi']
    if 'pypi' not in channel:
        channel.append('pypi')

    servers = [PYPI_CHANNELS[c] for c in channel]

    cmd += "--index-url=%s "%servers[0]

    cmd += " ".join(['--extra-index-url=%s '%server for server in servers[1::]])

    cmd += "-e ."
    
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

    Updates to latest pip, tox, twine, and wheel.
    """
    # TODO: will need to become something like the following w/ pip10
    # d:\python36\python.exe -m pip install --upgrade pip tox twine wheel
    return {'actions': ["pip install --upgrade pip tox twine wheel"]}


########## PACKAGING ##########



def task_package_build():
    """Build pip package, then install and test all_quick (or other
    specified env) in venv

    E.g. 

    ``doit package_build --formats=bdist_wheel``
    ``doit package_build -e all_quick-Ewith_numpy``

    """

    formats_param = {
        'name':'formats',
        'long':'formats',
        'type':str,
        'default':'sdist --formats=zip bdist_wheel --universal'
    }
    # TODO: missing support for pypi channels
    
    def thing(test_group,test_python,test_requires,pkg_tests):
        if pkg_tests:
            enviros = []
            for (p,g,r,w) in test_matrix(test_python,test_group,test_requires,['pkg']):
                enviros.append( get_env(p,g,r,w) )
            return 'python -m tox -e ' + ' , '.join(enviros)
        else:
            return echo("no tests")

    # TODO: would be able to use the packages created by tox if
    # https://github.com/tox-dev/tox/issues/232 were done    
    return {'actions': [CmdAction(thing),
                        'python setup.py %(formats)s'],
            'params': [formats_param,test_group,test_python,test_requires,pkg_tests]}

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

    Pass --channel multiple times to specify other pypi servers.

    E.g. 

    ``doit develop_install -o examples -o tests``
    ``doit develop_install -o all``
    ``doit develop_install -c testpypi -c pypi``

    """
    return {'actions': [CmdAction(_pip_install_with_options)],
            'params':[_options_param,_channel_param]}

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


def task_env_export():
    """TODO"""
    return {'actions':[]}
