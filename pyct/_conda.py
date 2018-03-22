"""
Tasks for conda world

"""

# TODO: for caching env on travis, what about links? option to copy?



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

def task_download_miniconda():
    """Download Miniconda3-latest"""
    url = miniconda_url[platform.system()]
    miniconda_installer = url.split('/')[-1]

    def download_miniconda(targets):
        urlretrieve(url,miniconda_installer)

    return {'targets': [miniconda_installer],
            'uptodate': [True], # (as has no deps)
            'actions': [download_miniconda]}

def task_install_miniconda():
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

############################################################

from doit.action import CmdAction

_channel_param = {
    'name':'channel',
    'long':'channel',
    'short': 'c',
    'type':list,
    'default':[]
}

def task_ci_configure_conda():
    """Common conda setup for CI systems

    Updates to latest conda, and adds conda-build and anaconda-client.
    """
    
    
    def thing1(channel):
        return "conda update -y %s conda"%" ".join(['-c %s'%c for c in channel])

    def thing2(channel):
        return "conda install -y %s anaconda-client conda-build"%" ".join(['-c %s'%c for c in channel])
    
    return {
        'actions': [CmdAction(thing1), CmdAction(thing2)],
        'params': [_channel_param]}


type_param = {
    'name':'type',
    'long':'type',
    'type':str,
    'default':''
}

def task_build_conda_package():
    """Build conda.recipe/ (or specified alternative).

    Note that whatever channels you supply at build time must be
    supplied by users of the package at install time for users to get
    the same(ish) dependencies as used at build time. (TODO: will be
    able to improve this with conda 4.4.)
    """
    def thing(channel):
        return "conda build %s conda.recipe/%s"%(" ".join(['-c %s'%c for c in channel]),
                                                 "%(type)s")
    
    return {'actions': [CmdAction(thing)],
            'params': [_channel_param,type_param]}



def task_upload_conda_package():
    """Upload package built from conda.recipe/ (or specified
alternative)."""
    
    # TODO: need to upload only if package doesn't exist (as e.g. there are cron builds)
    
    def thing(label):
        # TODO: fix backticks hack/windows
        return 'anaconda --token %(token)s upload --user pyviz ' + ' '.join(['--label %s'%l for l in label]) + ' `conda build --output conda.recipe/%(type)s`'

    label = {
        'name':'label',
        'long':'label',
        'short':'l',
        'type':list,
        'default':[]}

    # should be required, when I figure out params
    token = {
        'name':'token',
        'long':'token',
        'type':str,
        'default':''}

    return {'actions': [CmdAction(thing)],
            'params': [label,token,type_param]}



# TODO: not sure this task buys much (but allows to call create_env
# even if env already exists, for updating).

# TODO: should be called create_conda_env or similar
def task_create_env():
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


def task_capture_conda_env():
    """Report all information required to recreate current conda environment"""
    return {'actions':["conda info","conda list","conda env export"]}


# TODO: doit - how to share parameters with dependencies? Lots of awkwardness
# here to work around that...

# TODO: what do people who've installed dependencies via conda actually do?
def task_conda_develop_install():
    """Python develop install with dependencies installed by conda only"""
    d = _conda_install_x_dependencies(['install_requires','tests_require'])
    # TODO: should this be python setup.py develop --no-deps?  In
    # either case, what effect does no-deps have beyond not installing
    # dependencies?  I noticed while developing a pytest plugin that
    # with --no-deps, the plugin did not get registered...
    d['actions'].append("pip install --no-deps -e .")
    return d

def task_conda_develop_install_alternate():
    """Python develop install with dependencies installed by conda only, kind of"""
    d = _conda_install_x_dependencies(['install_requires','tests_require'])
    d['actions'].append("pip install -e .")
    return d

def _get_dependencies(kinds):
    try:
        from setup import meta
    except ImportError:
        try:
            from setup import setup_args as meta
        except ImportError:
            raise ImportError("Could not import setup metadata dict from setup.py (tried meta and setup_args)")

    deps = []
    for kind in kinds:
        if kind in ('tests_require','install_requires'):
            deps += meta.get(kind,[])
            if kind == 'tests_require':
                # pip doesn't support tests_require; we use extras_require['tests']
                deps += meta.get('extras_require',{}).get('tests',[])
        elif kind == 'extras_require':
            for option in meta.get('extras_require',{}):
                deps += meta['extras_require'][option]
        else:
            raise ValueError("unknown kind %s"%kind)
    return " ".join('"%s"'%dep for dep in deps)


# conda installs are independent tasks for speed (so conda gets all
# deps to think about at once)

def _thing(channel,kinds):
    return "conda install -y %s %s"%(" ".join(['-c %s'%c for c in channel]),
                                     _get_dependencies(kinds))

def _conda_install_x_dependencies(kinds):
    return {'actions': [CmdAction(lambda channel: _thing(channel,kinds))],
            'params': [_channel_param]}

def task_conda_install_required_dependencies():
    """Install required dependencies from setup.py using conda"""
    return _conda_install_x_dependencies(['install_requires'])

def task_conda_install_test_dependencies():
    """Install required and test dependencies from setup.py using conda"""
    return _conda_install_x_dependencies(['install_requires','tests_require'])

def task_conda_install_all_dependencies():
    """Install all dependencies from setup.py using conda"""
    return _conda_install_x_dependencies(["install_requires","tests_require","extras_require"])
