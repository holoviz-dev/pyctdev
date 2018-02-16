#! /usr/bin/env python

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
    install_requires=['doit']
)

if __name__ == "__main__":
    setup(**setup_args)
