#!/usr/bin/env python3

from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

# optional YAML output requirements that can't quite be captured in 
# a requirements.txt file:
#   PyYAML>=5.4.1
#
# Also tested with:
#   ruamel.yaml>=0.16.12

setup(
    name='imx_find_containers',
    packages=find_packages(),

    entry_points={
        'console_scripts': ['imx_find_containers=imx_find_containers:main']
    },
    install_requires=required,
    extras_require={
        "YAML":  ["PyYAML>=5.4.1"],
    }
)
