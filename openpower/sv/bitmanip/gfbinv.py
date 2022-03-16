from .decode_reducing_polynomial import decode_reducing_polynomial
from .cldivrem import degree


def gfbinv(a):
    """compute the GF(2^m) inverse of `a`."""
    # Derived from Algorithm 3, from [7] in:
    # https://ftp.libre-soc.org/ARITH18_Kobayashi.pdf

    s = decode_reducing_polynomial()
    m = degree(s)
    assert a >> m == 0, "`a` is out-of-range"
    r = a
    v = 0
    u = 1
    delta = 0

    for _ in range(2 * m):
        # could use count-leading-zeros here to skip ahead
        if r >> m == 0:  # if the MSB of `r` is zero
            r <<= 1
            u <<= 1
            delta += 1
        else:
            if s >> m != 0:  # if the MSB of `s` isn't zero
                s ^= r
                v ^= u
            s <<= 1
            if delta == 0:
                r, s = s, r  # swap r and s
                u, v = v << 1, u  # shift v and swap
                delta = 1
            else:
                u >>= 1
                delta -= 1
    if a == 0:
        # we specifically choose 0 as the result of inverting 0, rather than an
        # error or undefined, since that's what Rijndael needs.
        return 0
    return u
