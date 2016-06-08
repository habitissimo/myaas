from os import rename as _mv
from shutil import rmtree as _rmtree
from subprocess import call as _call


def copy_tree(src, dest):
    # reflink=auto will use copy on write if supported
    _call(["cp", "-r", "--reflink=auto", src, dest])


def rm_tree(path):
    _rmtree(path)


def rename(origin, destination):
    _mv(origin, destination)
