# TODO: should probably use tox --recreate because currently
# pip+tox not necessarily sync'ing env changes properly.

# TODO: missing test package task for pip. Current workaround is build package each time.

import warnings

from doit.action import CmdAction

from .util import _options_param, test_group, get_env, test_python, test_requires, pkg_tests, test_matrix, echo, get_buildreqs

# TODO: move tasks to pip.py and leave hacks here.

# util stuff

PYPI_CHANNELS = {
    'pypi': 'https://pypi.org/simple',
    'testpypi': 'https://test.pypi.org/simple'
}

PYPI_UPLOAD_URLS = {
    'pypi': 'https://upload.pypi.org/legacy/',
    'testpypi': "https://test.pypi.org/legacy/"
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

    sdist_install_build_deps_param = {
        'name': 'sdist_install_build_deps',
        'long': 'sdist-install-build-deps',
        'type': bool,
        'default': False,
    }

    sdist_run_tests_param = {
        'name': 'sdist_run_tests',
        'long': 'sdist-run-tests',
        'type': bool,
        'default': False,
    }

    # TODO: should be called commands or similar
    formats_param = {
        'name':'formats',
        'long':'formats',
        'type':str,
        'default':'sdist --formats=gztar bdist_wheel --universal'
    }
    # TODO: missing support for pypi channels
    
    def thing(test_group,test_python,test_requires,pkg_tests,sdist=False):
        if pkg_tests:
            enviros = []
            for (p,g,r,w) in test_matrix(test_python,test_group,test_requires,['pkg']):
                enviros.append( get_env(p,g,r,w) )

            # i.e. for now, standard tox for sdist
            cmd = 'python -m pyctdev._vendor.tox_wrapper' if not sdist else 'python -m tox'
            return cmd + ' -e ' + ' , '.join(enviros)
        else:
            return echo("no tests")

    def wheel(test_group,test_python,test_requires,pkg_tests,formats):
        if 'wheel' in formats:
            return thing(test_group,test_python,test_requires,pkg_tests)
        else:
            return echo("no wheel")

    def sdist(test_group,test_python,test_requires,pkg_tests,formats,sdist_run_tests):
        if 'sdist' in formats:
            if sdist_run_tests:
                return thing(test_group,test_python,test_requires,pkg_tests,sdist=True)
            else:
                warnings.warn("You have requested to build an sdist. Unlike wheel, sdist will not be installed and tested by default. To also install and test sdist, specify --sdist-run-tests.")
                return echo("not running sdist tests")
        else:
            return echo("no sdist")
        
    def sdist_build_deps(formats,sdist_install_build_deps):
        if 'sdist' in formats:
            if not sdist_install_build_deps:
                warnings.warn("If the project for which you are building an sdist has build dependencies, you will need to install them yourself first or specify --sdist-install-build-deps to have them installed for you (which will permanently affect your current environment). This is a limitation of pip not yet supporting building of sdist; https://github.com/pypa/pip/issues/5407, https://github.com/pypa/pip/issues/5401")
                return echo("not installing sdist build deps")
            else:
                buildreqs = get_buildreqs()
                deps = " ".join('"%s"'%dep for dep in buildreqs)
                if len(buildreqs)>0:
                    return "pip install %s"%deps
                else:
                    return echo("no build deps")
        else:
            return echo("no sdist requested")


    # TODO: would be able to use the packages created by tox if
    # https://github.com/tox-dev/tox/issues/232 were done    
    return {'actions': [CmdAction(wheel),
                        CmdAction(sdist_build_deps),
                        CmdAction(sdist),
                        'python setup.py %(formats)s'],
            'params': [formats_param,test_group,test_python,test_requires,pkg_tests,sdist_run_tests_param,sdist_install_build_deps_param]}

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
        'name':'repository_url',
        'long':'repository-url',
        'short': 'r',
        'type':str,
        'default':''
    }
    
    pypi = {
        'name':'pypi',
        'long':'pypi',
        'type':str,
        'default':'testpypi'
    }

    def thing(username,password,repository_url,pypi):
        if repository_url!="":
            return 'twine upload -u %(username)s -p %(password)s --repository-url=%(repository_url)s dist/*'
        else:
            return 'twine upload -u %(username)s -p %(password)s --repository-url='+ PYPI_UPLOAD_URLS[pypi] +' dist/*'

    # TODO: uploading everything in dist is a bad idea; fix with tox
    # #232 (mentioned above).
    return {'actions':[CmdAction(thing)],
            'params': [username,password,repository_url,pypi]}




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
