import os, platform

try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve

from ..util import faketox, test_matrix, doithack_join_cmds


miniconda_url = {
    "Windows": "https://repo.continuum.io/miniconda/Miniconda3-latest-Windows-x86_64.exe",
    "Linux": "https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh",
    "Darwin": "https://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
}

platform_url = miniconda_url[platform.system()]
miniconda_installer = platform_url.split('/')[-1]


def download_miniconda(targets):
    urlretrieve(platform_url, miniconda_installer)


# TODO: this is another doit param hack :(
def mc_installed(task, values):
    if task.options is not None:
        return os.path.exists(task.options['location'])
    else:
        for p in task.params:
            if p['name'] == 'location':
                return os.path.exists(p['default'])
    return False

def _test(test_group, test_requires, test_what):
    cmds = []
    for (p, g, r, w) in test_matrix([], test_group, test_requires, test_what):
        cmds += faketox.get_cmds(faketox.get_env(p, g, r, w))
    return doithack_join_cmds(cmds)
