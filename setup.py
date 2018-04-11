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
        # otherwise py2 users will just get an error (should really
        # be fixed in doit)
        'doit' if sys.version_info[0]>2 else 'doit <0.30',
        
        # because tox.ini is currently the master list of
        # tests/environments, some of tox is required...but tox is not
        # in anaconda defaults 'tox'...so we've vendored it.
        #'tox'
        
        # for conda build (included in conda build recipe)
        #'pyyaml'
    ],
    extras_require={
        'tests': ['flake8']
    }
)

if __name__ == "__main__":
    setup(**setup_args)
