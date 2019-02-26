# How to set up a project

## Structure

(TODO not yet written) Typically expected structure for `yourpackage`:

```
README.md # etc
doc/
examples/
yourpackage/
yourpackage/tests
```

...


## Packaging/testing config

For a project that:

  1. Is itself pure python (dependencies don't have to be)

  2. supports installation via python (pip) and conda

  3. has python packages built with setuptools and conda packages
     built with conda build

  4. is tested on win, mac, linux using appveyor and travis CI

  5. has docs generated with nbsite (?)
  
the typically expected packaging/testing config files are:

  * `README.md`, `LICENSE.txt`: project description and license

  * `setup.py`/`setup.cfg`: package metadata, dependencies, etc

  * `pyproject.toml`: dependencies required at packaging/build time.

  * `MANIFEST.in`: rules about which files to include in package

  * `tox.ini`: how to test (i.e. environments, groups of tests, test
    tool config, etc).

  * `.travis.yml`, `.appveyor.yml`: CI config. Hopefully just job
    definitions that call pyctdev tasks, as far as possible.

  * doc/conf.py ?


TODO: should be able to say, see projects in examples/ for starting
point. I.e. all this stuff should be in there.


### pyproject.toml

```
[build-system]
requires = [
    "param >=1.7.0",
    "setuptools >=30.3.0",
    "wheel"
]
```

### setup.py

```
from setuptools import setup

if __name__=="__main__":
    setup()
```

(TODO: missing packaging of examples; https://github.com/pyviz/pyct/issues/22)

### setup.cfg

#### About the package

```
[metadata]
name = yourpackage
version = attr: param.version.get_setupcfg_version
description = yourpackage provides...
long_description = file: README.md
long_description_content_type = text/markdown
license = BSD 3-Clause License
license_file = LICENSE.txt
classifiers =
    License :: OSI Approved :: BSD License
    Operating System :: OS Independent
    Programming Language :: Python
    Programming Language :: Python :: 2.7
    Programming Language :: Python :: 3.5
    ...
    Development Status :: 4 - Beta
author = PyViz
author_email = developers@pyviz.org
maintainer = PyViz
maintainer_email = developers@pyviz.org
url = https://yourproject.org/
project_urls =
    Bug Tracker = https://github.com/pyviz/yourproject/issues
    Documentation = https://yourproject.org/
    Source Code = https://github.com/pyviz/yourproject
```

#### dependencies

```
[options]
python_requires = >=2.7

install_requires =
    param >=1.6.1
    bokeh >=0.12.10
    etc...

[options.extras_require]
tests =
    pytest >=2.8.5
    nbsmoke >=0.2.6
    flake8
    etc...

examples =
    pyct
    holoviews
    etc...

...

```

TODO: indirect/non-python

#### Optional hints for packagers

```
[tool:pyctdev]
;;;;;;;;;;
; declare importable python names
provides =
    pyct
    pyct.build

extras_provide =
    cmd = pyct.cmd
;;;;;;;;;;

;;;;;;;;;;
; mutually compatible versions
pins =
    ###
    # 
    bokeh = 1.0.0dev6
    holoviews = 1.11.0a4
    hvplot = 0.2.1
    geoviews = 1.5.4a6
    datashader = 0.6.8
    panel = 0.1.0a3
    param = 1.8.0a2
    paramnb = 2.0.4
    parambokeh = 0.2.3
    ###
    # avoid tab-completion issue in ipython=6
    ipython = 5.*
    # for datashader compatibility
    dask = 0.18.2
    # StreamingDataFrame name change in 0.3.0
    streamz = 0.3.0
    ipywidgets = 7.*
    # for jupyter notebook and bokeh server
    tornado = 4.5.3
    # in case of unknown future or past compatibility issues
    python = 3.6.*
    numpy = 1.14.5
    pandas = 0.23.4
    xarray = 0.10.3
;;;;;;;;;;
```

#### Hints for specific ecosystems?

```
[tool:pyctdev.conda]

packages =
    pyct-core =
    pyct = cmd

package_dependencies =
    pyct = pyct-core

tests_map =
    build_examples = pyct-core, pyct
    cmd_examples = pyct
    min = pyct-core, pyct
    all = pyct
```

TODO: what else?

#### Additional recommended packaging options

```
[options]
...
include_package_data = True  # ensure MANIFEST.in rules respected at install time
packages = find:             # automatically find packages
```

#### entry points

```
[options.entry_points]
console_scripts =
    yourpackage = yourpackage.__main__:main
```

#### automated git tag versioning

```
[tool:autover.configparser_workaround.archive_commit=$Format:%h$]
```

(TODO: reponame can be different from package name? Anyway this will be replaced with setup.py instead of setup.cfg.)

#### ensure universal wheel

```
[wheel]
universal = 1
```


### tox.ini (testing)

```
# For use with pyct (https://github.com/pyviz/pyct), but just standard
# tox config (works with tox alone).

[tox]
# "test matrix" (bit cryptic; https://github.com/pyviz/pyct/issues/9)
#         test_python         test_group              test_requires    test_what
envlist = {py27,py36}-{lint,unit,examples,min,all}-{default,with_yaml}-{dev,pkg}


[_lint]
description = Flake check python and notebooks, and verify notebooks
deps = .[tests]
commands = flake8
           pytest --nbsmoke-lint -k ".ipynb"
           pytest --nbsmoke-verify -k ".ipynb"

[_unit]
description = Run unit tests
deps = .[tests]
commands = pytest yourpackage

[_examples]
description = Test that examples run
deps = .[examples, tests]
commands = pytest --nbsmoke-run -k ".ipynb"

[_with_yaml]
deps = yaml
#commands = python -c "1/0"

[_min]
description = Check the bare minimum is working.
commands = {[_unit]commands}
deps = .[tests]

[_all]
description = Run all tests
deps = .[examples, tests]
commands = {[_lint]commands}
           {[_unit]commands}
           {[_examples]commands}

[_pkg]
commands = yourpackage copy-examples --path=. --force
           yourpackage fetch-data --path=. --datasets small.yml

[testenv]
changedir = {envtmpdir}

commands = pkg: {[_pkg]commands}
           unit: {[_unit]commands}
           lint: {[_lint]commands}
           examples: {[_examples]commands}
           all: {[_all]commands}
           min: {[_min]commands}
#           with_yaml: {[_with_yaml]commands}           

deps = unit: {[_unit]deps}
       lint: {[_lint]deps}
       examples: {[_examples]deps}
       all: {[_all]deps}
       min: {[_min]deps}
       with_yaml: {[_with_yaml]deps}       

# TODO: is this up to date?
[pytest]
addopts = -v --pyargs --doctest-modules --doctest-ignore-import-errors
norecursedirs = doc .git dist build _build .ipynb_checkpoints
# notebooks to skip running; one case insensitive re to match per line
nbsmoke_skip_run = ^.*JSONInit\.ipynb$

[flake8]
include = *.py
# run_test.py is generated by conda build, which appears to have a
# bug resulting in code being duplicated a couple of times.
exclude = .git,__pycache__,.tox,.eggs,*.egg,doc,dist,build,_build,.ipynb_checkpoints,run_test.py
ignore = E,
         W
```



### travis, appveyor

TODO

(only calling pyctdev commands so can also be run locally)

(travis variables for pypi, anaconda.org)


## docs

TODO


## more TODO

  * notebook data tests
  * benchmarking
  * etc...
