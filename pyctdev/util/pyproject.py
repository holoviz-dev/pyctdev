"""pyproject.toml reading functions/hacks.

pyproject.toml currently only used for build stuff.
"""

import os

try:
    import pip._vendor.pytoml as toml
except ImportError:
    import pytoml as toml

from . import log_message


PYPROJECT_TOML = 'pyproject.toml'


def get_buildreqs():
    path = ['build-system', 'requires']
    log_message("Attempting to read '%s.%s' from %s...", *path, PYPROJECT_TOML)
    buildreqs = []
    if os.path.exists(PYPROJECT_TOML):
        pp = toml.load(open(PYPROJECT_TOML))
        if (path[0] in pp) and (path[1] in pp[path[0]]):
            buildreqs += pp[path[0]][path[1]]
        else:
            log_message("...'%s.%s' not found.", *path)
    else:
        log_message("...%s not found.", PYPROJECT_TOML)

    log_message("Build requirements: %s.", buildreqs)
    return buildreqs
