#!/usr/bin/env python

import shelve
import argparse
import re
import sys
from os import path


class Blast:
    DEFAULT_DB_PATH = path.expanduser(path.join('~', '.blast.db'))

    def __init__(self, path=None):
        if path is None:
            self.db_path = self.DEFAULT_DB_PATH
        else:
            self.db_path = path
        self.shelve = shelve.open(self.db_path)
        self.entries = self.shelve.get('entries', {})
        self.opened = True

    @staticmethod
    def is_valid_key(key):
        reg = r'[\w]+(\.[\w]+)?$'
        return re.match(reg, key)

    def clear(self):
        self.entries.clear()

    def get_list(self, key=None):
        if key is not None:
            keys = [name for name in self if name.startswith(key + '.')]
        else:
            keys = list(self)
        return sorted(keys)

    @classmethod
    def validate_key(cls, key):
        if not cls.is_valid_key(key):
            print('Error: Invalid key: `{0}`\n'.format(key) +
                    'Expected format: `<word1>[.<word2>]` ' +
                    'where words consist of letters, numbers and underscores')
            sys.exit(1)

    ### Commands ###
    def cmd_get(self, args):
        key = args.key
        self.validate_key(key)
        try:
            print(self[key])
        except KeyError:
            print('Error: Key not found!')

    def cmd_set(self, args):
        key = args.key
        self.validate_key(key)
        value = args.value
        if value is None:
            value = sys.stdin.read()
        self[key] = value

    def cmd_delete(self, args):
        key = args.key
        self.validate_key(key)
        try:
            del self[key]
        except KeyError:
            print('Error: Key not found!')

    def cmd_list(self, args):
        key = args.key
        if key is not None:
            self.validate_key(key)
        entries = self.get_list(key)
        if not entries:
            print('There are no entries!')
            return
        print('\n'.join(entries))
    ###^ Commands ^###

    ### Container interface ###
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
    ###^ Container interface ^###

    ### Resource management ###
    def close(self):
        self.shelve['entries'] = self.entries
        self.shelve.close()
        self.opened = False

    def __enter__(self):
        return self

    def __exit__(self, *_):
        if self.opened:
            self.close()
        return False

    def __del__(self):
        if self.opened:
            self.close()
    ###^ Resource management ^###




def main(args=None):
    with Blast() as blast:
        parser = argparse.ArgumentParser(prog='blast', 
                                        description='Your command line key-value store')
        subparsers = parser.add_subparsers(help='Sub-commands')

        get_parser = subparsers.add_parser('get', help='get help', description='Get value')
        get_parser.add_argument('key')
        get_parser.set_defaults(func=blast.cmd_get)

        set_parser = subparsers.add_parser('set', help='set help')
        set_parser.add_argument('key')
        set_parser.add_argument('value', nargs='?')
        set_parser.set_defaults(func=blast.cmd_set)

        delete_parser = subparsers.add_parser('delete', help='delete help')
        delete_parser.add_argument('key')
        delete_parser.set_defaults(func=blast.cmd_delete)

        list_parser = subparsers.add_parser('list', help='list help')
        list_parser.add_argument('key', nargs='?')
        list_parser.set_defaults(func=blast.cmd_list)

        args = parser.parse_args(args)
        args.func(args)

if __name__ == '__main__':
    main()
