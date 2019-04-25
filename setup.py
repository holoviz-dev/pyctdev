#! /usr/bin/env python

import sys
from setuptools import setup

import versioneer

setup_args = dict(
    name = 'pyctdev',
    description = 'python packaging common tasks for developers',
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    version = versioneer.get_version().lstrip('v'),
    cmdclass = versioneer.get_cmdclass(),
    license = 'BSD-3',
    url = 'http://github.com/pyviz/pyctdev',
    packages=['pyctdev'],
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

        # Pretty much part of every python distribution now anyway.
        # Use it e.g. to be able to read pyproject.toml
        'pip >=10'
    ],
    extras_require={
        'tests': ['flake8'],
        'ecosystem_pip': ['tox','twine','wheel'],
        # pins are supposed to be for when it became possible to
        # install them outside of root/base env, and when api appeared;
        # not sure exactly which versions
        # (actually, cb pin is for tested/known good version
        # TODO: beware pin here and in _conda.py!
        'ecosystem_conda': ['conda >=4.4', 'conda-build ==3.10.1']
    }
)

if __name__ == "__main__":
    setup(**setup_args)
