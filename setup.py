try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name = "maf-lib",
    author = "Nils Homer",
    author_email = "nils@fulcrumgenomics.com",
    version = 0.1,
    description = "mutation annotation format library",
    url = "https://github.com/NCI-GDC/maf-lib",
    license = "Apache 2.0",
    packages = ["maflib", "maftools"],
    package_dir = {"maflib" : "src/maflib", "maftools" : "src/maftools"},
    package_data = {'maflib': ['resources/*.json']},
    install_requires = [],
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],
    entry_points= {
        'console_scripts': [
            'maftools = maftools.__main__:main'
        ]
    },
    include_package_data=True,
)
