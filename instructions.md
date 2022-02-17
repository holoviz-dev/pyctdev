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

  1. supports installation via python (pip) and conda

  2. has python packages built with setuptools and conda packages
     built with conda build

  3. is tested on win, mac, linux using appveyor and travis CI

the typically expected packaging/testing config files are:

  * `README.md`, `LICENSE.txt`: project description and license

  * `setup.cfg`: python package metadata and dependencies

  * `pyproject.toml`: dependencies required at packaging/build time

  * `MANIFEST.in`: rules about which files to include in package

  * `conda.recipe/meta.yaml`: conda build recipe (templated from
    python packaging metadata as far as possible) i.e. conda
    equivalent of `setup.cfg` + `pyproject.toml`.

  * `tox.ini`: how to test (i.e. environments, groups of tests, test
    tool config, etc)

  * `.travis.yml`, `.appveyor.yml`: CI config

  * (`dodo.py`: currently required for pyctdev, but will probably go
    away)


### pyproject.toml

```
[build-system]
requires = [
    "pyctbuild",
    "setuptools"
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
version = attr: pyctbuild.version.get_setup_version2
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
    Programming Language :: Python :: 3.6
    Development Status :: 4 - Beta
author = PyViz
author_email = holoviews@gmail.com
maintainer = PyViz
maintainer_email = holoviews@gmail.com
url = https://yourproject.org/
project_urls =
    Bug Tracker = https://github.com/pyviz/yourproject/issues
    Documentation = https://yourproject.org/
    Source Code = https://github.com/pyviz/yourproject
```

A mapping from `pip` installable packages to `conda` installable packages can be added
in the `setup.cfg` file as follows:

```
[tool:pyctdev.conda]
namespace_map = 
    geopandas=geopandas-base
    graphviz=python-graphviz
    ...
```

Note that `pyctdev` strips the extras defined in `setup.py` (e.g. `ibis[sqlite]` is converted to `ibis`) so it's not possible
to define a mapping between an extra and a specific conda. For example declaring `ibis[sqlite]=ibis-sqlite` in `setup.cfg` won't be
taken into account by `pyctdev` since `ibis[sqlite]` has already been transformed to `ibis` when the mapping is used.

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

doc =
    nbsite
    sphinx_ioam_theme
    etc...
```

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
[tool:autover]
reponame = yourpackage
```

Also include `pkgname` if different from `reponame`.

(See also `version` in metadata, above.)


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
#        python version     test group        extra envs  extra commands       
envlist = {py27,py36}-{lint,unit,examples,all}-{default}-{dev,pkg}

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

deps = unit: {[_unit]deps}
       lint: {[_lint]deps}
       examples: {[_examples]deps}
       all: {[_all]deps}

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


### conda.recipe/meta.yaml

```
{% set sdata = load_setup_py_data() %}

package:
  name: yourpackage
  version: {{ sdata['version'] }}

source:
  path: ..

build:
  noarch: python
  script: python setup.py install --single-version-externally-managed --record=record.txt
  entry_points:
    {% for group,epoints in sdata.get("entry_points",{}).items() %}
    {% for entry_point in epoints %}
    - {{ entry_point }}
    {% endfor %}
    {% endfor %}  

requirements:
  host:
    # duplicates pyproject.toml (not supported in conda build)
    - python
    - setuptools
    - pyctbuild
  run:
    - python {{ sdata['python_requires'] }}
    {% for dep in sdata.get('install_requires',{}) %}
    - {{ dep }}
    {% endfor %}

test:
  imports:
    - yourpackage
  requires:
    {% for dep in sdata['extras_require']['tests'] %}
    - {{ dep }}
    {% endfor %}

about:
  home: {{ sdata['url'] }}
  summary: {{ sdata['description'] }}
  license: {{ sdata['license'] }}
  license_file: {{ sdata['license_file'] }}
```

Note: pyctdev will run the appropriate test commands from tox.ini
during packaging.


### travis, appveyor

TODO

(only calling pyctdev commands so can also be run locally)

(travis variables for pypi, anaconda.org)


## docs

TODO


## more TODO

  * notebook data tests
  * benchmarking

