#! /usr/bin/env python3

"""
Store and find files via tags.

TODO ls tags
TODO add/remove tags
TODO add search
"""

import sys
import argparse
import os
from os import path
from collections import namedtuple
from fnmatch import fnmatch

CONF_NAME = "tag.conf"
FILES_DIR = "files"

File = namedtuple("File", "name tags dir_path")

StorageInfo = namedtuple("StorageInfo", "files all_tags ")


class MatchAnd(object):
    def __init__(self, tags, not_tags):
        self._tags = tags or []
        self._not_tags = not_tags or []

    @property
    def name(self):
        return (
            "".join(("+"+x for x in sorted(self._tags)))
            + "".join(("-"+x for x in sorted(self._not_tags)))
        )

    def match(self, tags):
        for t in self._tags:
            if t not in tags:
                return False

        for t in self._not_tags:
            if t in tags:
                return False

        return True


def matcher_from_args(args):
    return MatchAnd(args.tag, args.exclude)


def tags_from_dir(d):
    result = []
    head = d
    while head != '':
        head, tail = path.split(head)
        if tail and tail != ".":
            result.append(tail)
    result.reverse()
    return result


def find_files(tag_path):
    dirs = ((p, path.relpath(p, tag_path), fs) for p, ds, fs in os.walk(tag_path))
    for p, d, fs in dirs:
        tags = tags_from_dir(d)
        for f in fs:
            yield File(f, tags, p)


def storage_info(file_list):
    all_tags = set()
    files = {}
    for f in file_list:
        name, tags, p = f
        if name in files:
            raise Exception("Duplicate file: %s" % name)
        files[name] = f
        all_tags.update(tags)
    return StorageInfo(files, all_tags)


def create_empty_dir(p):
    if path.exists(p):
        if path.isdir(p):
            if len(os.listdir(p)) != 0:
                raise Exception("%s is not empty" % p)
            return  # everything is already ok
        else:
            raise Exception("%s is not a directory" % p)
    else:
        os.makedirs(p)


def touch(p):
    with open(p, mode="w"):
        pass


def find_tag_dir(args):
    given_path = args.dir
    p = given_path
    while True:
        if path.isfile(path.join(p, CONF_NAME)):
            return p
        p, t = path.split(p)
        if t=="":
            break
    raise Exception("No tag store found in the directory %s" % given_path)


def init(args):
    p = path.expanduser(args.dir)
    create_empty_dir(p)
    touch(path.join(p, CONF_NAME))
    os.mkdir(path.join(p, FILES_DIR))


def filter_files(globs, matcher, files):
    def _impl(f):
        if not matcher.match(f.tags):
            return False

        for g in globs:
            if fnmatch(f.name, g):
                return True
        return False

    return filter(_impl, files)


def ls(args):
    globs = args.glob or ["*"]
    tag_path = path.join(find_tag_dir(args), FILES_DIR)
    info = storage_info(find_files(tag_path))
    filtered = filter_files(globs, matcher_from_args(args), info.files.values())

    for f in filtered:
        print(f.name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dir", nargs="?", default=os.getcwd(),
                        help="the directory of the tag file store")
    sub_parsers = parser.add_subparsers()
    init_parser = sub_parsers.add_parser("init", help="Initialize a directory as tag file store")
    init_parser.set_defaults(func=init)

    tag_expr_parser = argparse.ArgumentParser(add_help=False)
    tag_expr_parser.add_argument("-t", "--tag", nargs="*",
                                 help="Only show files with this tag")
    tag_expr_parser.add_argument("-n", "--exclude", nargs="*",
                                 help="Only show files without this tag")

    ls_parser = sub_parsers.add_parser("ls", help="List files", parents=[tag_expr_parser])
    ls_parser.add_argument("glob", nargs="*",
                           help="file patterns to show")
    ls_parser.set_defaults(func=ls)

    args = parser.parse_args()
    args.func(args)
#    try:
#        args.func(args)
#    except Exception as e:
#        print(str(e))
#        sys.exit(1)


if __name__ == "__main__":
    main()
