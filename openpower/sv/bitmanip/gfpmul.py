from .state import ST


def gfpmul(a, b):
    return (a * b) % ST.GFPRIME
