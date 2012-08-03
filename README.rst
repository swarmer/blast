#####
Blast
#####

Blast is your own command-line key-value store.
It is my reinterpretation of holman/boom.

The main usage is basically storing text snippets and links.

Installation
============

Drop `blast.py` somewhere in your `PATH`.

Example
=======
::

  $ blast set a 42
  $ blast list
  a
  $ blast get a
  42
  $ blast set numbers.a 550
  $ blast set numbers.b 12309
  $ blast list
  a
  numbers.a
  numbers.b
  $ blast clear numbers
  $ blast list
  a

Commands
========

The commands are:

- get
- set
- delete
- move
- list
- clear
- open
- copy

See ``blast --help`` or ``blast <command> --help`` for info.

Dependencies
============
Python 3.

Nose if you want to run ``nosetests``

License
=======
MIT (see LICENSE.txt).
