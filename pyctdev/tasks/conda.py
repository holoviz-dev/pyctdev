"""Something something.

Tasks here should require conda and/or conda build (i.e. they run a
conda command, or they use something from ._conda).

"""

from pyctdev.params import cleanup_meta_param, cleanup_param # TODO: you'll be removing these
from pyctdev import params

from ._conda import buildgraphandwriteitdown, python_develop, conda_upload, env_exists, conda_create, create_recipe, conda_build, _conda_env_export, _create_conda_env_file, create_recipe_appends, conda_build_purge, pkg_exists, _conda_install, _add_pyctdev

from . import register as some_register, ProjectTask

from . import env_capture, env_dependency_graph, env_create, env_export, env_file_generate, list_test_envs, develop_install, package_upload, package_build, package_test, install_deps_only

from ..task import DoitTask
from ..util.faketox import print_envs as print_tox_envs
from ..util.setuptools4conda import get_packages
from .._doithacks import PythonAction2, CmdAction2


def register(x): return some_register('conda', x)


# note: some conda installs could be chained via multiple dependent
# tasks...but that's way too slow. Instead, build up a big set of
# dependencies for conda to think about in one go.


# TODO: could this be universal?
register(
    DoitTask(
        task_type=list_test_envs,
        actions=[PythonAction2(print_tox_envs)])
)

register(
    DoitTask(
        task_type=env_capture,
        actions=[#CmdAction2("env"), # TODO windows, macos!
                 CmdAction2("conda info"),
                 CmdAction2("conda list"),
                 CmdAction2("conda env export")])
)

register(
    DoitTask(
        task_type=env_dependency_graph,
        actions=[PythonAction2(buildgraphandwriteitdown)],
        params=[params.env_name_override,
                # TODO: awkward way of doing it...
                {'name': 'with_graphviz',
                 'long': 'with-graphviz',
                 'type': bool,
                 'default': True,
                 'inverse': 'without-graphviz',
                 'help': 'With graphviz produces an svg; without produces some unknown basic text format.'}]))


register(
    DoitTask(
        task_type=develop_install,
        additional_doc="""note: dependencies installed by conda only.""",
        task_dep=["_conda_build_deps",
                  "_conda_develop_install"],
        actions=[CmdAction2(python_develop)]))


register(
    DoitTask(
        task_type=install_deps_only,
        params=[ params.env_name_override,
                 params.pin_deps,
                 params.extra,
                 params.all_extras,
                 params.channel ],
        task_dep=["_conda_build_deps"],
        actions = [ CmdAction2(_conda_install) ]))



# TODO: do we need support for "upload only if package doesn't exist"?
register(
    DoitTask(
        task_type=package_upload,
        additional_doc="""Package will be uploaded to anaconda.org.""",
        actions=[CmdAction2(conda_upload)],
        params=[
            params.user,
            params.password,
            # conda only
            {'name': 'label',
             'long': 'label',
             'short': 'l',
             'type': list,
             'default': [],
             'help': "label(s) for anaconda upload"},
        ]))


register(
    DoitTask(
        task_type=env_create,
        uptodate=[env_exists],
        params=[params.python,
                params.env_name,
                params.channel,
                params.add_pyctdev],
        actions=[CmdAction2(conda_create),
        # TODO note that when testing itself, pyctdev will use previous pyctdev
        # (but not yet testing this command...)
                 CmdAction2(_add_pyctdev)]))


register(
    DoitTask(
        task_type=package_build,
        additional_doc="""Creates recipe in conda.recipe/ then builds with conda-build.
        
        Note that any channels you supply at build time must be
        supplied by users of the package at install time for users to
        be able to get the same(ish) dependencies as used at build
        time.  """,
        # hacks to get a quick version of
        # https://github.com/conda/conda-build/issues/2648
        params=[params.channel,
                params.pin_deps,
                params.pin_deps_as_env,
                params.force,
                params.purge,
                # conda only
                params.package],
        task_dep=["_conda_build_deps"],
        uptodate=[pkg_exists],
        # TODO: maybe split these actions to tasks?
        actions=[PythonAction2(create_recipe),
                 CmdAction2(conda_build),
                 CmdAction2(conda_build_purge)],
        # TODO: restore this
        # 'teardown': [remove_recipe_append_and_clobber],
    ))

# rename to generate env file?
register(
    DoitTask(
        task_type=env_file_generate,
        # TODO: support channel pins too maybe. Either as a separate thing that can
        # also be requested (like version pins), or maybe just use channel::pkg in
        # pins?
        params=[
            params.env_file,
            params.advert,
            params.extra,
            params.channel,
            params.all_extras,
            params.pin_deps,
            params.package,
            params.env_name],
        actions=[PythonAction2(_create_conda_env_file)]))


register(
    DoitTask(
        task_type=env_export,
        params=[
            params.env_file,
            params.env_name_override,
            params.extra,
            params.all_extras,
            params.pin_deps,
        ],
        actions=[
            PythonAction2(_conda_env_export)],
    ))


# doit experiement...

class mytask(ProjectTask):
    pass

def z():
    return {'available_packages': list(get_packages())}


register(
    DoitTask(
        task_type=mytask,
        actions=[PythonAction2(z, read_only=True)],
        read_only=True,
    ))


# TODO: check about the doitdb? I.e. check any conditions under which
# it doesn't re-run.
register(
    DoitTask(
        task_type=package_test,
        additional_doc="tests_map for mapping test groups to conda packages defined in setup.cfg",
        # it's doing something like this multiple times:
        #   conda build -c pyviz/label/dev -t "d:\\mc3\\envs\\pddev\\conda-bld\\noarch\\pyct-core-0.4.5.post5+g6246ef7-py_0.tar.bz2" --append-file conda.recipe//recipe_append--pyct-core-py36-cmd_examples-default-pkg.yaml && conda build purge'
        # where the recipe append is adding the various tests, deps, etc

        # (if test commands overlap what's in recipe, will be some
        #  repetition...they ran above, and they will run again...)
        actions=[CmdAction2(create_recipe_appends)],
        # TODO cleanup
        # 'teardown': [remove_recipe_append_and_clobber_tests],
        getargs={'available_packages': ('mytask', 'available_packages')},
        task_dep=['package_build'],
        params=[params.channel,
                params.test_python,
                params.test_requires,
                params.test_group,
                cleanup_meta_param,
                cleanup_param,
                params.package]))
