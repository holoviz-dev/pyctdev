import os
if "PYCT_ECOSYSTEM" not in os.environ:
    os.environ["PYCT_ECOSYSTEM"] = "pip"

from pyct import *  # noqa: api
