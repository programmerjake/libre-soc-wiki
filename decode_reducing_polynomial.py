from .state import ST


def decode_reducing_polynomial():
    """returns the decoded reducing polynomial as an integer.
        Note: the returned integer is `XLEN + 1` bits wide.
    """
    v = ST.GFBREDPOLY & ((1 << ST.XLEN) - 1)  # mask to XLEN bits
    if v == 0 or v == 2:  # GF(2)
        return 0b10  # degree = 1, poly = x
    if (v & 1) == 0:
        # all reducing polynomials of degree > 1 must have the LSB set,
        # because they must be irreducible polynomials (meaning they
        # can't be factored), if the LSB was clear, then they would
        # have `x` as a factor. Therefore, we can reuse the LSB clear
        # to instead mean the polynomial has degree XLEN.
        v |= 1 << ST.XLEN
        v |= 1  # LSB must be set
    return v
