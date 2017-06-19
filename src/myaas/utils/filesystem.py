from os.path import getsize


def is_empty(path):
    return not getsize(path) > 100
