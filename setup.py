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


setup()

# __END__
