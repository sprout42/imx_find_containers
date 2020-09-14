import argparse

from . import utils
from . import container

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
        containers = container.find(item, args.increment, args.verbose)
        if containers:
            results[item] = containers

        for c in containers:
            print(c)

    if results:
        export(results)

    return 0
