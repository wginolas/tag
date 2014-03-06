#! /usr/bin/env python3

"""
Store and find files via tags.

TODO ls
TODO add/remove tags
TODO add search
"""

import sys
import argparse
import os
from collections import namedtuple

File = namedtuple("File", "name tags dir_path")

StorageInfo = namedtuple("StorageInfo", "files all_tags ")

CONF_NAME = "tag.conf"
FILES_DIR = "files"

def tags_from_dir(d):
    result = []
    head = d
    while head != '':
        head, tail = os.path.split(head)
        if tail and tail != ".":
            result.append(tail)
    result.reverse()
    return result


def find_files(path):
    dirs = ((p, os.path.relpath(p, path), fs) for p, ds, fs in os.walk(path))
    for p, d, fs in dirs:
        tags = tags_from_dir(d)
        for f in fs:
            yield File(f, tags, p)


def storage_info(file_list):
    all_tags = set()
    files = {}
    for f in file_list:
        name, tags, path = f
        if name in files:
            raise Exception("Duplicate file: %s" % name)
        files[name] = f
        all_tags.update(tags)
    return StorageInfo(files, all_tags)


def create_empty_dir(path):
    if os.path.exists(path):
        if os.path.isdir(path):
            if len(os.listdir(path)) != 0:
                raise Exception("%s is not empty" % path)
            return  # everything is already ok
        else:
            raise Exception("%s is not a directory" % path)
    else:
        os.makedirs(path)


def touch(path):
    with open(path, mode="w"):
        pass


def init(args):
    path = os.path.expanduser(args.dir)
    create_empty_dir(path)
    touch(os.path.join(path, CONF_NAME))
    os.mkdir(os.path.join(path, FILES_DIR))


def main():
    parser = argparse.ArgumentParser()
    sub_parsers = parser.add_subparsers()
    init_parser = sub_parsers.add_parser("init", help="Initialize a directory asd tag file store")
    init_parser.add_argument("dir", nargs="?", default=os.getcwd(),
                             help="the directory to initialize")
    init_parser.set_defaults(func=init)

    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as e:
        print(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
