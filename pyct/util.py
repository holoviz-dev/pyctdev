import sys

# TODO: provide fallback or vendor (bit of) tox
try:
    import tox.config as tox_config
except:
    import os.path
    for pkg in ('tox-3.0.0.zip', 'virtualenv-15.2.0.zip'):
        sys.path.append(os.path.join(os.path.dirname(__file__),'_vendor',pkg))
    import tox.config as tox_config
    
toxconf = tox_config.parseconfig('tox')

def get_env(test_python,test_group,test_requires):
    if test_python == '':
        test_python = getpy()
    return "%s-%s-%s"%(test_python,test_group,test_requires)


def get_tox_python(env):
    if env in toxconf.envconfigs:
        # TODO really doubt this is the right way
        return toxconf.envconfigs[env].basepython.split("python")[1]
    else:
        raise ValueError("Could not find %s in tox.ini"%env)

def get_tox_cmds(env):
    if env in toxconf.envconfigs:
        cmds = []
        for cmd in toxconf.envconfigs[env].commands:
            cmds.append(" ".join(['"{0}"'.format(w) for w in cmd]))
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
    'default':['tests']
}

test_python = {
    'name':'test_python',
    'long':'test-python',
    'type':str,
    'default':'' # defaults to current python
}

test_group = {
    'name':'test_group',
    'long':'test-group',
    'type':str,
    'default':'unit'
}

test_requires = {
    'name':'test_requires',
    'long':'test-requires',
    'type':str,
    'default':'default'
}


def getpy():
    return "py%s%s"%(sys.version_info[0:2])
