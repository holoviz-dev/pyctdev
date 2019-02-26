###
# TODO: replace with pyviz autover
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
###

import doit

try:
    from .util import log_message

    log_message("This is pyctdev %s (from %s)", __version__, __file__)
    log_message("Using doit %s (from %s)", ".".join(str(x)
                                                    for x in doit.__version__), doit.__file__)
    del log_message
except ModuleNotFoundError:
    # it's not a big deal if that doesn't work
    pass

# TODO probably need to move this elsewhere (actually probably remove
# and drop py27 support?)
#
# doit bug in 0.29, which is last version to support py27
try:
    doit.get_var("ecosystem")
except AttributeError:
    from doit import doit_cmd
    doit_cmd.reset_vars()
    del doit_cmd

del doit
