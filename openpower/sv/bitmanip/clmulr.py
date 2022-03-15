from .clmul import clmul


def clmulh(a, b, XLEN):
    return clmul(a, b) >> (XLEN - 1)
