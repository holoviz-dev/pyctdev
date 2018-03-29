import configparser

toxconf = configparser.ConfigParser()
toxconf.read('tox.ini')

def get_tox_cmds(env):
    if env in toxconf:
        return toxconf[env]['commands'].splitlines()
    else:
        return ["""python -c "print('Could not read """ + env + """ from tox.ini');import sys;sys.exit(1)" """]


_options_param = {
    'name':'options',
    'long':'options',
    'short': 'o',
    'type':list,
    'default':['tests']
}
