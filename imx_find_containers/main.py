import argparse

from . import utils
from . import container

def main():
    parser = argparse.ArgumentParser(
            prog=__package__,
            description='Tool to scrape metadata, find, and extract images from i.MX flash images')
    parser.add_argument('path',
            help='Path to search for i.MX containers in all binaries')
    parser.add_argument('--verbose', '-v', action='store_true',
            help='verbose debug/searching printouts')
    parser.add_argument('--increment', '-i', default=4, type=int,
            help='The amount to increment each address when searching for a container')
    parser.add_argument('--include-image-contents', '-I', action='store_true',
            help='Include contents of identified containers in the scan results file (increases time it takes to save scan results)')
    parser.add_argument('--extract', '-e', action='store_true',
            help='Extract the contents of any identified containers')
    parser.add_argument('--output-format', '-o', default='auto', choices=['auto', 'yaml', 'pickle'],
            help='Select if the scan results should be saved as a yaml or pickle')
    args = parser.parse_args()

    results = {}
    file_list = utils.recursive_scandir(args.path)
    for item in file_list:
        print(f'Searching {item}')
        containers = container.find(item, **vars(args))
        if containers:
            results[item] = containers

        if args.verbose:
            print('\nFound:')
            for c in containers:
                print(c)

    if results:
        print(vars(args))
        utils.export(results, **vars(args))

    return 0


__all__ = [
    'main',
]
