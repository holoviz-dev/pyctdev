"""
"""

import os, platform

from ..util import faketox
from ..params import test_requires, test_what, test_group
from ..task import DoitTask
from .._doithacks import CmdAction2, PythonAction2
from . import register as some_register, build_docs, develop_test, PyctdevTask
from ._universal import mc_installed, miniconda_installer, download_miniconda, _test


def register(x): return some_register('universal', x)


register(
    DoitTask(
        task_type=build_docs,
        additional_doc="testing additional doc",
        params=[{'name': 'org',
                 'long': 'org',
                 'type': str,
                 'default': ''},
                {'name': 'repo',
                 'long': 'repo',
                 'type': str,
                 'default': ''}],

        actions=[
            # TODO: this is out of date for current nbsite
            CmdAction2(
                'nbsite_nbpagebuild.py %(org)s %(repo)s ./examples ./docs'),
            CmdAction2('sphinx-build -b html ./docs ./docs/_build/html'),
            CmdAction2('nbsite_fix_links.py ./docs/_build/html'),
            CmdAction2('touch ./docs/_build/html/.nojekyll'),
            CmdAction2('nbsite_cleandisthtml.py ./docs/_build/html take_a_chance')]
    ))

# note: groups of tests with doit would be more flexible, but would
# duplicate tox

register(
    DoitTask(
        task_type=develop_test,
        additional_doc="someting somehing\n\n" + str(faketox.get_docs()),
        params=[test_requires,
                test_what,
                test_group],
        actions=[CmdAction2(_test)],
    ))


# Download & install miniconda...Requires python already, so it might
# seem odd to have this. But many systems (including generic
# (non-python) travis and appveyor images) now include at least some
# system python, in which case this command can be used. But generally
# people will have installed python themselves, so the download and
# install miniconda tasks can be ignored.

# rename to python_download and python_install ?? or not? as you can also
# install python. maybe distrib_install?

class miniconda_download(PyctdevTask):
    """Download Miniconda3-latest"""


class miniconda_install(PyctdevTask):
    """Install Miniconda3-latest to location if not already present"""
    params = ['location']


register(
    DoitTask(
        task_type=miniconda_download,
        targets=[miniconda_installer],
        uptodate=[True],
        actions=[PythonAction2(download_miniconda)]))

register(
    DoitTask(
        task_type=miniconda_install,
        # NOTE: if caching on CI, will result in no new mc being installed
        # ever until cache is cleared
        params=[{'name': 'location',
                 'long': 'location',
                 'short': 'l',
                 'type': str,
                 'default': os.path.abspath(os.path.expanduser('~/miniconda'))}],

        file_dep=[miniconda_installer],
        uptodate=[mc_installed],
        actions=[
            # TODO: check windows situation with update
            CmdAction2('START /WAIT %s' % miniconda_installer + " /S /AddToPath=0 /D=%(location)s")] if platform.system(
        ) == "Windows" else [CmdAction2("bash %s" % miniconda_installer + " -b -u -p %(location)s")]
    ))
