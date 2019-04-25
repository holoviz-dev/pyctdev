"""
Tasks for conda world

"""

# note: conda's api at https://github.com/conda/conda/issues/7059

# TODO: move tasks to conda.py and leave hacks here.

import platform
import os
import glob
import json
import re
try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve


# TODO: Some conda stuff not imported until later because this file
# should be importable even without conda.  Will deal with that in the
# future.

try:
    import yaml
except ImportError:
    yaml = None

from doit.action import CmdAction
from .util import _options_param, test_python, test_group, test_requires, get_tox_deps, get_tox_cmds, get_tox_python, get_env, pkg_tests, test_matrix, echo, get_buildreqs

# TODO: for caching env on travis, what about links? option to copy?


########## UTIL/CONFIG ##########

## TODO: rename, plus link to hack about parameter sharing :(
name = {
    'name':'name',
    'long':'name',
    'type':str,
    'default':'test-environment'}
env_name = {
    'name':'env_name',
    'long':'env-name',
    'type':str,
    'default':'test-environment'}
env_name_again = {
    'name':'env_name_again',
    'long':'env-name-again',
    'type':str,
    'default':''}
##

_channel_param = {
    'name':'channel',
    'long':'channel',
    'short': 'c',
    'type':list,
    'default':[] # note: no channel means user's defaults (currently
                 # typically what comes with ana/miniconda)...is that
                 # what we want?
}

# TODO: not sure what conda-using developers do/prefer...
# pip develop and don't install missing deps
# python_develop = "pip install --no-deps -e ."
# pip develop and pip install missing deps
#  python_develop = "pip install -e ."
# setuptools develop and don't install missing deps
python_develop = "python setup.py develop --no-deps"
# setuptools develop and easy_install missing deps:
#  python_develop = "python setup.py develop"

from .util import get_dependencies,_get_dependencies

def _conda_build_deps(channel):
    buildreqs = get_buildreqs()
    deps = " ".join('"%s"'%dep for dep in buildreqs)
    if len(buildreqs)>0:
        return "conda install -y %s %s"%(" ".join(['-c %s'%c for c in channel]),deps)
    else:
        return echo("Skipping conda install (no build dependencies)")


def _conda_install_with_options(options,channel,env_name_again):
    deps = get_dependencies(['install_requires']+options)
    if len(deps)>0:
        e = '' if env_name_again=='' else '-n %s'%env_name_again
        return "conda install -y " + e + " %s %s"%(" ".join(['-c %s'%c for c in channel]),deps)
    else:
        return echo("Skipping conda install (no dependencies)")


# TODO: another parameter workaround
def _conda_install_with_options_hacked(options,channel):
    return _conda_install_with_options(options,channel,'')

############################################################
# TASKS...


########## MISC ##########

def task_env_capture():
    """Report all information required to recreate current conda environment"""
    return {'actions':["conda info","conda list","conda env export"]}

def task_env_export():
    """
    Generate a pinned environment.yaml from specified env, filtering
    against specified groups of deps.

    If env does not exist, will be created first.

    Pretty awkward right now! Have to run something like this...

    doit ecosystem=conda env_export --env-name [ENV_NAME] --env-file [SOME_FILE.yaml] --env-name-again [ENV_NAME] env_create --name [ENV_NAME]

    e.g.

    doit ecosystem=conda env_export --env-name _pyctdev_test_one --env-file pyctdev_test_one.yaml --env-name-again _pyctdev_test_one --options examples env_create --name _pyctdev_test_one
    """

    # TODO: required, rename, friendlier
    env_file = {
        'name':'env_file',
        'long':'env-file',
        'type':str,
        'default':''}

    def x(env_name,options,env_file):
        import collections
        from conda_env.env import from_environment
        from conda.cli.python_api import Commands, run_command
        env_names = [(os.path.basename(e),e) for e in json.loads(run_command(Commands.INFO,"--json")[0])['envs']]
        counts = collections.Counter([x[0] for x in env_names])
        assert counts[env_name]==1 # would need more than name to be sure...
        prefix = dict(env_names)[env_name]
        E = from_environment(env_name, prefix, no_builds=True, ignore_channels=False)
        from conda.models.match_spec import MatchSpec

        deps = set([MatchSpec(d).name for d in _get_dependencies(['install_requires']+options)])

        for what in E.dependencies:
            E.dependencies[what] = [d for d in E.dependencies[what] if MatchSpec(d).name in deps]

        # fix up conda channels TODO: should probably just use non-env
        # commands all along instead of conda env
        if 'conda' in E.dependencies:
            packages = {package['name']:package for package in json.loads(run_command(Commands.LIST,"-p %s --json"%prefix)[0])}
            E.dependencies['conda'] = ["%s%s"%( (packages[MatchSpec(x).name]['channel']+"::" if packages[MatchSpec(x).name]['channel']!="defaults" else '') ,x) for x in E.dependencies['conda']]
            E.channels = ["defaults"]

        # what could go wrong?
        E.dependencies.raw = []
        if len(E.dependencies.get('conda',[]))>0:
            E.dependencies.raw += E.dependencies['conda']
        if len(E.dependencies.get('pip',[]))>0:
            E.dependencies.raw += [{'pip':E.dependencies['pip']}]

        # TODO: add python_requires to conda deps?
        E.prefix = None
        # TODO: win/unicode
        with open(env_file,'w') as f:
            f.write(E.to_yaml())

    return {'actions':[
        CmdAction(_hacked_conda_install_with_options),
        x],
            'task_dep': ['env_create'],
            'params': [env_name, _options_param, env_file, env_name_again,_options_param,_channel_param]}

# because of default options value...removing 'tests'
def _hacked_conda_install_with_options(task,options,channel,env_name_again):
    if 'tests' in task.options.get('options',[]):
        task.options['options'].remove('tests')
    return _conda_install_with_options(options,channel,env_name_again)

miniconda_url = {
    "Windows": "https://repo.continuum.io/miniconda/Miniconda3-latest-Windows-x86_64.exe",
    "Linux": "https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh",
    "Darwin": "https://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
}

# Download & install miniconda...Requires python already, so it might
# seem odd to have this. But many systems (including generic
# (non-python) travis and appveyor images) now include at least some
# system python, in which case this command can be used. But generally
# people will have installed python themselves, so the download and
# install miniconda tasks can be ignored.

def task_miniconda_download():
    """Download Miniconda3-latest"""
    url = miniconda_url[platform.system()]
    miniconda_installer = url.split('/')[-1]

    def download_miniconda(targets):
        urlretrieve(url,miniconda_installer)

    return {'targets': [miniconda_installer],
            'uptodate': [True], # (as has no deps)
            'actions': [download_miniconda]}

def task_miniconda_install():
    """Install Miniconda3-latest to location if not already present"""
    # NOTE: if caching on CI, will result in no new mc being installed
    # ever until cache is cleared

    location = {
        'name':'location',
        'long':'location',
        'short':'l',
        'type':str,
        'default':os.path.abspath(os.path.expanduser('~/miniconda'))}

    miniconda_installer = miniconda_url[platform.system()].split('/')[-1]
    return {
        'file_dep': [miniconda_installer],
        'uptodate': [_mc_installed],
        'params': [location],
        'actions':
            # TODO: check windows situation with update
            ['START /WAIT %s'%miniconda_installer + " /S /AddToPath=0 /D=%(location)s"] if platform.system() == "Windows" else ["bash %s"%miniconda_installer + " -b -u -p %(location)s"]
        }


# TODO: this is another doit param hack :(
def _mc_installed(task,values):
    if task.options is not None:
        return os.path.exists(task.options['location'])
    else:
        for p in task.params:
            if p['name']=='location':
                return os.path.exists(p['default'])
    return False

def task_ecosystem_setup():
    """Common conda setup (must be run in base env).

    Updates to latest conda, and anaconda-client (cb is pinned)
    """
    def thing1(channel):
        return "conda update -y %s conda"%" ".join(['-c %s'%c for c in channel])

    def thing2(channel):
        # TODO: beware pin here and in setup.py!
        return 'conda install -y %s anaconda-client "conda-build=3.10.1"'%" ".join(['-c %s'%c for c in channel])

    return {
        'actions': [
            CmdAction(thing1),
            CmdAction(thing2)
        ],
        'params': [_channel_param]}



########## PACKAGING ##########

recipe_param = {
    'name':'recipe',
    'long':'recipe',
    'type':str,
    'default':''
}

def _join_the_club(dep):
    # cb at least at 3.10.1 interprets square brackets as selectors
    # even if not after a # and then silently drops...not sure what's
    # accidental and what's deliberate difference between cb and
    # conda. Meanwhile, I've been using the fact that e.g. conda
    # install "dask[complete]" results in installing "dask" to
    # implement the convention that conda packages contain everything
    # i.e. any pip install x[option1,option2,...]  is covered by conda
    # install x. see https://github.com/pyviz/pyct/issues/42
    new = re.sub(r'\[.*?\]','',dep)
    # not much point warning only here, since it happens in other places too
    #if new!=dep:warnings.warn("Changed your dep from %s to %s"%(dep,new))
    return new


# TODO: (almost) duplicates some bits of package_build
# TODO: missing from pip version
def task_package_test():
    """Test existing package

    Specify a "test matrix" (kind of) via repeated --test-python,
    --test-group, and --test-requires.


    """

    def thing(channel,recipe):
        cmd = "conda build %s conda.recipe/%s"%(" ".join(['-c %s'%c for c in channel]),
                                                 "%(recipe)s")
        return cmd


    def thing2(channel,pkg_tests,test_python,test_group,test_requires,recipe):
        cmds = []
        if pkg_tests:
            # TODO: should test groups just be applied across others rather than product?
            # It's about test isolation vs speed of running tests...
            for (p,g,r,w) in test_matrix(test_python,test_group,test_requires,['pkg']):
                cmds.append(
                    thing(channel,recipe)+" -t --append-file conda.recipe/%s/recipe_append--%s-%s-%s-%s.yaml"%("%(recipe)s",p,g,r,w)
                    )
                cmds.append("conda build purge") # remove test/work intermediates (see same comment below)
        # hack again for returning variable number of commands...
        return " && ".join(cmds)

    def create_recipe_append(recipe,test_python,test_group,test_requires,pkg_tests):
        if not pkg_tests:
            return

        if yaml is None:
            raise ValueError("Install pyyaml or equivalent; see extras_require['ecosystem_conda'].")

        for (p,g,r,w) in test_matrix(test_python,test_group,test_requires,['pkg']):
            environment = get_env(p,g,r,w)
            deps = get_tox_deps(environment,hack_one=True) # note the hack_one, which is different from package_build
            deps = [_join_the_club(d) for d in deps]
            cmds = get_tox_cmds(environment)
            py = get_tox_python(environment)

            # deps and cmds are appended
            #
            # TODO: will overwrite recipe_append--... if someone
            # already happens to use it...
            #
            # would maybe like to do something more like conda build
            # conda.recipe -t existing_pkg --extra-command ... --extra-deps ...
            with open("conda.recipe/%s/recipe_append--%s-%s-%s-%s.yaml"%(recipe,p,g,r,w),'w') as f:
                f.write(yaml.dump(
                    {
                        'test':{
                            'requires':['python =%s'%py]+deps,
                            'commands':cmds,
                            # still undecided about which config files to use
                            'source_files': ['tox.ini']
                    }},default_flow_style=False))

    def remove_recipe_append_and_clobber(recipe,pkg_tests,test_python,test_group,test_requires):
        try:
            p = os.path.join("conda.recipe",recipe,"_pyctdev_recipe_clobber.yaml")
            os.remove(p)
        except:
            pass

        if not pkg_tests:
            return

        for (p,g,r,w) in test_matrix(test_python,test_group,test_requires,['pkg']):
            try:
                p = os.path.join("conda.recipe",recipe,"recipe_append--%s-%s-%s-%s.yaml"%(p,g,r,w))
                os.remove(p)
            except:
                pass

    return {'actions': [
        # then test it...
        # (if test commands overlap what's in recipe, will be some
        #  repetition...they ran above, and they will run again...)
        create_recipe_append,
        CmdAction(thing2),
    ],
            'teardown': [remove_recipe_append_and_clobber],
            'params': [_channel_param, recipe_param, test_python, test_group, test_requires, pkg_tests]}



def task_package_build():
    """Build and then test conda.recipe/ (or specified alternative).

    Specify --no-pkg-tests to avoid running any tests other than those
    defined explicitly in the recipe (i.e. to run only vanilla conda
    build, without any modifications).

    Specify a "test matrix" (kind of) via repeated --test-python,
    --test-group, and --test-requires.

    Note that whatever channels you supply at build time must be
    supplied by users of the package at install time for users to get
    the same(ish) dependencies as used at build time. (TODO: will be
    able to improve this with conda 4.4.)

    """
    # TODO: conda.recipe path hardcoded/repeated

    # hacks to get a quick version of
    # https://github.com/conda/conda-build/issues/2648


    pin_deps_as_env = {
        'name':'pin_deps_as_env',
        'long':'pin-deps-as-env',
        'type':str,
        'default':''}


    def create_recipe_clobber(recipe,pin_deps_as_env):
        if pin_deps_as_env == '':
            return
        else:
            requirements_run = []

            # TODO: unify with conda in env_export
            env_name = pin_deps_as_env
            import collections
            from conda.cli.python_api import Commands, run_command
            env_names = [(os.path.basename(e),e) for e in json.loads(run_command(Commands.INFO,"--json")[0])['envs']]
            counts = collections.Counter([x[0] for x in env_names])
            assert counts[env_name]==1 # would need more than name to be sure...
            prefix = dict(env_names)[env_name]

            packages = json.loads(run_command(Commands.LIST,"-p %s --json"%prefix)[0])
            packagesd = {package['name']:package for package in packages}

            deps = _get_dependencies(['install_requires'])
            deps = [_join_the_club(d) for d in deps]

            # TODO: could add channel to the pin...
            from conda.models.match_spec import MatchSpec
            requirements_run = ["%s ==%s"%(MatchSpec(d).name,packagesd[MatchSpec(d).name]['version']) for d in deps]

            with open("conda.recipe/%s/_pyctdev_recipe_clobber.yaml"%recipe,'w') as f:
                f.write(yaml.dump(
                    {
                        'requirements':{
                            'run': requirements_run
                        }
                    },default_flow_style=False))

    # TODO: this should be requested by flag! like for pip
    def thing0(channel):
        buildreqs = get_buildreqs()
        if len(buildreqs)>0:
            deps = " ".join('"%s"'%dep for dep in buildreqs)
            return "conda install -y %s %s"%(" ".join(['-c %s'%c for c in channel]),deps)
        else:
            return 'echo "no build reqs"'

    def thing(channel,pin_deps_as_env,recipe):
        cmd = "conda build %s conda.recipe/%s"%(" ".join(['-c %s'%c for c in channel]),
                                                 "%(recipe)s")
        if pin_deps_as_env != '':
            cmd += " --clobber-file conda.recipe/%s/_pyctdev_recipe_clobber.yaml"%recipe
        return cmd

    def thing2(channel,pkg_tests,test_python,test_group,test_requires,recipe,pin_deps_as_env):
        cmds = []
        if pkg_tests:
            # TODO: should test groups just be applied across others rather than product?
            # It's about test isolation vs speed of running tests...
            for (p,g,r,w) in test_matrix(test_python,test_group,test_requires,['pkg']):
                cmds.append(
                    thing(channel,pin_deps_as_env,recipe)+" -t --append-file conda.recipe/%s/recipe_append--%s-%s-%s-%s.yaml"%("%(recipe)s",p,g,r,w)
                    )
                cmds.append("conda build purge") # remove test/work intermediates (see same comment below)
        # hack again for returning variable number of commands...
        return " && ".join(cmds)

    def create_recipe_append(recipe,test_python,test_group,test_requires,pkg_tests):
        if not pkg_tests:
            return

        if yaml is None:
            raise ValueError("Install pyyaml or equivalent; see extras_require['ecosystem_conda'].")

        for (p,g,r,w) in test_matrix(test_python,test_group,test_requires,['pkg']):
            environment = get_env(p,g,r,w)
            deps = [_join_the_club(d) for d in get_tox_deps(environment)]
            cmds = get_tox_cmds(environment)
            py = get_tox_python(environment)

            # deps and cmds are appended
            #
            # TODO: will overwrite recipe_append--... if someone
            # already happens to use it...
            #
            # would maybe like to do something more like conda build
            # conda.recipe -t existing_pkg --extra-command ... --extra-deps ...
            with open("conda.recipe/%s/recipe_append--%s-%s-%s-%s.yaml"%(recipe,p,g,r,w),'w') as f:
                f.write(yaml.dump(
                    {
                        'test':{
                            'requires':['python =%s'%py]+deps,
                            'commands':cmds,
                            # still undecided about which config files to use
                            'source_files': ['tox.ini']
                    }},default_flow_style=False))

    def remove_recipe_append_and_clobber(recipe,pkg_tests,test_python,test_group,test_requires):
        try:
            p = os.path.join("conda.recipe",recipe,"_pyctdev_recipe_clobber.yaml")
            os.remove(p)
        except:
            pass

        if not pkg_tests:
            return

        for (p,g,r,w) in test_matrix(test_python,test_group,test_requires,['pkg']):
            try:
                p = os.path.join("conda.recipe",recipe,"recipe_append--%s-%s-%s-%s.yaml"%(p,g,r,w))
                os.remove(p)
            except:
                pass

    return {'actions': [
        create_recipe_clobber,
        # 0. install build requirements (conda build doesn't support pyproject.toml/PEP518
        CmdAction(thing0),
        # first build the package...
        CmdAction(thing),
        "conda build purge", # remove test/work intermediates (disk space on travis...but could potentially annoy someone as it'll remove other test/work intermediates too...)
        # then test it...
        # (if test commands overlap what's in recipe, will be some
        #  repetition...they ran above, and they will run again...)
        create_recipe_append,
        CmdAction(thing2),
    ],
            'teardown': [remove_recipe_append_and_clobber],
            'params': [_channel_param, recipe_param, test_python, test_group, test_requires, pkg_tests, pin_deps_as_env]}



def task_package_upload():
    """Upload package built from conda.recipe/ (or specified alternative)."""
    # TODO: need to upload only if package doesn't exist (as
    # e.g. there are cron builds)

    def thing(label):
        # TODO: fix backticks hack/windows
        return 'anaconda --token %(token)s upload --user %(user)s ' + ' '.join(['--label %s'%l for l in label]) + ' `conda build --output conda.recipe/%(recipe)s`'

    label_param = {
        'name':'label',
        'long':'label',
        'short':'l',
        'type':list,
        'default':[]}

    # should be required, when I figure out params
    token_param = {
        'name':'token',
        'long':'token',
        'type':str,
        'default':''}

    # should be required, when I figure out params
    user_param = {
        'name':'user',
        'long':'user',
        'type':str,
        'default':'pyviz'}

    return {'actions': [CmdAction(thing)],
            'params': [label_param,token_param,recipe_param,user_param]}



########## TESTING ##########

# TODO


########## DOCS ##########

# TODO



########## FOR DEVELOPERS ##########

# TODO: not sure this task buys much (but allows to call create_env
# even if env already exists, for updating).

def task_env_create():
    """Create named environment if it doesn't already exist

    Environment will include pyctdev.
    """
    python = {
        'name':'python',
        'long':'python',
        'type':str,
        'default':'3.6'}

    # TODO: improve messages about missing deps
    try:
        from conda.cli.python_api import Commands, run_command # noqa: hack
        uptodate = _env_exists
    except:
        uptodate = False

    def _morex(channel):
        return "conda create -y %s"%(" ".join(['-c %s'%c for c in channel])) + " --name %(name)s python=%(python)s"

    def _morexx():
        # when installing selfi nto environment, get from appropriate channel
    # (doing this is a hack anyway/depends how env stacking ends up going)
        from . import __version__
        from setuptools._vendor.packaging.version import Version
        selfchan = "pyviz"
        if Version(__version__).is_prerelease:
            selfchan+="/label/dev"

        return "conda install -y --name %(name)s -c " + selfchan + " pyctdev"


    return {
        'params': [python,name,_channel_param],
        'uptodate': [uptodate],
        # TODO: Wouldn't need to check for env if conda create --force
        # would overwrite/update existing env.
        # TODO: note: pyctdev when testing itself will use previous pyctdev
        # but not yet testing this command...
        'actions': [CmdAction(_morex),CmdAction(_morexx)]}

# TODO: this is another doit param hack :(
# need to file issue. meanwhile probably decorate uptodate fns
def _env_exists(task,values):
    name = None
    if task.options is not None:
        name = task.options['name']
    else:
        for p in task.params:
            if p['name']=='name':
                name = p['default']
    if name is None:
        return False
    else:
        from conda.cli.python_api import Commands, run_command
        return name in [os.path.basename(e) for e in json.loads(run_command(Commands.INFO,"--json")[0])['envs']]




# TODO: doit - how to share parameters with dependencies? Lots of
# awkwardness here to work around that...

# conda installs are independent tasks for speed (so conda gets all
# deps to think about at once)

# TODO: should be one command with --options param



def task_develop_install():
    """python develop install, with specified optional groups of dependencies (installed by conda only).

    Typically ``conda install "test dependencies" && pip install -e . --no-deps``.

    Pass --options multiple times to specify other optional groups
    (see project's setup.py for available options).

    E.g.

    ``doit develop_install -o examples -o tests``
    ``doit develop_install -o all``

    """
    return {'actions': [
        CmdAction(_conda_build_deps),
        CmdAction(_conda_install_with_options_hacked),
        python_develop],
            'params': [_options_param,_channel_param]}


def task_env_dependency_graph():
    """Write out dependency graph of named environment."""

    def _x(env_name):

        ##### find the environment
        # (todo copied from earlier in file!)
        import collections
        from conda.cli.python_api import Commands, run_command
        env_names = [(os.path.basename(e),e) for e in json.loads(run_command(Commands.INFO,"--json")[0])['envs']]
        counts = collections.Counter([x[0] for x in env_names])
        assert counts[env_name]==1 # would need more than name to be sure...
        prefix = dict(env_names)[env_name]

        ###### build graph from packages' metadata
        from conda.models.match_spec import MatchSpec
        nodes = set()
        edges = set()
        for pkgmetafile in glob.glob(os.path.join(prefix,'conda-meta','*.json')):
            pkgmeta = json.load(open(pkgmetafile))
            pkgname = pkgmeta['name']
            nodes.add(pkgname)
            for d in pkgmeta.get('depends', []):
                edges.add( (pkgname, MatchSpec(d).name) )

        ###### write out the graph
        try:
            import graphviz
        except ImportError:
            graphviz = None

        if graphviz:
            G = graphviz.Digraph(filename=env_name,format='svg') # can open in browser, can search text
            for n in nodes:
                G.node(n)
            for e in edges:
                G.edge(*e)
            G.render()
            print("wrote %s.svg"%env_name)
        else:
            # should replace this made up format with something else
            with open(env_name+".txt",'w') as f:
                f.write("***** packages *****\n")
                for n in nodes:
                    f.write("%s\n"%n)
                f.write("\n***** dependencies *****\n")
                for e in edges:
                    f.write("%s -> %s\n"%e)
            print("wrote %s.txt (install graphviz for svg)"%env_name)

    return {'actions': [_x,], 'params':[env_name,]}
