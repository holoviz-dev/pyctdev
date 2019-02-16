"""
"""
import os
import warnings

from ..util.setuptools import _get_setup_metadata, get_package_path
from ..util.pyproject import get_buildreqs
from ..util import echo, test_matrix, doithack_join_cmds, faketox, log_message

# TODO: hardcoded

PYPI_CHANNELS = {
    'pypi': 'https://pypi.org/simple',
    'testpypi': 'https://test.pypi.org/simple'
}

PYPI_UPLOAD_URLS = {
    'pypi': 'https://upload.pypi.org/legacy/',
    'testpypi': "https://test.pypi.org/legacy/"
}


# TODO: decide about pypi channels. Seems unimportant at first, but for
# use in closed env it's important.
def _pip_install_with_options(extra, channel, all_extras):
    cmd = "pip install --upgrade "

    if 'testpypi' in channel:
        # note: should pre always be used maybe? Or more likely,
        # should pre be separately configurable?
        cmd += "--pre "

    # note: like for conda, "defaults" is always there in a slightly
    # complicated way...we could change this to make it simpler
    # e.g. have [defaults] by default, and if you override you need to
    # specify all (including defalts somewhere, if you do want
    # that...)
    if len(channel) == 0:
        channel = ['pypi']
    if 'pypi' not in channel:
        channel.append('pypi')

    servers = [PYPI_CHANNELS[c] for c in channel]

    cmd += "--index-url=%s " % servers[0]

    cmd += " ".join(['--extra-index-url=%s ' %
                     server for server in servers[1::]])

    cmd += "-e ."

    if all_extras:
        meta = _get_setup_metadata()
        extra = set(meta.get('extras_require', {}))
        # don't know why I had this...
        #options = set(options).union(set(extras))

    if len(extra) > 0:
        cmd += "[%s]" % (",".join(extra))
    return cmd


def _twine_upload(user, password, pypi, sdist):
    pkg_file = get_package_path(sdist=sdist)
    return 'twine upload -u %(user)s -p %(password)s --repository-url=' + \
        PYPI_UPLOAD_URLS[pypi] + ' %s' % pkg_file


def _run_tox2(package_path, test_group, test_python, test_requires):
    enviros = []
    for (p, g, r, w) in test_matrix(
            test_python, test_group, test_requires, ['pkg']):
        enviros.append(faketox.get_env(p, g, r, w))

    cmd = 'python -m tox '
    cmds = [cmd + ' --version ']  # to know which tox
    # TODO: should be tied to pyctdev verbosity
    cmd += ' -vv '
    cmds += [cmd + ' --installpkg "%s" -e ' %
             package_path + ' , '.join(enviros)]
    return doithack_join_cmds(cmds)


# TODO: plus some cleanup params?
def test_package(test_python, test_requires, test_group, channel, sdist):
    pkg_file = get_package_path(sdist=sdist)
    return _run_tox2(pkg_file, test_group, test_python, test_requires)


def _maybe_sdist_build_deps(sdist, sdist_install_build_deps):
    if sdist:
        if not sdist_install_build_deps:
            warnings.warn("If the project (for which you are building an sdist) has build-time dependencies, you will need to specify --sdist-install-build-deps, or install them yourself first.")
            return echo("not installing sdist build deps")
        else:
            buildreqs = get_buildreqs()
            deps = " ".join('"%s"' % dep for dep in buildreqs)
            if len(buildreqs) > 0:
                return "pip install %s" % deps
            else:
                return echo("no build deps")
    else:
        return echo("no sdist requested")


def pkg_exists(task, values):
    pkg_file = get_package_path(sdist=task.options['sdist'])
    log_message("Would be building %s; does it already exist?", pkg_file)
    exists = os.path.exists(pkg_file)
    log_message("...%s", exists)
    if exists and ".dirty" in pkg_file:  # decide about this
        exists = False
        log_message("...but version is 'dirty' so will overwrite")

    return exists


def build_pkg(sdist):
    # TODO: replace with pip build one day
    cmd = 'python setup.py '
    if not sdist:
        cmd += 'bdist_wheel --universal '
    elif sdist:
        cmd += 'sdist --formats=gztar '
    return cmd
