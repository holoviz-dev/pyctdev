import sys
import itertools
import configparser

# TODO: provide fallback or vendor (bit of) tox
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

def get_tox_deps(env):
    if env in toxconf.envconfigs:
        deps = toxconf.envconfigs[env].deps
        deps2use = []
        for d in deps:
            if '.[' in d.name:
                pass # only tox dependencies - not from setup.py
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
    return 'python -c "print(\"%s\")"'%msg

