#!/usr/bin/env python3
"""

"""

import os
import setuptools
import sys

from setuptools.command.test import test as TestCommand


NAME = "musikernel"
URL = 'https://github.com/j3ffhubb/musikernel'
DESCRIPTION = (
    "Holistic audio production solution"
)


def _version():
    if 'test' in sys.argv:
        # avoid triggering a pytest coverage report bug
        return 'test'
    dirname = os.path.dirname(__file__)
    abspath = os.path.abspath(dirname)
    path = os.path.join(
        abspath,
        '..',
        'major-version.txt',
    )
    with open(path) as f:
        return f.read()

VERSION = _version()


def _github_download_url(
    url=URL,
    version=VERSION,
):
    return "{url}/archive/{version}.tar.gz".format(
        url=url,
        version=version
    )


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)

    def run_tests(self):
        #import here, because outside the eggs aren't loaded
        import pytest
        errno = pytest.main()
        sys.exit(errno)


setuptools.setup(
    name=NAME,
    version=VERSION,
    author="j3ffhubb",
    author_email="j3ffhubb@noreply.github.com",
    license="GPL3",
    description=DESCRIPTION,
    long_description=DESCRIPTION,
    url=URL,
    packages=setuptools.find_packages(
        exclude=(
            "scripts",
            "test",
            "test.*",
            "*.test",
            "*.test.*",
        ),
    ),
    include_package_data=True,
    install_requires=[
        'argcomplete',
        'pymarshal',
        'PyYAML',
    ],
    tests_require=[
        'pytest',
        'pytest-cov',
    ],
    extras_require={},
    cmdclass={
        'test': PyTest,
    },
    setup_requires=[
        'pytest-runner',
    ],
    # PyPI
    download_url=_github_download_url(),
    keywords=[],
    scripts=[
        'scripts/musikernel3.py',
    ],
)
