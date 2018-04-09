from setuptools import setup, find_packages


setup_args = dict(
    name='one',
    version='0.0.1',
    packages = find_packages(),
    install_requires = [
        'param'],
    extras_require = {
        'tests': ['flake8']
    },
    url = "http://",
    license = "BSD",
    description = "Example"
)


if __name__=="__main__":
    setup(**setup_args)
