from .state import ST
from .decode_reducing_polynomial import decode_reducing_polynomial
from .clmul import clmul
from .cldivrem import cldivrem


def gfbmul(a, b):
    product = clmul(a, b)
    red_poly = decode_reducing_polynomial()
    q, r = cldivrem(product, red_poly, width=ST.XLEN + 1)
    return r
