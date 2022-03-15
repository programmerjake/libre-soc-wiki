"""Polynomials with GF(2) coefficients."""


def pack_poly(poly):
    """`poly` is a list where `poly[i]` is the coefficient for `x ** i`"""
    retval = 0
    for i, v in enumerate(poly):
        retval |= v << i
    return retval


def unpack_poly(v):
    """returns a list `poly`, where `poly[i]` is the coefficient for `x ** i`.
    """
    poly = []
    while v != 0:
        poly.append(v & 1)
        v >>= 1
    return poly
