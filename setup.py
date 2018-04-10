#! /usr/bin/env python

import sys
from setuptools import setup

import versioneer

setup_args = dict(
    name = 'pyct',
    description = 'pyviz common tasks',
    version = versioneer.get_version().lstrip('v'),
    cmdclass = versioneer.get_cmdclass(),
    license = 'BSD-3',
    url = 'http://github.com/pyviz/pyct',
    packages=['pyct'],
    python_requires=">=2.7",
    install_requires=[
        # otherwise py2 users will just get and error (should really
        # be fixed in doit)
        'doit <0.30' if sys.version_info[0]==2 else 'doit',
        # because tox.ini is currently the master list of tests/
        # environments...tox is not in defaults (and is problematic)
        # could maybe vendor the required bit
        'tox',
        # for conda build config
        'pyyaml'
    ],
    extras_require={'tests': ['flake8']}
)

if __name__ == "__main__":
    setup(**setup_args)
