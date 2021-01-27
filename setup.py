#!/usr/bin/env python3

from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='imx_find_containers',
    packages=find_packages(),

    entry_points={
        'console_scripts': ['imx_find_containers=imx_find_containers:main']
    },
    install_requires=required,
)
