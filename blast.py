#!/usr/bin/env python

import argparse
import re
import sys
import subprocess
from os import path
from functools import wraps

from fridge import Fridge


class Platform:
    if 'win32' in sys.platform or 'cygwin' in sys.platform:
        OPEN_COMMAND = 'start'
        CLIP_ARGS = ['clip']
    elif 'darwin' in sys.platform:
        OPEN_COMMAND = 'open'
        CLIP_ARGS = ['pbcopy']
    else:
        OPEN_COMMAND = 'xdg-open'
        CLIP_ARGS = ['xclip', '-selection', 'clipboard']

    @classmethod
    def open(cls, url):
        subprocess.call([cls.OPEN_COMMAND, url])

    @classmethod
    def copy_to_clipboard(cls, text):
        with subprocess.Popen(cls.CLIP_ARGS, stdin=subprocess.PIPE) as process:
            process.communicate(input=text.encode())


class Blast:
    DEFAULT_DB_PATH = path.expanduser(path.join('~', '.blast_db.json'))

    def __init__(self, path=None):
        if path is None:
            self.db_path = self.DEFAULT_DB_PATH
        else:
            self.db_path = path
        self.entries = Fridge(self.db_path)
        self.closed = False

    def validating_key(func):
        @wraps(func)
        def wrapper(self, args):
            if args.key is not None:
                self.validate_key(args.key)
            try:
                func(self, args)
            except KeyError:
                print('Error: Key not found!')
        return wrapper

    @staticmethod
    def is_valid_key(key):
        reg = r'[\w]+(\.[\w]+)?$'
        return re.match(reg, key)

    def clear(self, key=None):
        if key is not None:
            new_entries = {k: v for k, v in self.entries.items()
                            if not k.startswith(key + '.')}
        else:
            new_entries = {}
        self.entries.clear()
        self.entries.update(new_entries)

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
    @validating_key
    def cmd_get(self, args):
        key = args.key
        val = self[key]
        Platform.copy_to_clipboard(val)
        print(val)

    @validating_key
    def cmd_set(self, args):
        key = args.key
        value = args.value
        if value is None:
            value = sys.stdin.read()
        self[key] = value

    @validating_key
    def cmd_delete(self, args):
        key = args.key
        del self[key]

    @validating_key
    def cmd_clear(self, args):
        key = args.key
        self.clear(key)

    @validating_key
    def cmd_list(self, args):
        key = args.key
        entries = self.get_list(key)
        if not entries:
            print('There are no entries!')
            return
        print('\n'.join(entries))

    @validating_key
    def cmd_open(self, args):
        key = args.key
        val = self[key]
        Platform.open(val)

    @validating_key
    def cmd_echo(self, args):
        key = args.key
        print(self[key])

    def cmd_move(self, args):
        key = args.key
        dest = args.dest
        self.validate_key(key)
        self.validate_key(dest)
        self[dest] = self[key]
        del self[key]
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
        self.entries.close()
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
        return False

    def __del__(self):
        self.close()
    ###^ Resource management ^###




def main(args=None):
    with Blast() as blast:
        parser = argparse.ArgumentParser(prog='blast', 
                                        description='Your command line key-value store')
        subparsers = parser.add_subparsers(help='Sub-commands')

        # get
        get_parser = subparsers.add_parser('get', help='get value', description='Get value by key')
        get_parser.add_argument('key')
        get_parser.set_defaults(func=blast.cmd_get)

        # set
        set_parser = subparsers.add_parser('set', help='set value',
                        description='Set the value at key. If the value is not passed, read it from stdin.')
        set_parser.add_argument('key')
        set_parser.add_argument('value', nargs='?')
        set_parser.set_defaults(func=blast.cmd_set)

        # delete
        delete_parser = subparsers.add_parser('delete', help='delete value',
                            description='Delete the value at key')
        delete_parser.add_argument('key')
        delete_parser.set_defaults(func=blast.cmd_delete)

        # list
        list_parser = subparsers.add_parser('list', help='list the keys',
                        description='List all the keys. If the key is passed, list only keys in that '
                                    '"namespace".')
        list_parser.add_argument('key', nargs='?')
        list_parser.set_defaults(func=blast.cmd_list)

        # clear
        clear_parser = subparsers.add_parser('clear', help='clear the entries',
                        description='Clears all the entries. If the key is passed, removes only keys in that '
                                    '"namespace".')
        clear_parser.add_argument('key', nargs='?')
        clear_parser.set_defaults(func=blast.cmd_clear)

        # open
        open_parser = subparsers.add_parser('open', help='open the url in entry',
                        description='Open filepath or URL stored in the entry specified by key')
        open_parser.add_argument('key', nargs='?')
        open_parser.set_defaults(func=blast.cmd_open)

        # echo
        echo_parser = subparsers.add_parser('echo', help='echo value',
                        description='Print value of key without copying it to clipboard')
        echo_parser.add_argument('key')
        echo_parser.set_defaults(func=blast.cmd_echo)

        # move
        move_parser = subparsers.add_parser('move', help='move value',
                        description='move value from key to dest')
        move_parser.add_argument('key')
        move_parser.add_argument('dest')
        move_parser.set_defaults(func=blast.cmd_move)

        args = parser.parse_args(args)
        args.func(args)

if __name__ == '__main__':
    main()
