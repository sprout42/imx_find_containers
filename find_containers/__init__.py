#!/usr/bin/env python
#
# Adapted from info in NXP docs:
#   - IMX8DQXPRM.pdf
#   - AN12056.pdf
#
# And info from following tools:
#   - https://source.codeaurora.org/external/imx/uboot-imx
#   - https://source.codeaurora.org/external/imx/imx-mkimage/
#   - https://www.nxp.com/webapp/Download?colCode=IMX_CST_TOOL_NEW&location=null

import re
import os
import argparse
import enum
import struct

from . import utils
from .container import Container


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path',
            help='Path to search for i.MX containers in all binaries')
    parser.add_argument('--verbose', '-v', action='store_true',
            help='verbose debug/searching printouts')
    parser.add_argument('--increment', '-i', default=4, type=int,
            help='The amount to increment each address when searching for a container')
    args = parser.parse_args()

    results = {}
    file_list = utils.recursive_scandir(args.path)
    for item in file_list:
        print(f'Searching {item}')
        containers = find(item, args.increment, args.verbose)
        if containers:
            results[item] = containers

        for c in containers:
            print(c)

    if results:
        export(results)
