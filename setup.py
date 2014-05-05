#! /usr/bin/env python3
import codecs
from setuptools import setup

with codecs.open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name = "tag",
    version = "0.0.1",
    description = "Organize and find files with tags",
    long_description=long_description,
    setup_requires = "setuptools",
    packages = ["tag"],
    entry_points = {
        'console_scripts': [
            'tag = tag.tag:main'
        ]
    }
)