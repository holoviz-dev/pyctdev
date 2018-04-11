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
    include_package_data = True,
    install_requires=[
        # otherwise py2 users will just get an error (should really
        # be fixed in doit)
        'doit' if sys.version_info[0]>2 else 'doit <0.30',

        ## tox
        # because tox.ini is currently the master list of
        # tests/environments, some of tox is required - just the
        # config reading bit. But that's tied in with all of tox. And
        # tox is not in anaconda defaults. Further, tox and virtualenv
        # may be problematic with conda, or someone may have/want a
        # customized version, so we don't cause them to be installed
        # and just vendor them.
        #'tox'
        #'virtualenv'
        'pluggy',   # for tox
        'py',       # for tox
        #'argparse', # for virtualenv
        ##

        ## for python packaging
        'wheel',
        'pip',

        ## for conda packaging
        # 'conda-build',
        
        ## conda build
        'pyyaml'
        ##
    ],
    extras_require={
        'tests': ['flake8']
    }
)

if __name__ == "__main__":
    setup(**setup_args)
