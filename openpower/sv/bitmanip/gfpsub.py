from .state import ST


def gfpsub(a, b):
    return (a - b) % ST.GFPRIME
