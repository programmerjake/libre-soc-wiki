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
    r_shift = 0
    d_shift = 0
    msb = 1 << (width - 1)
    for _ in range(width):
        if r & msb:
            if d & msb:
                r ^= d
                q |= 1
            else:
                d <<= 1
                d_shift += 1
        else:
            if d & msb:
                r <<= 1
                q <<= 1
                r_shift += 1
            else:
                r <<= 1
                r_shift += 1
                d <<= 1
                d_shift += 1
    r >>= r_shift
    return q, r
