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
        # otherwise py2 users will just get an error (should really
        # be fixed in doit)
        # TODO: pin. (and py3 only now?)
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
        # Also many conda packages use it to build anyway.
        'pip >=10',
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
        'ecosystem_conda': ['conda ==4.6.4',
                            'conda-build ==3.17.8',
                            'anaconda-client ==1.7.2'],
        'graphs': ['python-graphviz'],
    }
)

if __name__ == "__main__":
    setup(**setup_args)
