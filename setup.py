#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup

from beamer import __version__, __license__, __author__, __email__

with open('README.md') as f:
    long_description = f.read()

setup(
    name='beamer',
    description='Simplistic CLI for toggling and positioning a secondary monitor or projector',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/philer/beamer',
    version=__version__,
    license=__license__,
    author=__author__,
    author_email=__email__,
    keywords='cli xrandr beamer mirror screen',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only',
        'Operating System :: POSIX :: Linux',
        'Topic :: Desktop Environment',
        'Topic :: Utilities',
        'Natural Language :: English',
    ],
    python_requires='>=3',
    py_modules=['beamer'],
    entry_points={'console_scripts': ['beamer = beamer:main']},
)
