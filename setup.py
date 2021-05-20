#!/usr/bin/env python

from setuptools import setup

GIT_REPO = "maf-lib"
PACKAGE = "maflib"

GIT_REPO_URL = "https://github.com/NCI-GDC/{}".format(GIT_REPO)


setup(
    url=GIT_REPO_URL,
    use_scm_version={"relative_to": __file__, 'write_to': f'{PACKAGE}/_version.py'},
    setup_requires=['setuptools_scm'],
)

# __END__
