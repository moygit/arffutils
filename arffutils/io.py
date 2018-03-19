#!/usr/bin/env python

"""Context manager that can handle StringIO objects, files, and handles.

Example
----
>>> with io_handler(f) as fh:
>>>     lines = f.readlines()

>>> with io_handler(f, "w") as fh:
>>>     fh.writelines(["abcd\n", "efgh\n"])

Useful when you don't know in advance what type of object `f` will be.
"""

from contextlib import contextmanager
import yaml


@contextmanager
def io_handler(file_, mode='rt'):
    "The context-manager itself: open, yield, and close."
    # Is it a path or a handle?
    handle = None
    if hasattr(file_, 'read'):
        handle = file_
    else:
        handle = open(file_, mode)
    yield handle
    # Close if handle; ignore if path.
    # We don't want to decide this based on whether there's a close
    # method because that would mess up writable StringIO objects.
    if handle != file_:
        handle.close()


def read_yaml(yml_file_path):
    "Read the given yaml file."
    with io_handler(yml_file_path) as yml_file:
        return yaml.load(yml_file)
