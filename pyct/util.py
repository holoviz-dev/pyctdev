# TODO: provide fallback or vendor tox

import tox.config
toxconf = tox.config.parseconfig('tox')



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

env_param = {
    'name':'environment',
    'long':'environment',
    'short': 'e',
    'type':str,
    'default':'unit-default'
}
