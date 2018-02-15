from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


import glob
import platform
import os
import sys
import zipfile
try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve

miniconda_url = {
    "Windows": "https://repo.continuum.io/miniconda/Miniconda3-latest-Windows-x86_64.exe",
    "Linux": "https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh",
    "Darwin": "https://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
}


# Download & install miniconda...Requires python already, so it might
# seem odd to have this. But many systems (including generic
# (non-python) travis and appveyor images) now include at least some
# system python, in which case this command can be used. But generally
# people will have installed python themselves, so the download and
# install miniconda tasks can be ignored.

def task_download_miniconda():
    url = miniconda_url[platform.system()]
    miniconda_installer = url.split('/')[-1]

    def download_miniconda(targets):
        urlretrieve(url,miniconda_installer)

    return {'targets': [miniconda_installer],
            'uptodate': [True], # (as has no deps)
            'actions': [download_miniconda]}


def task_install_miniconda():
    location = {
        'name':'location',
        'long':'location',
        'short':'l',
        'type':str,
        'default':os.path.abspath(os.path.expanduser('~/miniconda'))}

    miniconda_installer = miniconda_url[platform.system()].split('/')[-1]
    return {
        'file_dep': [miniconda_installer],
        'uptodate': [False], # will always run (could instead set target to file at installation location?)
        'params': [location],
        'actions': [
            'START /WAIT %s'%miniconda_installer + " /S /AddToPath=0 /D=%(location)s"] if platform.system() == "Windows" else ["bash %s"%miniconda_installer + " -b -p %(location)s"]
        }

def task_create_env():
    python = {
        'name':'python',
        'long':'python',
        'type':str,
        'default':'3.6'}

    env = {
        'name':'name',
        'long':'name',
        'type':str,
        'default':'test-environment'}

    return {
        'params': [python,env],
        'actions': ["conda create -y --name %(name)s python=%(python)s"]}


def task_capture_conda_env():
    return {'actions':["conda info","conda list","conda env export"]}

def task_develop_install():
    return {'actions':["pip install --no-deps -e ."]}
