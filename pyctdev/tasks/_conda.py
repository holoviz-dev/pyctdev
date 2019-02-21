"""Functions to support conda tasks.

Functions here should require conda and/or conda build (either because
they run conda commands, or because they import conda). Or they should
be completely specific to conda.

"""

############################################################
## python stdlib imports

import os
import json
import warnings
import glob
import sys
import pprint
from collections import OrderedDict, Counter

############################################################
## conda/build stdlib-like imports

# yaml is always included with conda so should be safe
import yaml


############################################################
## external imports

# optional
try:
    import graphviz
except ImportError:
    graphviz = None


############################################################
## conda/build imports

import conda
from conda.models.match_spec import MatchSpec as conda_MatchSpec
from conda.cli.python_api import Commands as conda_Commands, run_command as conda_run_command

import conda_build
import conda_build.utils as conda_build_utils
import conda_build.api as conda_build_api

from conda_env.env import from_environment as conda_env_from_environment, Environment as conda_env_Environment

############################################################
## internal/pyctdev imports

from ..util import echo, log_message, _test_matrix_thing, log_warning, doithack_join_cmds, faketox
from ..util.pyproject import get_buildreqs
from ..util.setuptools import read_pins, _get_dependencies, read_extras_provide, read_provides, SETUP_CFG, get_setup_args, Requirement, parse_version_with_packaging_Version
from ..util.setuptools4conda import python2condaV, python2conda, get_packages, get_pkg_tests, read_conda_packages, get_package_dependencies

from .. import _doithacks
from .._doithacks import CmdAction2
from .. import params

from . import register_support as some_register_support


log_message("Imported conda %s (from %s)", conda.__version__, conda.__file__)
log_message("Imported conda_build %s (from %s)", conda_build.__version__, conda_build.__file__)

# TODO: not sure what conda-using developers do/prefer (but the
# choices seem painful)...
#
# pip develop and don't install missing deps
python_develop = "pip install --no-deps -e ."
# pip develop and pip install missing deps
#   python_develop = "pip install -e ."
# setuptools develop and don't install missing deps
#   python_develop = "python setup.py develop --no-deps"
# setuptools develop and easy_install missing deps:
#   python_develop = "python setup.py develop"


# conda build doesn't support pyproject.toml/PEP518
# TODO: this should be requested by flag! like for pip
def __conda_build_deps(channel): # todo: rename - __ temporary
    # return command to install build deps (from pyproject.toml)
    buildreqs = get_buildreqs()
    if len(buildreqs) > 0:
        deps = " ".join('"%s"' % d for d in python2condaV(buildreqs))
        cmd = "conda install -y %s %s" % (
            " ".join(['-c %s' % c for c in channel]), deps)
        log_message(
            "At some point later, I'll just install build dependencies into your current environment (sorry!) by running: %s", cmd)
    else:
        cmd = echo("(no build dependencies were declared in pyproject.toml)")
    return cmd


def _pin(deps):
    # pin the given dependencies with pins as specified in setup.cfg
    pins = read_pins()
    pins = {python2conda(d): pins[d] for d in pins}
    if len(pins) == 0:
        warnings.warn("Pins requested, but no pins in setup.cfg")
        return deps

    deps = python2condaV(deps)
    deps2 = [python2conda(d) for d in deps]
    assert deps == deps2 # TODO: what's going on here?

    pinned_but_missing = set(pins).difference(
        set([conda_MatchSpec(d).name for d in deps]))
    if len(pinned_but_missing) != 0:
        raise ValueError(
            "Pins specified for non-existent dependencies %s" % pinned_but_missing)

    pinneddeps = []
    for d in deps:
        dname = Requirement(d).name
        if dname in pins:
            pinneddeps.append("%s ==%s" % (dname, pins[dname]))
        else:
            pinneddeps.append("%s" % dname)
    return pinneddeps


def _conda_install(
        extras=None, all_extras=False, channel=None, env_name=None, pin_deps=False):
    """Beyond conda: supporting options and pinning

    Supports channel
    """
    if extras is None:
        extras = []

    if channel is None:
        channel = []

    # TODO: list vs. string form for _pin
    deps = _get_dependencies(['install_requires'] +
                             extras, all_extras=all_extras, pypi_only=False)
    deps = python2condaV(deps)
    #deps = [python2conda(d) for d in deps]

    if len(deps) > 0:
        deps = _pin(deps) if pin_deps else deps
        deps = " ".join('"%s"' % dep for dep in deps)
        # TODO and python2conda() ??
        e = '' if env_name is None else '-n %s' % env_name
        return "conda install -y " + e + \
            " %s %s" % (" ".join(['-c %s' % c for c in channel]), deps)
    else:
        return echo("Skipping conda install (no dependencies)")


def env_exists(task, values):
    env_name = task.options['env_name']
    candidates = _conda_envs(env_name)
    counts = Counter([x[0] for x in candidates])

    if counts[env_name]==0:
        return False
    elif counts[env_name]==1:
        return True
    else:
        raise ValueError("Did not find exactly one environment named '%s'.\nPotentially relevant conda info:\n%s"%(env_name, _conda_debug_info()))


def _conda_debug_info():
    info = json.loads(conda_run_command(conda_Commands.INFO, "--json")[0])
    maybe_useful = set(['active_prefix',
                        'active_prefix_name',
                        'base',
                        'conda_prefix',
                        'conda_shlvl',
                        'default_prefix',
                        'root_prefix',
                        'envs'])

    maybe_useful_info = {k:v for k,v in info.items() if k in maybe_useful}
    return pprint.pformat(maybe_useful_info, indent=4)

def _conda_env_prefix(env_name):
    candidates = _conda_envs(env_name)
    counts = Counter([x[0] for x in candidates])
    if counts[env_name]!=1:
        raise ValueError("Did not find exactly one environment named '%s'.\nPotentially relevant conda info:\n%s"%(env_name, _conda_debug_info()))
    return dict(candidates)[env_name]

def _conda_envs(env_name):
    # TODO before merge check you didn't mess this up
    return [(os.path.basename(e), e) for e in json.loads(
        conda_run_command(conda_Commands.INFO, "--json")[0])['envs']]

def _conda_list(prefix):
    return json.loads(conda_run_command(
        conda_Commands.LIST, "-p %s --json" % prefix)[0])

#####
# TODO: these two were part of ecosystem_setup, which is now gone. But
# maybe it needs to come back (possibly as a set of tasks).
#
# def _update_conda(channel):
#     return "conda update -y %s conda" % " ".join(
#         ['-c %s' % c for c in channel])
#
#
# def _install_pkg_tools(channel):
#     # TODO: beware pin here and in setup.py! (will be .cfg)
#     # instead, should read from setup
#     return 'conda install -y %s anaconda-client "conda-build=3.10.1"' % " ".join(
#         ['-c %s' % c for c in channel])
#####

# TODO rewrite and move somewhere common
def buildgraphandwriteitdown(env_name,with_graphviz):
    if with_graphviz:
        global graphviz
        if graphviz is None:
            # at least making the error message appear near where it's used.
            # TODO: consider something more sophisticated, e.g. an import task so that task wouldn't
            # run without the right dependencies?
            import graphviz

    # build graph from packages' metadata
    nodes = set()
    edges = set()
    for pkgmetafile in glob.glob(os.path.join(
            _conda_env_prefix(env_name), 'conda-meta', '*.json')):
        pkgmeta = json.load(open(pkgmetafile))
        pkgname = pkgmeta['name']
        nodes.add(pkgname)
        for d in pkgmeta.get('depends', []):
            edges.add((pkgname, conda_MatchSpec(d).name))

    # write out the graph
    if with_graphviz:
        # can open in browser, can search text
        G = graphviz.Digraph(filename=env_name, format='svg')
        for n in nodes:
            G.node(n)
        for e in edges:
            G.edge(*e)
        G.render()
        log_message("wrote %s.svg", env_name)
    else:
        # TODO: should replace this made up format with something else
        with open(env_name + ".txt", 'w') as f:
            f.write("***** packages *****\n")
            for n in nodes:
                f.write("%s\n" % n)
            f.write("\n***** dependencies *****\n")
            for e in edges:
                f.write("%s -> %s\n" % e)
        log_message("wrote %s.txt (install graphviz for svg)", env_name)


def conda_upload(label):
    # TODO: same comment as for package test: hacky to expect the recipe to be there
    # and to use it for finding the packages. existing -> extant ?
    existing_packages = conda_build_api.get_output_file_paths("conda.recipe")
    # TODO: not yet tried (can you do multiple at the same time?)
    return 'anaconda --token %(password)s upload --user %(user)s ' + ' '.join(
        ['--label %s' % l for l in label]) + ' '.join(existing_packages)

# U R HERE sorting this command out and places that use it
def conda_create(channel,env_name,python):
    #import pdb;pdb.set_trace()
    return "conda create -y %s" % (" ".join(
        ['-c %s' % c for c in channel])) + " --name %(env_name)s python=%(python)s"


def add_pyctdev(env_name):
    # when installing selfi nto environment, get from appropriate channel
    # (doing this is a hack anyway/depends how env stacking ends up going)
    # TODO: part of env stack issue
    selfchan = "pyviz"

    from .. import __version__
    version = parse_version_with_packaging_Version(__version__)
    if version.is_prerelease:
        selfchan += "/label/dev"
    if "PYCTDEV_SELF_CHANNEL" in os.environ:
        selfchan = os.environ["PYCTDEV_SELF_CHANNEL"]

    if selfchan != "":
        selfchan = " -c " + selfchan
    return "conda install -y --name %(env_name)s " + selfchan + " pyctdev"


# TODO: verify there should be no all_extras here
def create_recipe(package, force, pin_deps, pin_deps_as_env):

    if pin_deps and pin_deps_as_env:
        raise ValueError("Can't --pin-deps and --pin-deps-as-env")

    if os.path.exists("conda.recipe/meta.yaml"):
        if force:
            log_message('Overwriting existing recipe: conda.recipe/meta.yaml')
        else:
            log_warning(
                "Using existing recipe: conda.recipe/meta.yaml; not overwriting without --force")
            return ##### sigh

    packages = get_packages(package)
    package_dependencies = get_package_dependencies()

    # TODO: should we warn if there are no dependencies? The default
    # case is probably that you have one fat package dependending on a
    # core one. Or all extras are assumed to depend on the core one
    # (but could also add ability to have dependencies between extras,
    # although that doesn't exist in python land). How to know the
    # core one?

    # TODO: in general, any setup.cfg field might need conversion
    # from python to conda e.g. license (e.g. conda-forge exact
    # licnese name might be different from pypi's?)

    # TODO: support conda verify

    setup_args = get_setup_args()

    meta = OrderedDict()

    meta['package'] = OrderedDict((
        ('name', setup_args['name'] + "-split"),  # TODO ???
        ('version', setup_args['version']),
    ))

    meta['source'] = OrderedDict((
        ('path', '..'),
    ))

    extras_provide = read_extras_provide()

    outputs = []
    for pkgname in packages:
        output = OrderedDict()
        extras = read_conda_packages().get(pkgname, None)

        deps = python2condaV(
            _get_dependencies(
                ['install_requires'] + extras,
                pypi_only=False))
        deps2 = [python2conda(d) for d in _get_dependencies(
            ['install_requires'] + extras, pypi_only=False)]
        assert deps == deps2 # TODO: what is going on here?

        if pin_deps_as_env:
            log_message("Pinning dependencies as %s",pin_deps_as_env)
            # TODO: unify with conda in env_export
            env_name = pin_deps_as_env
            packages = _conda_list(_conda_env_prefix(env_name))
            packagesd = {package['name']: package for package in packages}

            # TODO: could add channel to the pin...
            deps = ["%s ==%s" % (
                conda_MatchSpec(d).name, packagesd[conda_MatchSpec(d).name]['version']) for d in deps]
        elif pin_deps:
            log_message("Pinning dependencies as setup.py")
            deps = _pin(deps)
        else:
            pass

        version = setup_args['version']
        # any interpackage dependencies?

        # TODO: should there be this dep in host too?

        # TODO: I forget without looking, should there be run_constrained in the
        # package that's doing the depending?
        pkgdeps=["%s == %s"%(pd,version) for pd in package_dependencies.get(pkgname,[])]

        deps += pkgdeps

        ## inverse deps for run_constrained...
        run_constrained = []
        for sigh in package_dependencies:
            for pd in package_dependencies[sigh]:
                if pd == pkgname:
                    if sigh not in run_constrained: # ???
                        run_constrained.append(sigh)
        run_constrained = sorted(run_constrained)

        r = open(os.path.join(os.path.dirname(
            __file__), "condatemplate.yaml")).read()
        # hack https://github.com/conda/conda-build/issues/2475
        r = r.replace(r"{{ pname }}", pkgname)

        tdeps = python2condaV(
            _get_dependencies(
                ['tests_require']
                + ['tests'],
                pypi_only=False))
        tdeps2 = [python2conda(d) for d in _get_dependencies(
            ['tests_require'] + ['tests'], pypi_only=False)]
        assert tdeps2 == tdeps
        output['name'] = pkgname

        output['build'] = OrderedDict((
            # TODO: needs updating to c-f style,
            ('script', "python setup.py install --single-version-externally-managed --record=record.txt"),
            ('noarch', 'python')
        ))

        output['requirements'] = OrderedDict()

        if run_constrained:
            output['requirements']['run_constrained'] = ["%s == %s"%(d,version) for d in run_constrained]

        # TODO: do you need pkgdeps in host as well as run?
        output['requirements']['host'] = sorted(python2condaV(get_buildreqs())+pkgdeps)

        output['requirements']['run'] = sorted(deps)

        provides = read_provides()

        for extra in extras:
            provides += extras_provide.get(extra, [])

        if len(provides) == 0:
            log_message('Assumes package name is import name - no hypnens.')
            provides = [setup_args['packages']]

        output['test'] = OrderedDict((
            ('requires', sorted(tdeps)),
            ('imports', sorted(provides)),
        ))

        outputs.append(output)

    meta['outputs'] = outputs

    meta['about'] = OrderedDict((
        ('home', setup_args['url']),
        ('summary', setup_args['description']),
        ('license', setup_args['license'])),
    )

    optional_fields= ['license_file']
    for field in optional_fields:
        if field in setup_args:
            meta['about'][field] = setup_args[field]

    if 'project_urls' in setup_args:
        if 'Source Code' in setup_args['project_urls']:
            meta['about']['dev_url'] = setup_args['project_urls']['Source Code']

    if not os.path.exists("conda.recipe"):  # could do better/race
        os.makedirs("conda.recipe")

    # should be using conda build api throughout this fn instead
    # of copying the representer here...
    def odict_representer(dumper, data):
        return dumper.represent_dict(data.items())
    yaml.add_representer(OrderedDict, odict_representer)
    with open("conda.recipe/meta.yaml", 'w') as f:
        yaml.dump(meta, f, default_flow_style=False)

# TODO: support purge-all?
def conda_build_purge(purge):
    if purge:
        return "conda build purge"
    else:
        return "echo 'not doing conda build purge'"

def conda_build(channel):
    return "conda build %s conda.recipe/" % (
        " ".join(['-c %s' % c for c in channel]))

# TODO: what to call this, what should it remove (see also for tests)

def _remove_recipe_append_and_clobber(
        test_python, test_group, test_requires):
    raise
    #if not pkg_tests:
    #    return


# setup.cfg -> conda env file
def _create_conda_env_file(pin_deps, package, extra, channel,
                all_extras, env_file, env_name, advert):

    packages = get_packages(package)

    all_deps = []
    for pkgname in packages:
        extras = read_conda_packages().get(pkgname, None)

        deps = python2condaV(
            _get_dependencies(
                ['install_requires'] + extras,
                all_extras = all_extras,
                pypi_only=False))

        deps2 = [python2conda(d) for d in _get_dependencies(
            ['install_requires'] + extras, all_extras=all_extras,pypi_only=False)]
        assert deps == deps2 # TODO why??
        all_deps += deps

    deps = set(all_deps)

    if pin_deps:
        deps = _pin(deps)

    e = conda_env_Environment(
        name=env_name,
        channels=channel,
        filename=env_file,
        dependencies=sorted(deps))

    e.save()

    if advert:
        # hack in link back
        with open(env_file, 'r+') as f:
            content = f.read()
            f.seek(0)
            # probably more useful info could be put here
            f.write("# file created by pyctdev:\n#   "
                    + " ".join(sys.argv) + "\n# (run from %s)"%os.getcwd() + "\n\n" + content)


# existing env -> env file (conda env export)
def _conda_env_export(env_name, extra, env_file, all_extras):
    prefix = _conda_env_prefix(env_name)
    E = conda_env_from_environment(
        env_name, prefix, no_builds=True, ignore_channels=False)

    deps = python2condaV(
        _get_dependencies(
            ['install_requires']
            + extra,
            all_extras=all_extras,
            pypi_only=False))
    deps = set([Requirement(d).name for d in deps])

    for what in E.dependencies:
        E.dependencies[what] = [
            d for d in E.dependencies[what] if conda_MatchSpec(d).name in deps]

    # fix up conda channels TODO: should probably just use non-env
    # commands all along instead of conda env
    if 'conda' in E.dependencies:
        packages = {package['name']
            : package for package in _conda_list(prefix)}
        E.dependencies['conda'] = ["%s%s" % ((packages[conda_MatchSpec(x).name]['channel'] + "::" if packages[conda_MatchSpec(
            x).name]['channel'] != "defaults" else ''), x) for x in E.dependencies['conda']]
        E.channels = ["defaults"]

    # what could go wrong?
    E.dependencies.raw = []
    if len(E.dependencies.get('conda', [])) > 0:
        E.dependencies.raw += E.dependencies['conda']
    if len(E.dependencies.get('pip', [])) > 0:
        E.dependencies.raw += [{'pip': E.dependencies['pip']}]

    # TODO: add python_requires to conda deps?
    E.prefix = None
    # TODO: win/unicode
    with open(env_file, 'w') as f:
        f.write(E.to_yaml())
    log_message("Wrote %s", env_file)

def _conda_build_test(channel, pkg, append_file):
    c = "conda build %s " % " ".join(['-c %s' % c for c in channel])
    c += ' -t "%s" --append-file %s' % (pkg, append_file)
    return c


# TODO: rename
def create_recipe_appends(test_python, test_requires,
                           channel, test_group, cleanup, package, available_packages):
    if len(package) == 0:
        log_message("No packages specified; defaulting to all available: %s", available_packages)
        package = available_packages

    package_tests = get_pkg_tests(test_group,package)

    n_pkgs_being_tested = 0
    for pk in package_tests:
        if len(package_tests[pk]) == 0:
            log_message('Package %s not being tested', pk)
        else:
            n_pkgs_being_tested += 1

    # TODO: decide what to do (in combination with allowing packages to be
    # specified)
    if n_pkgs_being_tested == 0:
        raise ValueError("No packages being tested.")  # say what to do...
    elif len(package) > n_pkgs_being_tested:
        log_message("Not all packages are being explicitly tested; the "
                    "supplied --test-group(s) do not cover all packages. If "
                    "that is accidental, either pass more --test-group(s) "
                    "and/or ensure %s's pyctdev.conda.tests_map covers all "
                    "the packages you expect it to.", SETUP_CFG)

    existing_packages = conda_build_api.get_output_file_paths(
        "conda.recipe")

    def topkg(name):
        d = {}
        for pakage in existing_packages:
            # TODO: should use a conda fn for package filename to package name
            d[os.path.basename(pakage).rsplit('-', 2)[0]] = pakage
        return d[name]

    taskcmds = []

    for pkgname, p, g, r, w in _test_matrix_thing(
            package_tests, test_group, test_python, test_requires):
        environment = faketox.get_env(p, g, r, w)
        extra_test_deps = python2condaV(faketox.get_deps(environment))
        cmds = faketox.get_cmds(environment)
        py = faketox.get_python(environment)

        # deps and cmds are appended
        #
        # ??? would maybe like to do something more like conda
        # build conda.recipe -t existing_pkg --extra-command
        # ... --extra-deps ...
        rappend = "conda.recipe/recipe_append--%s-%s-%s-%s-%s.yaml" % (
            pkgname, p, g, r, w)
        with open(rappend, 'w') as f:
            f.write(yaml.dump(
                {
                    'test': {
                        # assumes that having some other python and this one pinned results in
                        # the pinned one being used; TODO should be clobbering the python dep (maybe
                        # config.yaml is what I should be using now?)
                        'requires': ['python =%s' % py] + extra_test_deps,
                        'commands': cmds,
                        # TODO: is this required or not now?
                        # 'source_files': ['tox.ini']
                    }}, default_flow_style=False))
        taskcmds.append(_conda_build_test(channel, topkg(pkgname), rappend))

    if cleanup:
        # another remove test/work intermediates (see same comment elsewhere)
        taskcmds.append("conda build purge")
    if conda_build_utils.on_win:
        # see https://github.com/pyviz/pyct/issues/64
        taskcmds = ['call ' + c for c in taskcmds]

    return doithack_join_cmds(taskcmds)

# TODO: rename this. And what should it clean up?
def _remove_recipe_append_and_clobber_tests(
        test_python, test_group, test_requires, cleanup_meta):
    if not cleanup_meta:
        return

    raise
#     try:
#         p = os.path.join("conda.recipe","meta.yaml")
#         os.remove(p)
#     except:
#         pass
#
#    package_tests = get_pkg_tests(test_group)
#
#    for pkgname, p, g, r, w in _test_matrix_thing(package_tests, test_group, test_python, test_requires):
#        try:
#            p = os.path.join(
#                "conda.recipe", "recipe_append--%s-%s-%s-%s-%s.yaml" % (pkgname, p, g, r, w))
#            os.remove(p)
#        except:
#            pass


def pkg_exists(task,values):
    pkg_files = conda_build_api.get_output_file_paths("conda.recipe")
    # TODO: always build if version is dirty
    # TODO: only rebuild whichever package is missing, not all of them
    exists = True
    log_message("Would be building %s; does it already exist?", pkg_files)
    for f in pkg_files:
        if not os.path.exists(f):
            exists = False
            log_message("...%s is missing",f)
    return exists


######################################################################

# TODO: decide what to do about register_support

def register_support(x): return some_register_support('conda',x)

@_doithacks.hidden_task
def _conda_build_deps():
    return { 'actions': [ CmdAction2(__conda_build_deps) ],
             'params': [params.channel] }

register_support(_conda_build_deps)

@_doithacks.hidden_task
def _conda_develop_install():
    extra_with_tests_as_default = {**params.extra, 'default':['tests']}
    return { 'actions': [ CmdAction2(_conda_install) ],
             # TODO: consider including pin + rest of options here? (except env)
             'params' : [ extra_with_tests_as_default,
                          params.all_extras,
                          params.channel ] }

register_support(_conda_develop_install)


# the thing is you wnat conda to have all deps at once to consider and not install
# separately for several reasons (performance slow, different solution for multiple runs vs all in one).
@_doithacks.hidden_task
def _some_conda_install():
    return { 'actions': [ CmdAction2(_conda_install) ],
             # TODO: all I need?
             'params' : [ params.env_name,
                          params.pin_deps,
                          params.extra,
                          params.all_extras,
                          params.channel ] }

register_support(_some_conda_install)
