#!/usr/bin/env python

import shelve
import argparse
import re
import sys
from os import path


class Store:
    DB_PATH = path.expanduser(path.join('~', '.blast.db'))

    def __init__(self, path=None):
        if path is None:
            self.db_path = self.DB_PATH
        else:
            self.db_path = path

    def __getitem__(self, key):
        return self.entries[key]

    def __setitem__(self, key, value):
        self.entries[key] = value

    def __delitem__(self, key):
        del self.entries[key]

    def __iter__(self):
        return iter(self.entries)

    def __len__(self):
        return len(self.entries)

    def __contains__(self, item):
        return item in self.entries

    def __enter__(self):
        self.shelve = shelve.open(self.db_path)
        self.entries = self.shelve.get('entries', {})
        return self

    def __exit__(self, *_):
        self.shelve['entries'] = self.entries
        self.shelve.close()


def validate_key(key):
    reg = r'[\w]+(\.[\w]+)?$'
    if not re.match(reg, key):
        print('Invalid key: `{0}`\n'.format(key) +
                'Expected format: `<word1>[.<word2>]` ' +
                'where words consist of letters, numbers and underscores')
        sys.exit(1)

### Commands ###
def cmd_get(args):
    with Store() as store:
        key = args.key
        validate_key(key)
        try:
            print(store[key])
        except KeyError:
            print('Key not found!')

def cmd_set(args):
    with Store() as store:
        key = args.key
        validate_key(key)
        value = args.value
        if value is None:
            value = sys.stdin.read()
        store[key] = value

def cmd_delete(args):
    with Store() as store:
        key = args.key
        validate_key(key)
        try:
            del store[key]
        except KeyError:
            print('Key not found!')

def cmd_list(args):
    with Store() as store:
        if len(store) == 0:
            print('There are no entries!')
            return
        key = args.key
        if key is not None:
            validate_key(key)
            matching_entries = (name for name in store if name.startswith(key))
            print('\n'.join(matching_entries))
        else:
            print('\n'.join(store))
###^ Commands ^###

def main():
    parser = argparse.ArgumentParser(prog='blast', 
                                    description='Your command line key-value store')
    subparsers = parser.add_subparsers(help='Sub-commands')

    get_parser = subparsers.add_parser('get', help='get help', description='Get value')
    get_parser.add_argument('key')
    get_parser.set_defaults(func=cmd_get)

    set_parser = subparsers.add_parser('set', help='set help')
    set_parser.add_argument('key')
    set_parser.add_argument('value', nargs='?')
    set_parser.set_defaults(func=cmd_set)

    delete_parser = subparsers.add_parser('delete', help='delete help')
    delete_parser.add_argument('key')
    delete_parser.set_defaults(func=cmd_delete)

    list_parser = subparsers.add_parser('list', help='list help')
    list_parser.add_argument('key', nargs='?')
    list_parser.set_defaults(func=cmd_list)

    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
