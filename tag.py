#! /usr/bin/env python3

"""
Store and find files via tags.

TODO add search
TODO add file
TODO import
TODO help
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

StorageInfo = namedtuple("StorageInfo", "tag_path files all_tags ")


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
    dirs = ((path.relpath(p, tag_path), fs) for p, ds, fs in os.walk(tag_path))
    for d, fs in dirs:
        tags = tags_from_dir(d)
        for f in fs:
            yield File(f, tags, d)


def storage_info(args):
    tag_path = path.join(find_tag_dir(args), FILES_DIR)
    file_list = find_files(tag_path)

    all_tags = set()
    files = {}
    for f in file_list:
        name, tags, p = f
        if name in files:
            raise Exception("Duplicate file: %s" % name)
        files[name] = f
        all_tags.update(tags)
    return StorageInfo(tag_path, files, all_tags)


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


def glob_files(info, args):
    globs = args.glob or ["*"]
    return filter_files(globs, matcher_from_args(args), info.files.values())


def abs_path(info, f):
    if f.dir_path == ".":
        return path.join(info.tag_path, f.name)
    else:
        return path.join(info.tag_path, f.dir_path, f.name)

def ls(args):
    info = storage_info(args)
    filtered = glob_files(info, args)

    for f in sorted(filtered, key=lambda x: x.name):
        if args.show_path:
            left = abs_path(info, f)
        else:
            left = f.name

        if args.show_tags:
            right = " " + " ".join(sorted(f.tags))
        else:
            right = ""

        print(left+right)


def edit(args):
    info = storage_info(args)
    filtered = glob_files(info, args)
    for f in filtered:
        new_tags = set(f.tags)

        if args.remove:
            for t in args.remove:
                if t in new_tags:
                    new_tags.remove(t)

        if args.add:
            for t in args.add:
                new_tags.add(t)

        if len(new_tags) == 0:
            new_dir = ""
        else:
            new_dir = path.join(*sorted(new_tags))

        old_file = abs_path(info, f)
        new_file = path.join(info.tag_path, new_dir, f.name)
        if old_file != new_file:
            #print(old_file, new_file)
            os.renames(old_file, new_file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dir", nargs="?", default=os.getcwd(),
                        help="the directory of the tag file store")
    sub_parsers = parser.add_subparsers()
    init_parser = sub_parsers.add_parser("init", help="Initialize a directory as tag file store")
    init_parser.set_defaults(func=init)

    tag_expr_parser = argparse.ArgumentParser(add_help=False)
    tag_expr_parser.add_argument("-t", "--tag", action="append",
                                 help="Only show files with this tag")
    tag_expr_parser.add_argument("-n", "--exclude", action="append",
                                 help="Only show files without this tag")
    tag_expr_parser.add_argument("glob", nargs="*",
                           help="file patterns to show")

    ls_parser = sub_parsers.add_parser("ls", help="List files", parents=[tag_expr_parser])
    ls_parser.add_argument("-l", "--show-tags", action="store_true",
                           help="show the tags of each file")
    ls_parser.add_argument("-p", "--show-path", action="store_true",
                           help="show the path of each file")
    ls_parser.set_defaults(func=ls)

    edit_parser = sub_parsers.add_parser("edit", help="Edit the tags of filed", parents=[tag_expr_parser])
    edit_parser.add_argument("-a", "--add", action="append",
                             help="Add a tag to the files")
    edit_parser.add_argument("-r", "--remove", action="append",
                             help="Remove a tag from the files")
    edit_parser.set_defaults(func=edit)

    args = parser.parse_args()
    args.func(args)
#    try:
#        args.func(args)
#    except Exception as e:
#        print(str(e))
#        sys.exit(1)


if __name__ == "__main__":
    main()
