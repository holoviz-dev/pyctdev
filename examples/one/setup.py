from setuptools import setup, find_packages


setup_args = dict(
    name="one",
    version="0.0.1",
    python_requires=">=2.7",
    packages=find_packages(),
    install_requires=[
        # just example
        "hypothesis[numpy] <3.57.0"
        # TODO: need a [] without a version to test cb dropping as selector
    ],
    extras_require={
        "tests": ["flake8"],
        "examples": [
            "holoviews[recommended] <=1.10.0",  # pulls in other deps and pinned (both deliberate, for testing)
        ],
    },
    url="http://",
    license="BSD",
    description="Example",
)


if __name__ == "__main__":
    setup(**setup_args)
