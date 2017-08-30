#!/usr/bin/env python
from __future__ import generators
from __future__ import with_statement

import os
import runpy
from codecs import open

from setuptools import setup, find_packages

# Based on https://github.com/pypa/sampleproject/blob/master/setup.py
# and https://python-packaging-user-guide.readthedocs.org/

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

VERSION = runpy.run_path(os.path.join(here, "js2esi", "version.py"))["VERSION"]

setup(
    name="js2esi",
    version=VERSION,
    description="A primitive js to esi compiler. Write JS that will generate usable esi.",
    long_description=long_description,
    url="https://www.akamai.com",
    author="Colin Bendell",
    author_email="colinb@akamai.com",
    license="Apache2",
    keywords='js akamai esi edge side includes language',
    classifiers=[
        "License :: OSI Approved :: Apache2 License",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Environment :: Console :: Curses",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Internet",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: Proxy Servers",
        "Topic :: Software Development :: Testing"
    ],
    packages=find_packages(include=[
        "js2esi", "js2esi.*",
    ]),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'js2esi  = js2esi.tools.main:js2esi',
            'esi2js = js2esi.tools.main:esi2js',
        ]
    },
    # https://packaging.python.org/en/latest/requirements/#install-requires
    # It is not considered best practice to use install_requires to pin dependencies to specific versions.
    install_requires=[
        'ply>=3.4',
    ],
    extras_require={
        'dev': [
            "pytest>=3.1",
            "nose>=1.3.1"
        ],
        'examples': [
        ]
    }
)

