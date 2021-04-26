#!/usr/bin/env python

import importlib
import os
import subprocess
from types import SimpleNamespace

from setuptools import Command, find_packages, setup

GIT_REPO = "maf-lib"
PACKAGE = "maflib"

PYPI_REPO = "bioinf-{}".format(PACKAGE)
GIT_REPO_URL = "https://github.com/NCI-GDC/{}".format(GIT_REPO)

INSTALL_REQUIRES = []

TESTS_REQUIRE = [
    'mock',
    'pytest',
    'pytest-cov',
]

DEV_REQUIRES = [
    'detect-secrets==0.13.1',
    'isort',
    'flake8',
    'pre-commit',
    'tox',
]


GIT_COMMANDS = SimpleNamespace(
    branch=["git", "rev-parse", "--abbrev-ref", "HEAD"],
    commit=["git", "rev-list", "--count", "HEAD"],
    hash=["git", "rev-parse", "HEAD"],
    shorthash=["git", "rev-parse", "--short", "HEAD"],
)


try:
    # Set versions if version file exists
    mod = importlib.import_module("{}".format(PACKAGE))
    __pypi_version__ = mod.__version__
except Exception:
    __pypi_version__ = '0'


def get_readme():
    lines = ''
    path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(path):
        with open(path) as fh:
            lines = fh.read()
    return lines


class PrintVersion(Command):
    description = "Print out specified version, default long version."
    user_options = [
        ("docker", None, "Print docker-friendly version."),
        ("hash", None, "Print commit hash."),
        ("pypi", None, "Print package version."),
    ]

    def initialize_options(self):
        self.docker = False
        self.hash = False
        self.pypi = False

    def finalize_options(self):
        pass

    def run(self):
        if self.pypi:
            print(__pypi_version__)
        elif self.docker:
            # Replace '+' in version with '.' for Docker tagging
            print(__pypi_version__.replace('+', '.'))
        elif self.hash:
            try:
                commit_hash = call_subprocess(GIT_COMMANDS.hash)
            except Exception:
                print('')
            else:
                print(commit_hash)
        else:
            print(__pypi_version__)


class Requirements(Command):
    description = "Write specified requirements to requirements.in"
    user_options = [
        ("install", None, "Bundles requirements for install."),
        ("dev", None, "Bundles all requirements for development."),
    ]

    def initialize_options(self):
        self.install = False
        self.dev = False

    def finalize_options(self):
        pass

    def run(self):
        REQUIREMENT = ['-c requirements.txt']
        if self.dev:
            reqs = REQUIREMENT + DEV_REQUIRES + TESTS_REQUIRE
            path = "dev-requirements.in"
        elif self.install:
            reqs = INSTALL_REQUIRES
            path = "requirements.in"
        else:
            raise ValueError("Choose one of install, test, or dev")
        self.write_requirements(path, reqs)
        return

    def write_requirements(self, path, reqs):
        with open(path, "w") as fh:
            fh.write("\n".join(reqs) + "\n")


def call_subprocess(cmd: list):
    """Return stdout of given command."""
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    stdout, _ = p.communicate()
    return stdout.decode().strip()


setup(
    name=PYPI_REPO,
    description="Mutation Annotation Format (MAF) library",
    author="Charles Czysz",
    author_email="czysz@uchicago.edu",
    long_description=get_readme(),
    url=GIT_REPO_URL,
    python_requires=">=3.6",
    include_package_data=True,
    packages=find_packages(),
    setup_requires=['setuptools_scm'],
    use_scm_version={
        "write_to": os.path.join(PACKAGE, "_version.py"),
        "fallback_version": __pypi_version__,
    },
    install_requires=INSTALL_REQUIRES,
    tests_require=TESTS_REQUIRE,
    cmdclass={"capture_requirements": Requirements, "print_version": PrintVersion},
)

# __END__
