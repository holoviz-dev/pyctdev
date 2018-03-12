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
    install_requires=['doit <0.30'] if sys.version_info[0]==2 else ['doit']
)

if __name__ == "__main__":
    setup(**setup_args)
