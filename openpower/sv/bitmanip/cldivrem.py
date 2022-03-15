def cldivrem(n, d, width):
    """ Carry-less Division and Remainder.
        `n` and `d` are integers, `width` is the number of bits needed to hold
        each input/output.
        Returns a tuple `q, r` of the quotient and remainder.
    """
    assert d != 0, "TODO: decide what happens on division by zero"
    assert 0 <= n < 1 << width, f"bad n (doesn't fit in {width}-bit uint)"
    assert 0 <= d < 1 << width, f"bad d (doesn't fit in {width}-bit uint)"
    r = n
    q = 0
    d <<= width
    for _ in range(width):
        d >>= 1
        q <<= 1
        if degree(d) == degree(r):
            r ^= d
            q |= 1
    return q, r


def degree(v):
    """the degree of the GF(2) polynomial `v`. `v` is a non-negative integer.
    """
    assert v >= 0
    retval = -1
    while v != 0:
        retval += 1
        v >>= 1
    return retval
