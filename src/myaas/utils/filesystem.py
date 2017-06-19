from os import rename as _mv
from os.path import getsize
from shutil import rmtree as _rmtree
from subprocess import call as _call

from myaas import settings


def copy_tree(src, dest):
    # reflink=auto will use copy on write if supported, always, forces it
    mode = "always" if settings.FORCE_COW else "auto"
    _call(["cp", "-r", f"--reflink={mode}", src, dest])


def rm_tree(path):
    _rmtree(path)


def rename(origin, destination):
    _mv(origin, destination)

def is_empty(path):
    return not getsize(path) > 100
