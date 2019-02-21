import sys
import itertools


def get_role():
    import doit

    # role can be user or dev - default also set in util.log_message
    return doit.get_var("role", "user")

##################################################
# TODO: temp wrapper
# - might want to link to doit's verbosity too?
# - report the module of caller?
import param
_l = param.Parameterized(name="pyctdev")


def log_warning(msg, *args, **kw):
    _l.warning(msg, *args, **kw)


def log_message(msg, *args, **kw):
    if get_role() == 'dev':
        _l.message(msg, *args, **kw)


def log_verbose(msg, *args, **kw):
    _l.verbose(msg, *args, **kw)
##################################################


def getpy():
    return "py%s%s" % (sys.version_info[0:2])


def test_matrix(test_python, test_group, test_requires, test_what):
    # TODO: sigh, defaults
    test_python = [getpy()] if len(test_python) == 0 else test_python
    test_group = ['min'] if len(test_group) == 0 else test_group
    test_requires = ['default'] if len(test_requires) == 0 else test_requires
    test_what = ['dev'] if len(test_what) == 0 else test_what
    for combo in itertools.product(
            test_python, test_group, test_requires, test_what):
        yield combo


def _test_matrix_thing(package_tests, test_groups, test_python, test_requires):
    for pkgname, test_groups in package_tests.items():
        for group in test_groups:
            for (p, g, r, w) in test_matrix(
                    test_python, [group], test_requires, ['pkg']):
                yield pkgname, p, g, r, w


# TODO: this is a hack until figure out how to make doit show the command
# it's going to run (currently only shows after a failure happens)
def echo(msg):
    return 'python -c "print(\'%s\')"' % msg


def doithack_join_cmds(cmds):
    # Hack to support multiple commands :( Hopefully can remove when
    # easier to pass stuff between doit tasks.
    return " && ".join(cmds)
