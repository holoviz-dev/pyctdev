# Background

What are the problems for the types of projects we maintain, which are
primarily those under the PyViz umbrella, and what alternatives there
might be for solving them?

PyViz projects are so far all pure python projects, though they often
have dependencies outside of pure python. They also often have lots of
jupyter notebooks (ipykernel), at least some of which depend on
external (large) data. As the number of pyviz projects has grown, or
as individual projects have grown, it's getting difficult to manage
everything. Also, practices that work well for a couple of highly
skilled developers don't necessarily scale well to more contributors.

What's below is a list of various relevant topics. It's all up for
discussion. There are places where I don't even know I don't know what
I'm talking about. We need to agree on things, then maybe discuss
whether support should be added for something in a place other than
pyctdev eventually (e.g. there's `doit conda_develop_install` to install
required and test dependencies plus the package itself in 'editable'
mode - but this could instead be a command provided by conda itself).


## 0. What are all the tasks? How to run a task?

We manage a large number of independent Python software projects,
which each require a set of typical common tasks like "run the tests"
(on various platforms), "build the docs", "install the dependencies",
"install examples ready for a user to work with".

In theory, it should be possible to run simple commands like `pytest`,
`conda env create`, `conda build`, `python setup.py develop`, etc,
with those commands configured for a particular project via
e.g. setup.cfg, meta.yaml, or some other simple config file. However,
a variety of complications arise in practice:

  1. Commands tend to get so long (with many arguments) that
     remembering individual commands is difficult and requires extra
     documentation.

  2. There end up being so many commands that just listing them as a
     reference requires documentation. One might want to group some
     commands into common tasks. E.g. "run all the tests" could be
     "run the unit tests, run lint checks, run performance tests, run
     detailed/slow tests". Or e.g. "install the dependencies" might be
     "install the minimum dependencies and install some optional
     testing dependencies".

  4. There are often dependencies between tasks. E.g. "install
     miniconda" might depend on "download miniconda". Or "run tests"
     might depend on "download test data".
  
  5. There ends up being duplication of complex task definitions
     between projects (e.g. commands to install miniconda, or to
     download data).

  6. Might not want to repeat some expensive task once it's been
     done. E.g. don't re-download data, don't re-run a notebook if
     it's up to date, etc.

  3. There are "missing commands" for tasks that don't fit into
     typical 'python software project commands'. E.g. many of our
     projects need to do things like fetch and/or extract data before
     running tests.
  
  7. On a real-world project (i.e. more than just a single software
     project), often need to work around (temporary)
     problems. E.g. "install the dependencies" might be "install some
     specific version of anaconda, set conda offline, install some
     dependencies from a local channel".


Might seem that pyctdev is often shadowing simple commands and is thus a
bit pointless or a source of repetition. However, it's still useful as
documentation of what command(s) we expect to use to carry out a task,
and it allows grouping/dependencies. E.g. we have a definition of what
is 'developer install', with alternatives (conda and pip). Even if the
command turns out to be dead simple, this still has the benefit of
being documentation about what we agree the command is by default. The
command(s) can be run alone without using doit.

Don't know if the preceding is a good idea, but I at least get pretty
confused about what I'm supposed to do on any particular project.

In contrast, if a pyctdev task is many steps/is complex, might be better
to have more support in underlying tools. E.g.  `doit
conda_develop_install` exists because there's no way to 'develop
install' using conda, getting the dependencies, without running
multiple conda and pip commands.


Alternatives to doit+pyctdev:

  * do nothing

  * simple/declarative config + commands

    * anaconda project

  * alternative python workflow/task management system
  
    * snakemake
    
    * paver
    
    * microbuild/pynt

  * others?
  
    * buildout

    * fabricate

    * shovel

    * delegator.py

    * sarge

    * fabric

    * pyinvoke

    * a-a-p

    * xonsh

    * docker

    * scikit-ci

    * salt

    * ansible

    * chef

    * puppet

  * make + bash

  * make + (python shell lib/wrapper)
  
    * plumbum
    
  * python reimplmentation of make

    * pymake
    
    * py-make

  * alternative cross-platform, make-like tool

    * scons
    
    * waf
    
    * cmake
    

## 1. Can run project admin tasks locally, on CI, and cross platform

Why?

Remote CI: impartial, world visible, parallel, clean-ish environments,
more hardware/environments than we have, etc.

Local: debugging, speed, things too expensive to run on free CI
systems, etc.

Windows: most personal/business computers in the world at the moment?

Mac: what developers are using?

Linux: frequently used on compute servers, web servers, scientific
world, commonly used for docker containers, etc...?

Often projects have a travis config file full of platform-specific
bash code, which is required because there's no cross-platform command
to do a certain thing. Such code lets tests be automated, but won't
work on Windows, so code ends up not getting tested on Windows. Or if
testing on windows, we end up with an appveyor file full of
cmd/powershell that may or may not do the same as the travis file, and
diverges from the bash version of the code.

So the travis file often ends up like a makefile, but one which you
have no hope of running locally. It's usually different from the
readme instructions, which is different again from what developers do.


## 2. support python and conda ecosystems

While pip and conda overlap, they have different advantages and
disadvantages, and don't cover all of the same things.

Seems important to support both ecosystems because there are many
users of both.

This includes:

  * developers using pip or conda
  
  * installation of packages via pip or conda
  
  * creation of isolated/reproducible environments via python tools
    (e.g. pipenv, or virtualenv+pip) or conda env.


## 3. support multiple versions of python

Seems like there'll always be multiple versions of python to
support. Right now, that might be e.g. 2.7, 3.5, 3.6. Our projects
generally have little trouble supporting multiple versions from one
codebase, but tests need to run over multiple python versions.


## 4. dependencies in one place

Projects typically end up with multiple repeated specifications of
dependencies (requirements.txt, meta.yaml, environment.yml, plus
CI-specific ones), each of which can drift out of sync with each other
or have differences whose purpose (if any) is difficult to discern
later. Testing may need to use multiple different sets of dependencies
(e.g. python 2.7, python 3.5, python 3.6, only with minimum
dependencies, with all, with certain combinations, etc).

Expressing the dependencies in one place should be a simplification.

Went for setup.py. However, the master list could be stored in a
different place (e.g. a text file, or conda meta.yaml, or pipfile, or
whatever). The main thing is having the dependencies expressed in one
place.

The dependencies in setup.py are probably "general concept"
dependencies (not sure what the right term is), e.g. "numpy". Maybe
they have some pinning. But pinning could get a lot more specific
e.g. for an environment file.  Even down to maybe where do you get the
dependencies from (see also 'channels' section below TODO maybe move
channels section up below this one)? v1.0 of something from
conda-forge might actually be different of v1.0 of something from
defaults, maybe because of much lower level dependencies. (Example?
geoviews misery? not getting stuff that uses mkl?) (Can't really do
the same for pip, because it's all from pypi*, and lower level stuff
comes from e.g. os package manager; no control over that.)

* actually setuptools supports dependency_links...let's not go there.

Apart from "general concept" dependencies, there are also times to
have specific dependencies. For a particular application,
i.e. environment.  So conda environment.yaml, or
pipfile/requirements.txt. These could be generated from the general
dependencies, e.g. at release time (getting the set of dependencies
that have already been tested together).

There may be extra dependencies for developers/testing.

TODO: more to fill in from email


## 5. dependencies labelled for different purposes

Python has long supported some ability to express what dependencies
are for/multiple sets of dependencies.  There's `install_requires` for
required dependencies (at install and run time). There's
not-well-supported `tests_require`. There's also not-well-supported
`setup_requires` for 'build time' dependencies (this situation may
improve in the future - PEP518ish). But there's mainly
`extras_require`, a dictionary for multiple sets of dependencies. Our
projects can have extras_require['examples'], extras_require['tests'],
etc.

Have gone for setup.py and `extras_require`, but really this is about
agreeing what to do for our projects, and trying to be consistent, and
trying to keep up (from time to time) with changes in conda and python
worlds.

TODO: update from email


## 6. testing of what users install

Test what users actually install at least as much as testing what
developers do. Projects currently often do not test packages until
after creating them for a release, when they are manually tested.  The
package creation process is often currently not visible/tracked
anywhere.

Need to agree on the aim, agree to put tests into conda packages,
agree to use tox (or equivalent alternative).


## 7. testing of what developers do

Test what developers do, to the extent that's possible. Or at least
test the instructions you give out to would-be developers.

conda-using developers maybe do `conda install package && conda remove
--force package && python setup.py develop --no-deps` or `conda
install some list of dependencies && python setup.py develop
--no-deps` or `conda install some of the dependencies && python
setup.py develop` (which easy_installs the missing dependencies? or
maybe it's all pip now?) or `conda install some list of dependencies
&& pip install -e .` (which pip installs the missing dependencies), or
`conda build path/to/recipe && conda install --use-local && python
setup.py develop --no-deps`, etc etc (note: what about `conda
develop`?).

non-conda-using developers maybe do `python setup.py develop`
(easy_install the dependencies?) or `pip install -e .` (I prefer the
latter because it uses pip to install dependencies - I get wheels, for
fast trouble free installation).

Developers may also want to create and manage environments (conda) or
virtual environments (python). pyctdev can create environments. Why have
pyctdev able to create environments? 1. Because it's useful to have one
command you can run that will create *or* switch to environment if it
already exists. E.g. imagine CI with miniconda/environment caching.
One doit command to create or switch to environment is easier than
having to figure out every time if the environment exists and creating
it otherwise. (Add something to conda instead?) 2. Because it allows
other features, e.g. pyctdev could provide tox-like functionality for
conda developers, where tests can be run over multiple versions of
python, multiple sets of dependencies, etc. (Although maybe that's
covered by conda-build with multiple recipes?)

Note: the above pyctdev features (creating envs, testing over multiple
envs, develop install) are maybe candidates for moving to conda
commands? Or already exist in conda somewhere?


## 8. noarch:python conda packages

Generating and testing (win/mac/linux) * (32/64 bits) * (python
2.7/3.5/3.6) packages for a pure python package seems like a lot of
unnecessary work. If we can get away with one noarch:python package on
pyviz, that might simplify things.

Currently we tend to manually build and upload multiple
platform-specific packages to ioam and ioam/label/dev. We also
maintain conda forge recipes (which are also currently for arch
packages).

My understanding is that conda-forge would welcome noarch. However, it
seems likely that for anaconda defaults, noarch:python would not be
used.


## 9. Channels/sources of dependencies

TODO: very WIP

For python/pip, there's pypi.

For conda, there are many channels on anaconda.org. We plan to have
pyviz and pyviz dev. Mainly, though, there's anaconda defaults and
conda-forge, which are not always compatible.

We currently don't give much advice to people about how to install, so
some people end up mixing channels, or miss a required channel.

conda-forge and main are not binary compatible, conda-forge is conda
4.3 while main is conda 4.4, etc, so things can go quite wrong if
people mix them.

Current package recipes seem to have channels used at build time that
are very likely to be different from those used at install time
(e.g. datashader uses gbrener and conda-forge when building package,
but it's unlikely people use those when installing).


General proposals:

(0) We release to pypi

(1) We release (or just to label/dev?) to anaconda.org pyviz? Then
people can do either `conda install -c pyviz package` or `conda
install -c pyviz -c conda-forge package`. But whatever, we should be
clear that people should either use main or conda-forge for
dependencies, and not mix them (they can mix if they want, but they're
on their own). (Note: not entirely sure people would ever manage to
completely avoid mixing, because main is the default and may have
packages not on conda-forge.)

(2) We release to conda-forge, so people can use conda-forge all they
like - but we also hope/expect/request that Anaconda copies things to
main immediately-ish, so people can instead use main all they
like. (in reality, won't be copying packages if ours are noarch - will
build new packages...?)

(3) We also have pyviz/label/dev, which contains frequent dev packages
created and uploaded by "our own CI". We use these dev packages in
projects, and could tell "advanced" users to try them out. When we
tell people "install from the dev channel", for some projects we may
need to be clear if they should be doing `conda install -c
pyviz/label/dev package -c conda-forge package` or just using
defaults.

If we've been using pyviz/label/dev packages on top of conda-forge
ourselves (? no idea what we currently do), there should be no
surprises when those packages eventually get released on conda-forge,
because we'll have been testing the same set of packages all together
ourselves. If main then faithfully takes things from conda-forge,
there should hopefully then be no surprises there too (?). But the
best tested is going to be whatever we ourselves are using...



## 10. generate "environment" files

advantage of packages (vs environments): can be installed into an
existing environment rather than forcing an isolated environment

disadvantage of packages: environment can be guaranteed (at least to a
higher degree) to work because it's exactly controlled (or at least
controlled to a higher degree).

So e.g. might want to publish highly pinned examples environment.yaml
(for conda env), allowing a user to get a standalone, isolated conda
environment that's got a high chance of working for the specific
examples supplied.  Such an environment needs to be updated over
time. Could generate the environment.yaml from current
dependencies. E.g. for successfully already tested conda package
installed into clean env, capture the environment and use that. Might
need rules for filtering dependencies (e.g. only including those
listed in extras_require['examples']).

The same would apply for pipfile or requirements.txt or whatever
(pipenv or pip+virtualenv+requirements.txt or whatever) or other
similar system a project might want to support.



## 11. How to structure project

TODO: email


## 12. Unify how various tools are run

setup.cfg fairly popular at the moment. Might be replaced in the
future, but seems reasonable to to use if for now.

For now, pyctdev has various common (but awkward/long) test commands
stored, available under tasks like `doit unit_tests` and `doit
nb_lint`, etc. And it has some groups too, e.g. `all_tests`. If more
of the pytest things above were done, these might not be necessary.

There's some tension/overlap between config stored in setup.cfg (or
tox.ini), and things in pyctdev. Bit worried pyctdev could grow a yaml
config file...


## 13. What's tested, and how.


## 14. docs



## 15. versioning

Will need to change what some projects do.

datashader, jupyterlab_holoviews, nbsite, nbsmoke, EarthSim, pyviz,
and sphinx_ioam_theme don't use v.

geoviews and parambokeh mix the two forms (confuses github a bit,
e.g. in tag ordering?)

hv, param, paramnb, autover, (pyctdev), (plus topographica, lancet,
imagen, featuremapper, ...) use v.


## 16. what release type tasks are automated on travis



### automatically generated website

Anything's possible. E.g.:

 * Allow to request a doc build (one at a time only)? E.g. maybe
   pushing a specially named tag (e.g. docbuild) results in build and
   upload to https://pyviz-docs.github.io/package-docbuild. Would
   allow someone to work on the website, or see the result of the
   website for any branch/PR (just move the docbuild tag). Or use
   travis build trigger to achieve the same thing.

 * Use s3. Any/all doc builds could be hosted or made available as a
   download archive at a url that depends on the branch/tag. Docs for
   historical releases could be available too. E.g. always put docs at
   something like https://docs.project.org/0.1.2, and keep
   https://project.org serving the latest release.


## 17. Extra CI/Travis things

TODO

Because no CI system directly supports all the platforms we support,
we have to configure multiple CI systems with different setup
requirements to do the same thing on each platform. Can't necessarily
split the tasks up the same way onto each of the different CI
systems. (The CI systems start from different points (e.g. what
libraries are already present), and they themselves implement some
form of 'tasks' e.g. 'before_install', 'install', 'script', etc, and
they implement stages/pipelines for splitting up bits that can be
independently executed e.g. so you can test with python 2.7 in
parallel with 3.6.)


## A1. missing things, other things to think about


### Tools for handling notebooks in git repo

E.g. commands to clear user-/system-specific metadata, etc.

### whitespace

I would be happy to pick any one standard to use with my editor and
stick to it. However, chances of any kind of agreement on an existing
standard seem pretty close to zero ;) Anyway, this kind of thing only
matters/begins to save time as more people contribute.

### alternative to multiple config files: pyctdev only

TODO: pyctdev could have a config file containing config for all the
tools, so there'd be no need for lots of separate files (setup.cfg,
tox.ini, options passed to commands in travis/appveyor, etc). But then
the separate tools wouldn't work on their own...

### GitHub issues template

Have an issues template asking for information up front, rather than
requesting it later.


### doit downsides/problems

In general, could argue it's not worth supporting "infrequent
contributors" who don't know what they are doing - any competent
python developer should really know about all these things
already. But (a) there are many people who can contribute expertise/do
visualization etc who aren't (full time) python developers and (b) at
least I fall into the category of not knowing/remembering how to
contribute to/perform various tasks for most pyviz projects.

Other things:

* doit's a bit general/low level (although the idea is that pyctdev
  helps)

* can be awkward to develop tasks (although the idea is we don't have
  to keep doing that)
  
* have to try quite hard to keep things declarative (and result's
  not as clear as e.g. a yaml config file would be)

* Last doit to support py2 is 0.29. To simplify installation, pyctdev is
  on pypi as py2 and py3, so it's always `pip install pyctdev` to get
  pyctdev and the right doit (whereas `pip install doit` on py2 fails
  fails; need `pip install pyctdev<0.30`).

* May need to get one of doit's dependencies to put wheels on pypi
  (some mac users have reported pip installing doit because of
  problems with the dependency; annoying because it's a dependency
  that should be optional?)

* Would be handy to get doit onto defaults and conda-forge for
  conda using developers. But could go onto pyviz.

* If you start with just python (or conda), you can use that to pip
  install doit+pyctdev. You can then use doit+pyctdev to do stuff like
  create an environment and install dependencies into it. When you
  then activate that environment, if you want to run more doit tasks
  (which you probably will want to do), you should install doit+pyctdev
  again so it uses the env's python. TODO: doit's create_environment
  should install doit+pyctdev?
  
    * note: say you were using python 3 and created python 2
      environment. If you stay in same directory, the python2 doit you
      install (see above about doit for python2), won't be able to
      read the newer version of doit's db.

* provokes negative reactions, another tool, etc. (Although the idea
  is developers don't have to use it - they can run the commands
  stored in doit on their own i.e. use doit for documentation of what
  the commands are. And eventually doit/pyctdev could become unnecessary
  as what's covered by standardish python tools may expand enough to
  cover managing projects rather than 'just python software
  packages'.) (May well be possible already to find a better/simpler
  tool than doit. Shouldn't be hard to switch if we keep pyctdev
  reasonably straightforward, just generally calling external tools.)

* I'm sure there are more...

