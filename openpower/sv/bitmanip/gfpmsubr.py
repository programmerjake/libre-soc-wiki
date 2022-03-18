from .state import ST


def gfpmsubr(a, b, c):
    return (c - a * b) % ST.GFPRIME
