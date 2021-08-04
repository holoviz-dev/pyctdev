import sys
import os
import itertools
import configparser

# Fallbacks for conda, which can't install tox from defaults (at
# least, not as of June 2018). Allows to parse tox.ini (i.e. to use
# tox.ini as single place where all test cmds and envs are stored)
try:
    import tox.config as tox_config
except:
    import os.path
    for pkg in ('tox-3.0.0.zip', 'virtualenv-15.2.0.zip'):
        sys.path.append(os.path.join(os.path.dirname(__file__),'_vendor',pkg))
    import tox.config as tox_config
    
toxconf = tox_config.parseconfig('tox')
# we later filter out any _onlytox commands...
toxconf_pre = configparser.ConfigParser()
toxconf_pre.read('tox.ini')

onlytox = '{[_onlytox]commands}'

def get_env(test_python,test_group,test_requires,test_what):
    if test_python == '':
        test_python = getpy()
    return "%s-%s-%s-%s"%(test_python,test_group,test_requires,test_what)


def get_tox_python(env):
    if env in toxconf.envconfigs:
        # TODO really doubt this is the right way
        return toxconf.envconfigs[env].basepython.split("python")[1]
    else:
        raise ValueError("Could not find %s in tox.ini"%env)

def get_tox_cmds(env):
    if env in toxconf.envconfigs:
        toxpre = toxconf_pre['testenv']['commands'].splitlines()
        # skip all "onlytox" commands
        i = 0 if not toxpre[0].startswith(onlytox) else len(toxconf_pre['_onlytox']['commands'].splitlines())
        for c in toxpre[1::]:
            assert not c.startswith(onlytox), "Bad tox config: only first command can be 'onlytox' skipped"
        cmds = []
        for cmd in toxconf.envconfigs[env].commands[i::]:
            if len(cmd)>0:
                # can't quote first on win (need to quote rest...a list would be better than string - should clean up
                cmds.append("%s "%cmd[0] + " ".join(['"{0}"'.format(w) for w in cmd[1::]]))
        return cmds
    else:
        #raise ValueError("Could not find %s in tox.ini"%env)
        return ["""python -c "print('Could not read """ + env + """ from tox.ini');import sys;sys.exit(1)" """]

def get_tox_deps(env,hack_one=False):
    if env in toxconf.envconfigs:
        deps = toxconf.envconfigs[env].deps
        deps2use = []
        for d in deps:
            if hack_one is False: # you are testing that dependencies were already specified correctly
                if '.[' in d.name:
                    pass # only tox dependencies - not from setup.py
                elif d.name=='.':
                    assert False # expecting this to never happen
                else:
                    deps2use.append(d.name)
            else:
                if '.[' in d.name: # can't quite decide if this is the right thing to do (it's for supporting --test-requires on existing package)
                    deps2use += _get_dependencies([x.strip() for x in deps[0].name[2:-1].split(',')])
                    
                elif d.name=='.':
                    assert False # expecting this to never happen
                else:
                    deps2use.append(d.name)

                
        return deps2use
        
    else:
        raise ValueError("Could not find %s in tox.ini"%env)

_options_param = {
    'name':'options',
    'long':'options',
    'short': 'o',
    'type':list,
    # TODO: confusing to do this, because it means no way to have
    # none
    'default':['tests']
}

# the hack for above default
_options_param2 = {
    'name':'options2',
    'long':'options2',
    'short': 'o2',
    'type':list,
    'default':[]
}


# TODO: very related to options_param :(
# TODO: couldn't pip support this, or some kind of pattern matching?
_all_extras_param = {
    'name':'all_extras',
    'long':'all-extras',
    'type':bool,
    'default':False
}

test_python = {
    'name':'test_python',
    'long':'test-python',
    'type':list,
    'default':[]
}

test_group = {
    'name':'test_group',
    'long':'test-group',
    'type':list,
    'default':[]
}

test_requires = {
    'name':'test_requires',
    'long':'test-requires',
    'type':list,
    'default':[]
}

test_what = {
    'name':'test_what',
    'long':'test-what',
    'type':list,
    'default':[]
}

pkg_tests = {
    'name':'pkg_tests',
    'long':'pkg-tests',
    'type':bool,
    'default':True,
    'inverse':'no-pkg-tests'
}


def getpy():
    return "py%s%s"%(sys.version_info[0:2])

def test_matrix(test_python,test_group,test_requires,test_what):
    # sigh, defaults
    test_python = [getpy()] if len(test_python)==0 else test_python
    test_group = ['unit'] if len(test_group)==0 else test_group
    test_requires = ['default'] if len(test_requires)==0 else test_requires
    test_what = ['dev'] if len(test_what)==0 else test_what               
    for combo in itertools.product(test_python,test_group,test_requires,test_what):
        yield combo

def echo(msg):
    return 'python -c "print(\'%s\')"'%msg


##### only for conda really

# TODO: drop support for pyviz custom dict stuff in setup.py
# (i.e. migrate all to setup.cfg) and then this stuff will become much
# simpler...
def _get_setup_metadata():
    meta = None
    if os.path.exists("setup.cfg"):
        from setuptools.config import read_configuration
        setupcfg = read_configuration("setup.cfg")
        if 'options' in setupcfg:
            if 'install_requires' in setupcfg['options']:
                meta = setupcfg['options']

    if meta is None:
        try:
            from setup import meta
        except ImportError:
            try:
                from setup import setup_args as meta
            except ImportError:
                raise ValueError("Could not find dependencies in setup.cfg, and could not import setup metadata dict from setup.py (tried meta and setup_args)")

    return meta

def _get_setup_metadata2(k):
    meta = None
    if os.path.exists("setup.cfg"):
        from setuptools.config import read_configuration
        setupcfg = read_configuration("setup.cfg")
        if k in setupcfg['metadata']:
            return setupcfg['metadata'][k]
        elif k in setupcfg['options']:
            return setupcfg['options'][k]

    if meta is None:
        try:
            from setup import meta
        except ImportError:
            try:
                from setup import setup_args as meta
            except ImportError:
                raise ValueError("Could not find %s in setup.cfg, and could not import setup metadata dict from setup.py (tried meta and setup_args)"%k)
        return meta[k]


# TODO: what do people who install dependencies via conda actually do?
# Have their own list via other/previous development work? Read from
# travis? Translate from setup.py?  Read from meta.yaml? Install from
# existing anaconda.org conda package and then remove --force?  Build
# and install conda package then remove --force?
def _get_dependencies(groups,all_extras=False):
    """get dependencies from setup.cfg or otherwise setup.py"""
    meta = _get_setup_metadata()
    deps = []
    if all_extras:
        extras = meta.get('extras_require',{})
        groups = set(groups).union(set(extras))
    for group in groups:
        if group in ('install_requires','tests_require'):
            deps += meta.get(group,[])
        else:
            # TODO: it's ok to not fail for missing install_requires, tests_require, i.e. standard ones. Not ok to not fail for missing extras_require e.g. I try doit develop_install -o recommended but if recommended does not exist that should be an error
            deps += meta.get('extras_require',{}).get(group,[])
    return deps

def get_dependencies(groups,all_extras=False):
    return " ".join('"%s"'%dep for dep in _get_dependencies(groups,all_extras=all_extras))


def get_buildreqs():
    try:
        import pip._vendor.pytoml as toml
    except Exception:
        try:
            # pip>=20.1
            import pip._vendor.toml as toml
        except Exception:
            # pip>=21.2.1
            import pip._vendor.tomli as toml

    buildreqs = []
    if os.path.exists('pyproject.toml'):
        with open('pyproject.toml') as f:
            pp = toml.load(f)
        if 'build-system' in pp:
            buildreqs += pp['build-system'].get("requires",[])
    return buildreqs


# TODO: can i use more of setuptools config parsing?  There was some
# reason I didn't use setuptools.config.read_configuration, but I
# can't remember what it was now. (I think it was to do with needing a
# % sign for the git format (autover), but that breaking some version
# of config reading.) Replace bit by bit and see what happens?
def read_pins(f):
    from setuptools.config import ConfigHandler
    # duplicates some earlier configparser stuff (which doesn't
    # support py2; need to clean up)
    try:
        import configparser
    except ImportError:
        import ConfigParser as configparser # python2 (also prevents dict-like access)
    pyctdev_section = 'tool:pyctdev'
    config = configparser.ConfigParser()
    config.read(f)

    if pyctdev_section not in config.sections():
        return {}

    try:
        pins_raw = config.get(pyctdev_section,'pins')
    except configparser.NoOptionError:
        pins_raw = ''
    
    return ConfigHandler._parse_dict(pins_raw)

def read_conda_packages(f,name):
    from setuptools.config import ConfigHandler
    # duplicates some earlier configparser stuff (which doesn't
    # support py2; need to clean up)
    try:
        import configparser
    except ImportError:
        import ConfigParser as configparser # python2 (also prevents dict-like access)
    config = configparser.ConfigParser()
    config.read(f)

    pyctdev_section = 'tool:pyctdev.conda'
    
    if pyctdev_section not in config.sections():
        return []

    try:
        packages_raw = config.get(pyctdev_section,'packages')
    except configparser.NoOptionError:
        packages_raw = ''

    return ConfigHandler._parse_list(ConfigHandler._parse_dict(packages_raw)[name])


def read_conda_namespace_map(f):
    from setuptools.config import ConfigHandler
    # duplicates some earlier configparser stuff (which doesn't
    # support py2; need to clean up)
    try:
        import configparser
    except ImportError:
        import ConfigParser as configparser # python2 (also prevents dict-like access)
    pyctdev_section = 'tool:pyctdev.conda'
    config = configparser.ConfigParser()
    config.read(f)

    if pyctdev_section not in config.sections():
        return {}

    try:
        namespacemap_raw = config.get(pyctdev_section,'namespace_map')
    except configparser.NoOptionError:
        namespacemap_raw = ''
    
    return ConfigHandler._parse_dict(namespacemap_raw)

