# pyct: pyviz common tasks

Tools, documentation, and guidelines to support common tasks across
many similar PyViz projects.

doit+pyct is a cross-platform, make-like tool plus library of common
tasks to allow project admin tasks to be run equally well locally or
on CI systems, and on different platforms.

Although doit+pyct must be installed, the approach is trying to call
standard python and/or conda tools where possible, so that people can
run commands independently without installing doit+pyct. In that case,
pyct can serve as documentation of what all the tasks and commands
are. The biggest benefit of this project right now is collecting all
common cross-project tasks in one place (and having a place to create
issues and/or discuss). Now that it's possible to see what all the
tasks are, the doit+pyct approach could be improved, or an alternative
tool could be used, or changes/additions to underlying tools could be
proposed.

There's an accompanying [background](backgrond.md) document with more
details, and explanations for choices. It's broken into the same
sections, so can be read alongside this document.

** Note: draft that will change/grow. Everything's up for
 discussion. **


## 0. What are all the tasks? How to run a task?

pyct shows what tasks there are, e.g. "run unit tests", "build conda
package", "upload conda package", "install as a developer", and so on.

pyct also documents how to perform those tasks, i.e. what the
necessary command(s) are for a task, or what tasks should be run
before others.

To see all the tasks, you can read `pyct/__init__.py`, or if you have
doit+pyct installed, type `doit list` in a project using pyct to get a
list of the tasks with descriptions. `doit info` gives more detail on
any particular task. Note: not all tasks are currently implemented in
pyct - some only appear in documentation (here) for now.


## 1. Can run project admin tasks locally, on CI, and across platforms

doit/pyct are written in python so should work everywhere python's
available. (And once any python's available, doit can be used to
install other pythons if necessary - currently miniconda and
anaconda.)

Other suggested tools used by pyct are also cross platform: tox,
conda, pip, etc.

Apart from the tools, some of pyct is documentation/guidelines. Tries
to suggest minimal CI-specific magic except where it helps a lot (e.g.
taking advantage of some build system's parallelization, or caching,
...).


## 2. support python and conda ecosystems

Install with pip or conda, create reproducible/isolated environments
with python tools (virtualenv+pip, or pipenv) or with conda tools
(conda env).

TODO: not written yet; doit could wrap these tools...


## 3. support multiple versions of python

Run tests over multiple versions of python.

Python: doit uses tox to run same tests over multiple environments via
convenient `tox` command.

Conda: TODO doit wraps conda commands to ...


## 4. dependencies in one place

Express the dependencies in one place, setup.py. The dependencies
listed in setup.py are used for:

  * end-user pip packages
    
  * end-user conda packages
    
  * developers using conda
    
  * developers using pip
    
  * generating environment files (e.g. examples environment.yml)

    
## 5. dependencies labelled for different purposes

TODO: update from email

Including e.g.:

  * required
    
  * for tests
    
  * for examples
    
  * for building docs


Have gone for `extras_require` in setup.py.

pip understands `extras_require`. E.g. a pip using developer could run
`pip install -e .[tests]` to do a develop install with the required
dependencies plus the dependencies required for testing. Or a user
could run `pip install package[examples]`.

For multiple conda packages (to support 'options'), have
e.g. `conda.recipe/base/` and `conda.recipe/examples/`. The
`package-examples` package has extra dependencies (and depends on
`package`). pyct supports building and uploading either or both.  The
dependencies are all read from setup.py via conda build's support for
reading from setup.py.


## 6. testing of what users install

conda: conda recipes should include test commands (which run on package
installed in a clean env), so when doing conda build you test what
will be installed by users.

python: tox achieves the same thing for python packages (builds
package, creates virtual environment, installs package into
virtualenv, runs tests). tox additionally supports running the same
tests over multiple versions of python, multiple environments, etc.

Above all easier if projects (a) all use same test tools, (b) have a
well defined way to run various groups of tests - see "unify how
various tools are run", below.



## 7. testing of what developers do

conda: `doit conda_develop_install` installs required and test
dependencies (from setup.py) using conda, then runs some variant of
`python setup.py develop`.

pip: `doit_pip_develop_install` `pip install -e`

pyct can also create environments...todo.


## 8. noarch:python conda packages

Project repos should contain conda recipe(s), and these should
probably be for noarch packages.

The conda packages are templated, reading info from setup.py instead
of duplicating it (description, version, license, homepage,
dependencies, etc).


## 9. Channels/sources of dependencies

For python/pip: pypi

For conda: anaconda.org pyviz (releases) and pyviz/label/dev (dev
versions). Only our specific packages are on this channel. Should be
possible for people to use on top of conda-forge or anaconda
defaults. (We could recommend that any one install should not mix
conda-forge and defaults. For a project with tricky requirements, we
could recommend one above the other. Or if a project suffers in
performance on one or the other, we could make a recommendation.)


## 10. generate "environment" files

(TODO: update from email)

pyct support transforming dependencies and generating environment.yml
(and possibly pipenv or similar).


## 11. How to structure project

(TODO: update from email)

I.e. where to put examples, tests, docs (both in repository and when
package is installed.

We should try to pick one common/preferred layout - is that at all
feasible?

We should try to have one common way for users to install examples
and download data.

We should try to agree on what differences there should be between
repository layout and what's actually shipped in packages. E.g. while
both hv and ds have examples/ dir in repository, hv creates 'fake' (?)
examples subpackage when packaging, datashader installs `examples` as
a top-level package in site-packages, etc. Or e.g.  datashader ships
tests in package, while hv does not.


## 12. Unify how various tools are run

Using setup.cfg.

### pytest/nose

Have a `[pytest]` (or `[nose]`) section defining the way to run tests
by default so that the command to run tests is just `pytest`. Prevents
situation where everyone (travis, appveyor, conda package, tox) is
running with different arguments and hence accidentally running
different tests (or maybe that's desirable).

Tox goes further and allows to store multiple test commands for easy
access (to run either individually or all together).

TODO: And/or, pytest has features for defining/selecting groups of
tests. So e.g. maybe `pytest` for the basic/fast/unit tests,
`pytest -m slow` for slow tests, `pytest -m examples` for examples,
etc (not sure what the right way of doing it is, would need to
investigate).


### flakes

Have a `[flake8]` section defining the things we do and do not care
about, and which places to look for files to check. Then the command
to run is just `flake8`.


## 13. What's tested, and how.

Pick one common/preferred way of running tests (e.g. pytest or nose)
and head towards using it more and more where possible.

* python unit tests (pytest/nose)

* python flakes (pyflakes)

* performance/benchmark tests (pytest-benchmark, custom stuff,
  airspeed velocity, ??)

* example notebooks run without error (pytest plugin: nbsmoke/nbval/nbsite)

* example notebooks flakes check (pytest plugin: nbsmoke)

* notebook "data tests" (pytest plugin: nbval)
  
* ...?


## 14. docs


### website

nbsite for examples -> website.

### live docs

Live/browser way for users to try examples: mybinder



## 15. versioning

Version via git tag. Version is stored only in one place in the
repository (a git tag), and is written into packages. Every place that
needs to know version (`__init__.py`; packaging: `setup.py`,
`meta.yaml`; docs) reads it from the single source.

Storing in one place, and it being the tag rather than in the git repo
source code, makes it easier to automate various other 'release time'
tasks.

Be consistent with tags (either vX.Y.Z or X.Y.Z across all projects).

Almost all pyviz projects will use autover via param.



## 16. what release type tasks are automated on travis

As far as possible, just by running one or a couple of doit commands,
avoiding CI-provided magic except where it's unavoidable or very
useful (e.g. parallelizing builds, etc).

### automatically generated conda packages

Every merge to master or every time an alpha/beta/rc format tag is
pushed, conda packages are built and uploaded to anaconda.org
pyviz/label/dev.

If a release format tag is pushed:

  * conda noarch:python package(s) built and uploaded to anaconda.org
    pyviz (pyviz main)
  
  * python sdist and universal wheel built and uploaded to ?pypi ?test
    pypi ?saved elsewhere (might want to manually inspect before
    committing to pypi)


### automatically generated website

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


## 17. Extra CI/Travis things

### caching

Installing miniconda and dependencies from scratch every time takes up
quite a lot of build time for some projects.

So, should support caching of miniconda/conda environments (and maybe
same for python/pip, although speed may not be an issue there).

$HOME/miniconda (which includes environment being used) is cached at
the end of a job. At the start of a job, cache is fetched, and
dependencies are updated according to project's current specified
dependencies.

In many ways, this could be a better test than installing from
scratch, since most devs/users will be updating existing conda
installations/environments rather than starting from scratch.

### build stages/parallelization of builds

