# FAQ

*WIP/draft*: some made up questions and answers...


## oh no, another packaging tool!?

There's no packaging tool here :) pyctdev only calls existing
packaging and testing tools.

The motivation for pyctdev is that we maintain several projects, for
which we have a large number of boring, overlapping tasks over two
packaging ecosystems (python, conda).

We wanted to be able to declare dependencies once, express how to test
once, have automated releases, perform tasks locally or on CI, have a
constant way to refer to a task despite ever-changing underlying
tools, etc...


## why do I need so many files in the root of my repository?

The requirement for these files comes from the packaging and CI
systems themselves. pyctdev currently supports:

  * the pip/python ecosystem (which it currently views as pypi, pip,
    setuptools, wheel, tox, twine, etc, though this will likely change
    over time)

  * the conda ecosystem (anaconda.org, conda build)


## what's the relationship between pyct, pyctbuild, and pyctdev?

pyctdev provides "high level" tasks that project maintainers (and
optionally developers) can use (e.g. "set up development environment",
"build docs", etc). Meanwhile...

  * pyct: optional run time dependency of pyviz projects; provides
    user commands (e.g. copy examples, fetch data)

  * pyctbuild: required build time dependency of pyviz projects
    i.e. required at package time and by developers; provides "common
    setup.py stuff" (packaging of examples, auto versioning)

Note that pyctbuild is not part of pyctdev because:

  * pyctdev has dependencies on various ecosystem' packaging tools
    (e.g. conda build)

  * there are packagers others than ourselves (the whole world does
    not use pyctdev, so things that are required by any packager are
    in pyctbuild)

Note that pyct is not bundled into packages at build time by pyctbuild
because:

  * pyct is optional and not used by all packages

  * we might want to upgrade pyct independently of the pyviz packages
    that use it


## I use pip but not conda - can I still use pyctdev?

Yes (the default "ecosystem" is pip).


## I use conda but not pip - can I still use pyctdev?

Yes (set your project's default "ecosystem" to conda).


## I don't use conda or pip - can I still use pyctdev?

You'd have to add a new 'backend' to pyctdev, as the only two that
currently exist are conda and pip.


## I'm a python package maintainer and use pip already, but I would like to support conda...but I don't want to run conda myself or add special config for it. Can I use pyctdev for that?

It's a good question. I guess pyctdev could provide a way to convert
your wheels to conda packages. That would obviate conda build from the
process of generating conda packages. In fact, maybe I could have
written pyctdev this way from the start...

Note: you'd still need conda build to test your conda packages.  But
you could use conda-forge for that.
