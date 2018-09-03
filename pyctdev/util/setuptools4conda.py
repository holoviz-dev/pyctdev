from . import log_message

from .setuptools import _get_from_setup_cfg, tidyextras, Requirement, SETUP_CFG, _get_setup_metadata2


def read_conda_packages():
    """Return {conda pkg name : list of python extras}"""
    return _get_from_setup_cfg('tool:pyctdev.conda', 'packages', dict, list)


def read_conda_package_dependencies():
    return _get_from_setup_cfg(
        'tool:pyctdev.conda', 'package_dependencies', dict, list)


def read_conda_namespace_map():
    return {tidyextras(x): y for (x, y) in _get_from_setup_cfg(
        'tool:pyctdev.conda', 'namespace_map', dict).items()}


# TODO: this is a sketch. There's also conda-forge vs defaults to
# consider.

def python2conda(dep, nsmap=None):
    # convert python name to conda name

    if nsmap is None:
        # should be read just once rather than for each dep
        nsmap = read_conda_namespace_map()

    # first check for map by name+extras
    # then by name. otherwise just use name.
    #
    # TODO: somewhere there must be a real py spec -> matchspec
    # converter
    r = Requirement(dep)
    mapped = nsmap.get(tidyextras(dep),
                       nsmap.get(r.name, r.name))
    sp = "%s" % mapped
    if len(r.specifier) > 0:
        sp += " %s" % r.specifier
    return sp


# what a mess
# TODO: go through and remove the duplicate calls to V vs. no V and the assert
def python2condaV(deps):
    nsmap = read_conda_namespace_map()
    return [python2conda(dep, nsmap) for dep in deps]


def read_conda_tests_map():
    # Alternative would be to consider it the other way round, i.e.
    # to be more packaging centric e.g.
    #  package_tests =
    #      pyct-core = build_examples
    #      pyct = build_examples, cmd_examples
    return _get_from_setup_cfg('tool:pyctdev.conda', 'tests_map', dict, list)


def get_package_dependencies():
    deps = read_conda_package_dependencies()

    # setup.cfg:
    # package_dependencies = 
    #   a = b, c
    #   b = d

    # a --depends--> b
    #   --depends--> c
    # b --depends--> d

    # no checking for stuff like cycles
    
    return deps


def get_packages(requested_packages=None):
    if requested_packages is None:
        requested_packages = []

    defined_packages = read_conda_packages().keys()
    if len(defined_packages) == 0:
        try:
            defined_packages = [_get_setup_metadata2('name')]
        except KeyError:
            raise ValueError("No name or packages defined in setup.cfg.")

    if len(requested_packages) == 0:
        return defined_packages
    else:
        assert set(defined_packages).issuperset(set(requested_packages))
        return requested_packages


def get_pkg_tests(test_group, packages):
    # TODO: defaults (see test_matrix in util)
    if len(test_group) == 0:
        log_message(
            "No --test-group(s) specified; defaulting to 'min'. Note: definition of 'min' will be required in %s under pyctdev.conda.tests_map",
            SETUP_CFG)
        test_group.append("min")

    tests_map = read_conda_tests_map()

    package_tests = {pkg: [] for pkg in packages}

    for g in test_group:
        for pk in tests_map[g]:
            if pk not in package_tests:
                raise ValueError(
                    "Package '%s' required by test_group, but it is not in the list of packages." % pk)
            package_tests[pk].append(g)

    return package_tests
