#! /usr/bin/env python

from setuptools import setup

import versioneer

setup(name = 'pyct',
      description = 'pyviz common tasks',
      version = versioneer.get_version(),
      cmdclass = versioneer.get_cmdclass(),
      license = 'BSD-3',
      url = 'http://github.com/pyviz/pyct',
      packages=['pyct'],
      install_requires=['doit']
      )
