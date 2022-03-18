from .state import ST


def gfpadd(a, b):
    return (a + b) % ST.GFPRIME
