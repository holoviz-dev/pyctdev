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
    entry_points={
        'console_scripts': [
            'pyctdev = pyctdev.__main__:main'
        ]
    },
    install_requires=[
        "param",
        # py2: <0.30 otherwise py2 users will just get an error (should really
        # be fixed in doit)
        # py3 pin because we should evaluate new major releases
        'doit ==0.31' if sys.version_info[0]>2 else 'doit <0.30',

        # doit requires cloudpickle but does not specify the dependency
        'cloudpickle',

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
        # Also many conda packages use it to build anyway.        
        # pinning to avoid https://github.com/pyviz/pyctdev/issues/12
        'pip >=19.1.1'
#        'setuptools >=39' # for its vendoring of stuff        
    ],
    extras_require={
        'tests': ['flake8'],
        'ecosystem_pip': ['tox','twine','wheel'],
        # pins are supposed to be for when it became possible to
        # install them outside of root/base env, and when api appeared;
        # not sure exactly which versions
        # (actually, cb pin is for tested/known good version
        # TODO: does this work out practically vs ecosystem_setup? E.g. what about updating to latest conda? Or just rely on miniconda to provide that (then what about e.g. caching on travis?)
        'ecosystem_conda': ['conda >=4.4',
                            'conda-build >=3.10.1',
                            'anaconda-client']
                            # +some kind of yaml?
    }
)

if __name__ == "__main__":
    setup(**setup_args)
