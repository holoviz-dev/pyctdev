# pyct: pyviz common tasks

Tools (and documentation) to support common tasks across many similar
PyViz projects.

**Note: documentation is draft/currently being written**

## What is pyct?

The main part of pyct is a cross-platform, make-like tool plus library
of common tasks to allow project admin tasks to be run equally well
locally or on CI systems, on different platforms, or to support
different python package 'ecosystems' (pip and conda):

```
$ doit list
build_docs            build docs
develop_install       python develop install with specified optional groups of dependencies.
ecosystem_setup       Common pip setup
env_capture           Report all information required to recreate current environment.
env_create            TODO: create named environment if it doesn't already exist.
package_build         Build pip package, then install and test all_quick in venv
package_upload        Upload pip packages to pypi
test_all              flake tests, unit tests, examples
test_examples         Run examples (likely to be time/memory consuming)
test_examples_quick   Run quick examples.
test_flakes           Check for flakes (typically python module and notebooks).
test_quick            Run quick tests
test_unit             Run core unit tests; should always pass everywhere.

$ doit ecosystem=conda list
build_docs            build docs
develop_install       python develop install, with specified optional groups of dependencies (installed by conda only).
ecosystem_setup       Common conda setup
env_capture           Report all information required to recreate current conda environment
env_create            Create named environment if it doesn't already exist
miniconda_download    Download Miniconda3-latest
miniconda_install     Install Miniconda3-latest
package_build         Build conda.recipe/ (or specified alternative).
package_upload        Upload package built from conda.recipe/ (or specified alternative).
test_all              flake tests, unit tests, examples
test_examples         Run examples (likely to be time/memory consuming)
test_examples_quick   Run quick examples.
test_flakes           Check for flakes (typically python module and notebooks).
test_quick            Run quick tests
test_unit             Run core unit tests; should always pass everywhere.
```

Although doit+pyct must be installed to run these tasks, the approach
is trying to call standard python and/or conda tools where possible,
so that people can run commands independently without installing
doit+pyct. This means pyct can be viewed as:

  * documentation of what all the common tasks are
  
  * documentation of the commands necessary to perform those tasks

  * a way to expose gaps in underlying tools that we might like to
    fill (or exposes our lack of knowledge of how to use them, so we
    can be corrected :) )
  
  * a way to map relatively unchanging "high level tasks" (e.g. "run
    the unit tests") to underlying commands that might change over
    time (e.g. as the python packaging ecosystem changes) or that vary
    between projects (e.g. run tests with nose or with pytest).

  * our current best understanding of how to perform the various tasks
    (balancing the best possible way with what's practically possible
    in general, given what tools are currently widely available).
    
The accompanying [background](background.md) document (even more draft
than this one!) contains more details, along with explanations for
choices. It's broken into the same sections, so can be read alongside
this document.

There's also an [instructions](instructions.md) document for setting
up a new project (but it's only a placeholder right now...).


## What does pyct cover?

Something something

### 0. What are all the tasks? How to run a task?

pyct shows what tasks there are, e.g. "run unit tests", "build conda
package", "upload conda package", "install as a developer", and so on.

pyct also documents how to perform those tasks, i.e. what the
necessary command(s) are for a task, or what tasks should be run
before others.

To see all the tasks, you can type `doit list` in a project using pyct
to get a list of the tasks with descriptions. `doit info` gives more
detail on any particular task. Alternatively, you can read the pyct
source code; most tasks are straightforward commands.


### 1. Can run project admin tasks locally, on CI, and across platforms

doit/pyct are written in python so should work everywhere python's
available. (And once any python's available, doit can be used to
install other pythons if necessary - currently miniconda and
anaconda.)

Other suggested tools used by pyct are also cross platform: tox,
conda, pip, etc.


### 2. support python and conda ecosystems

pyct supports performing most tasks with either the python/pip or the
conda ecosystem. E.g. `doit develop_install` will typically run `pip
install -e .[tests]`, which installs the dependencies using pip and
then does an editable install. Alternatively, `doit ecosystem=conda
develop install` will install dependencies using conda, followed by an
editable install. Projects can set a default ecosystem. 

The ability to install with pip or conda, create reproducible/isolated
environments with python tools (virtualenv+pip, or pipenv) or with
conda tools (conda env), package for pip or conda, helps developers
using primarily one ecosystem to still support the other (e.g. via CI
systems).


### 3. support multiple versions of python

Similarly to allowing developers to support both pip and conda
ecosystems, pyct allows developers to support multiple versions of
python. For python, doit uses tox to run same tests over multiple
environments using tox. For conda, pyct runs conda build over multiple
versions of python.


### 4. dependencies in one place

pyct allows developers to express their project's "abstract"
dependencies in one place. Currently this place is setup.py, as it's
widely supported by both python and conda tools. The dependencies
listed in setup.py are used for:

  * end-user pip packages
    
  * end-user conda packages
    
  * developers using conda
    
  * developers using pip
    
  * generating environment files (e.g. examples environment.yml)

The abstract dependencies may be transformed to more concrete ones,
e.g. for a tutorial examples environment, versions of all dependencies
may be pinned to ensure reproducibility (see 10/environment files,
below).

pyct support transforming dependencies and generating environment.yml
(and possibly pipenv or similar).


### 5. dependencies labelled for different purposes

pyct supports expressing build and install/runtime dependencies, plus
various optional groups of dependencies (e.g. for running examples,
building docs, etc).

pyct uses standard/generally supported python/pip/setuptools setup.py
arguments to do this (`install_requires` and `extras_require`). pip
understands these, so the same optional dependency groups are
available to users (e.g. a user can run `pip install
package[examples]` to get package and the dependencies necessary to
run its examples.

To support 'options' in the conda ecosystem, multiple packages are
generated - though typically our projects just have "base" and
"examples" packages. `package-examples` depends on a specific pinned
`package` (pinned at build time).


### 6. testing of what users install

pyct encourages testing of the packages that users will install,
rather than focusing only on testing what developers work with.

In the python ecosystem, tox is used to build a package, create a
clean virtual environment, installs the package, and then run the
tests. tox additionally supports running the same tests over multiple
versions of python, in multiple environments (e.g. with different sets
of dependencies installed), etc.

In the conda ecosystem, conda build is called multiple times to
achieve the same.


### 7. testing of what developers do

It's often difficult to contribute to a project, because setting it up
to the point of being able to run the tests is difficult. Seasoned
project developers know what they are doing, but it's less obvious to
occasional developers.

pyct ensures the dependencies required to develop a project are
obvious, and encourages developers to keep them up to date (e.g. by
testing `doit develop_install` on neutral CI machines).

pyct also tries to capture how developers set up their environment.
E.g. dependencies installed by conda, with a `python setup.py develop
--no-deps` on top.


### 8. Testing in different environments

E.g. `doit package_build --test-python=py36 --test_requires=with_xarray --test-group=unit`
will build a package then install it into a python 3.6 environment,
and will then further install `with_xarray` dependencies, and then
will run the unit tests. The dependencies for `with_xarray` are
specified in tox.ini (as are the unit test commands). This works with
ecosystem=pip and ecosystem=conda. It's also possible to have extra
test commands that only run in a particular test environment
(e.g. `with_xarray`).

`doit test_unit` will run the unit tests in your current environment.
If there are extra commands for a particular environment, they will be
run if you select it. E.g. `doit test_unit --test-group
with_xarray`. However, your current environment is not altered by test
commands, so you would need to have installed `with_xarray`
dependencies if necessary.


### 9. packages on demand? simplify packaging recipes?

As well as specifying dependencies once, attempt to express other
package metadata only once. Currently this is in setup.py. Templating
is then used for conda build. This prevents the common situation where
descriptions, URLs, licenses, etc, are mismatched.

pyct expects project is being released first on pypi and (anaconda.org
pyviz). From these sources, conda-forge can be updated, followed by
anaconda defaults (but we are not necessarily the maintainers of those
channels).

pyct is currently primarily supporting pure python packages. While
they may often have complex, platform specific dependencies, the
packages themselves are pure python. Therefore noarch:python conda
packages where possible.


### 10. Channels/sources of dependencies

For python/pip: typically just pypi.org. But other 'channels' can be
specified. E.g. test.pypi.org, or a private server.

Our pyviz conda packages can usually be installed on top of either
anaconda defaults or conda-forge. anaconda.org pyviz (releases) and
pyviz/label/dev (dev versions). Only our specific packages are on this
channel. (We could recommend that any one install should not mix
conda-forge and defaults. For a project with tricky requirements, we
could recommend one above the other. Or if a project suffers in
performance on one or the other, we could make a recommendation.)


### 11. How to structure project

Although it's not necessary, a common structure simplifies things
across multiple similar projects. Pyviz projects typically have
repositories that look like:

```
/package/
/package/tests
/package/tests/data
/examples/
/examples/data        # maybe just have /data
/examples/assets
/docs/
```

Limit differences between what's in repository and what's in package
shipped to users.


### 12. Unify how various tools are run

Often, it's not clear how to run the tests for a project. Pyct already
helps with this by having high level tasks such as "run unit
tests". However, pyct also encourages internal command definitions to
appear only once.

Currently, setup.cfg is used to store global options for commands
(e.g. flake8 rules), while tox.ini is used to store the various actual
commands used for different things (e.g. running unit tests, running
tests in different environments, etc). (TODO: what is shared across
projects, and how? Would rather not have a config file for pyct...)


### 13. What's tested, and how.

There are various tools for running tests (e.g. pytest, nose). An aim
of pyct is for pyviz projects to all end up using the same tools where
possible. And to configure those tools in the same kind of way.

* unit tests: pytest

* flakes: pyflakes

* examples:

    * notebooks run without error: pytest plugin nbsmoke
    
    * notebooks flakes: pytest plugin nbsmoke
    
    * notebooks "data tests": pytest plugin nbva

* performance/benchmark tests: (pytest-benchmark, custom stuff,
  airspeed velocity, ??)

* ...?

pytest has features for defining ("marking") and then selecting groups
of tests to run. So pyct expects there to be:

  * "slow tests" (`pytest -m slow`)

  * ...?


### 14. docs

#### website

  * nbsite for examples -> website

#### live docs

  * Live/browser way for users to try examples: mybinder


### 15. versioning

Version via git tag. Version is stored only in one place in the
repository (a git tag), and is written into packages. Every place that
needs to know version (`__init__.py`; packaging: `setup.py`,
`meta.yaml`; docs) reads it from the single source.

Storing in one place, and it being the tag rather than in the git repo
source code, makes it easier to automate various other 'release time'
tasks. Most pyviz projects will use autover (via param).

Versioning scheme:

  * we use `vX.Y.Z`

  * post 1.0, (TODO: copy hv's scheme?)


### 16. automate release type tasks on travis

As far as possible, just by running one or a couple of doit commands,
avoiding CI-provided magic except where it's unavoidable or very
useful (e.g. parallelizing builds, etc).

#### automatically generated packages

Every (dev) release:

  * conda packages are built and uploaded to anaconda.org
    (pyviz/label/dev) pyviz/label/main

  * pip packages (sdist zip, universal wheel) are built and uploaded
    to (test.pypi.org) pypi.org

A release happens when a `vX.Y.Z` tag is pushed. Dev releases can
either be defined as "every merge to master" (e.g. for a mature
project), or "every time a `vX.Y.ZaN` style tag is pushed (for a
rapidly changing project).

Note: "package build" means generate package, install package into
clean environment, run tests.


#### automatically generated website

Two main options:

  1. for young, fast-moving projects: a single main website (default:
     https://package.github.io/) updated on releases (plus maybe also
     special post-release tags where we're fixing minor docs issues
     without changing code, which presumably must be tagged
     specially), with a separate dev website (default:
     https://pyviz-docs.github.io/package-master) updated on every
     push to master (or every time an alpha/beta/rc format tag is
     pushed ?).

  2. Same as 1, but also archiving websites for each major release
     (i.e. one copy for X.Y, updated for each new .Z) over time until
     we eventually delete them.  Presumably could actually just make 2
     the default, with the definition that only versions 1.0 or
     greater count as a major release, in which case it would follow
     policy 1 until reaching 1.0, then policy 2, thereby acting as
     appropriate for a young, fast-moving project until release 1.0,
     then archiving each x.y version.

Note: for e.g. datashader, using travis isn't currently feasible (build
takes too long/uses too much memory/requires too-large data). But
travis is just using doit commands, so same can be run locally at
release time.


### 17. Extra CI things

#### platforms

* Ubuntu (travis)

* MacOS (travis)

* Windows (appveyor)


#### caching

Installing miniconda and dependencies from scratch every time takes up
quite a lot of build time for some projects.

Caching of miniconda/conda environments is therefore
supported. (Supported also for python/pip, although speed is not an
issue there).

In many ways, this could be a better test than installing from
scratch, since most devs/users will be updating existing conda
installations/environments rather than starting from scratch.


#### build stages/parallelization of builds

Rather than running tasks sequentially (wall clock time consuming; a
task might affect subsequent ones), tasks can be run independently in
parallel.

