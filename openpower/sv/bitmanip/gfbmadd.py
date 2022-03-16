from .state import ST
from .decode_reducing_polynomial import decode_reducing_polynomial
from .clmul import clmul
from .cldivrem import cldivrem


def gfbmadd(a, b, c):
    v = clmul(a, b) ^ c
    red_poly = decode_reducing_polynomial()
    q, r = cldivrem(v, red_poly, width=ST.XLEN + 1)
    return r
