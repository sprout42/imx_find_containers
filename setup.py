#!/usr/bin/env python3

from setuptools import setup, find_packages


setup(
    name='find_containers',
    packages=find_packages(),

    entry_points={
        'console_scripts': ['find_containers=find_containers:main']
    }
)