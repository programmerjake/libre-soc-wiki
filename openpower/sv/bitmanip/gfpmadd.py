from .state import ST


def gfpmadd(a, b, c):
    return (a * b + c) % ST.GFPRIME
