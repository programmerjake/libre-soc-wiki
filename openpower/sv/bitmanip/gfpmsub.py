from .state import ST


def gfpmsub(a, b, c):
    return (a * b - c) % ST.GFPRIME
