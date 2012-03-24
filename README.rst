#####
Blast
#####

Blast is your own command-line key-value store.

The main usage is basically storing text snippets and links.

Example
=======
::

  $ blast set a 42
  $ blast list
  a
  $ blast get a
  42

Commands
========

The commands are:

- get
- set
- delete
- list
- clear

See '`blast --help`' or '`blast <command> --help`' for info.

Dependencies
============
Python 3.

Nose if you want to run ``nosetests``

License
=======
MIT (see LICENSE.txt).
