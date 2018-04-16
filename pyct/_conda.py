"""
Tasks for conda world

"""

import platform
import sys
import os
try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve

try:
    import yaml
except ImportError:
    yaml = None

from doit.action import CmdAction
from .util import _options_param, test_python, test_group, test_requires, get_tox_deps, get_tox_cmds, get_tox_python, get_env, pkg_tests, test_matrix, echo

# TODO: for caching env on travis, what about links? option to copy?


########## UTIL/CONFIG ##########

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
python_develop = "pip install --no-deps -e ."
# pip develop and pip install missing deps
#  python_develop = "pip install -e ."
# setuptools develop and don't install missing deps
#  python_develop = "python setup.py develop --no-deps"
# setuptools develop and easy_install missing deps:
#  python_develop = "python setup.py develop"


# TODO: what do people who install dependencies via conda actually do?
# Have their own list via other/previous development work? Read from
# travis? Translate from setup.py?  Read from meta.yaml? Install from
# existing anaconda.org conda package and then remove --force?  Build
# and install conda package then remove --force?
def get_dependencies(groups):
    """get dependencies from setup.py"""
    try:
        from setup import meta
    except ImportError:
        try:
            from setup import setup_args as meta
        except ImportError:
            raise ImportError("Could not import setup metadata dict from setup.py (tried meta and setup_args)")

    deps = []
    for group in groups:
        if group in ('install_requires','tests_require'):
            deps += meta.get(group,[])
        else:
            deps += meta.get('extras_require',{}).get(group,[])

    return " ".join('"%s"'%dep for dep in deps)



def _conda_install_with_options(options,channel):
    deps = get_dependencies(['install_requires']+options)
    if len(deps)>0:
        return "conda install -y %s %s"%(" ".join(['-c %s'%c for c in channel]),deps)
    else:
        return echo("Skipping conda install (no dependencies)")



############################################################
# TASKS...


########## MISC ##########

def task_env_capture():
    """Report all information required to recreate current conda environment"""
    return {'actions':["conda info","conda list","conda env export"]}


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
    """Install Miniconda3-latest"""

    location = {
        'name':'location',
        'long':'location',
        'short':'l',
        'type':str,
        'default':os.path.abspath(os.path.expanduser('~/miniconda'))}

    miniconda_installer = miniconda_url[platform.system()].split('/')[-1]
    return {
        'file_dep': [miniconda_installer],
        'uptodate': [lambda task,values: os.path.exists(task.options['location'])],
        'params': [location],
        'actions':
            # TODO: check windows situation with update
            ['START /WAIT %s'%miniconda_installer + " /S /AddToPath=0 /D=%(location)s"] if platform.system() == "Windows" else ["bash %s"%miniconda_installer + " -b -u -p %(location)s"]
        }


def task_ecosystem_setup():
    """Common conda setup (must be run in base env).

    Updates to latest conda, conda-build, and anaconda-client.
    """
    # TODO: could request to do these things in base (when everyone has new
    # enough conda)
    def thing1(channel):
        return "conda update -y %s conda"%" ".join(['-c %s'%c for c in channel])

    def thing2(channel):
        return "conda install -y %s anaconda-client conda-build"%" ".join(['-c %s'%c for c in channel])
    
    return {
        'actions': [CmdAction(thing1), CmdAction(thing2)],
        'params': [_channel_param]}



########## PACKAGING ##########

recipe_param = {
    'name':'recipe',
    'long':'recipe',
    'type':str,
    'default':''
}


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
    
    def thing(channel):
        return "conda build %s conda.recipe/%s"%(" ".join(['-c %s'%c for c in channel]),
                                                 "%(recipe)s")

    def thing2(channel,pkg_tests,test_python,test_group,test_requires):
        cmds = []
        if pkg_tests:
            for (p,g,r,w) in test_matrix(test_python,test_group,test_requires,['pkg']):
                cmds.append(
                    thing(channel)+" -t --append-file conda.recipe/%s/recipe_append--%s-%s-%s-%s.yaml"%("%(recipe)s",p,g,r,w)
                    )
        # hack again for returning variable number of commands...
        return " && ".join(cmds)
    
    def create_recipe_append(recipe,test_python,test_group,test_requires,pkg_tests):
        if not pkg_tests:
            return

        if yaml is None:
            raise ValueError("Install pyyaml or equivalent; see extras_require['ecosystem_conda'].")

        for (p,g,r,w) in test_matrix(test_python,test_group,test_requires,['pkg']): 
            environment = get_env(p,g,r,w)
            deps = get_tox_deps(environment)
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

    def remove_recipe_append(recipe,pkg_tests,test_python,test_group,test_requires):
        if not pkg_tests:
            return

        for (p,g,r,w) in test_matrix(test_python,test_group,test_requires,['pkg']):
            try:
                p = os.path.join("conda.recipe",recipe,"recipe_append--%s-%s-%s-%s.yaml"%(p,g,r,w))
                os.remove(p)
            except:
                pass

    return {'actions': [
        # first build the package...
        CmdAction(thing),
        # then test it...
        # (if test commands overlap what's in recipe, will be some
        #  repetition...they ran above, and they will run again...)
        create_recipe_append,
        CmdAction(thing2),
    ],
            'teardown': [remove_recipe_append],
            'params': [_channel_param, recipe_param, test_python, test_group, test_requires, pkg_tests]}



def task_package_upload():
    """Upload package built from conda.recipe/ (or specified alternative)."""
    # TODO: need to upload only if package doesn't exist (as
    # e.g. there are cron builds)
    
    def thing(label):
        # TODO: fix backticks hack/windows
        return 'anaconda --token %(token)s upload --user pyviz ' + ' '.join(['--label %s'%l for l in label]) + ' `conda build --output conda.recipe/%(recipe)s`'

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

    return {'actions': [CmdAction(thing)],
            'params': [label_param,token_param,recipe_param]}



########## TESTING ##########

# TODO


########## DOCS ##########

# TODO



########## FOR DEVELOPERS ##########

# TODO: not sure this task buys much (but allows to call create_env
# even if env already exists, for updating).

# TODO: should be called create_env or similar
def task_env_create():
    """Create named environment if it doesn't already exist"""
    python = {
        'name':'python',
        'long':'python',
        'type':str,
        'default':'3.6'}

    name = {
        'name':'name',
        'long':'name',
        'type':str,
        'default':'test-environment'}

    return {
        'params': [python,name],
        # TODO: this assumes env created in default location...but
        # apparently any conda has access to any other conda's
        # environments (?!) plus those in ~/.conda/envs (?!)
        # TODO: consider using conda's api? https://github.com/conda/conda/issues/7059
        'uptodate': [lambda task,values: os.path.exists(os.path.join(sys.prefix,"envs",task.options['name']))],
        # TODO: should add doit here
        'actions': ["conda create -y --name %(name)s python=%(python)s"]}



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
        CmdAction(_conda_install_with_options),
        python_develop],
            'params': [_options_param,_channel_param]}

