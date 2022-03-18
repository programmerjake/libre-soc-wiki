from .state import ST


def gfpinv(a):
    # based on Algorithm ExtEucdInv from:
    # https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.90.5233&rep=rep1&type=pdf
    p = ST.GFPRIME
    assert p >= 2, "GFPRIME isn't a prime"
    assert a != 0, "TODO: decide what happens for division by zero"
    assert isinstance(a, int) and 0 < a < p, "a out of range"
    if p == 2:
        return 1  # the only value possible

    u = p
    v = a
    r = 0
    s = 1
    while v > 0:
        if u & 1 == 0:
            u >>= 1
            if r & 1 == 0:
                r >>= 1
            else:
                r = (r + p) >> 1
        elif v & 1 == 0:
            v >>= 1
            if s & 1 == 0:
                s >>= 1
            else:
                s = (s + p) >> 1
        else:
            x = u - v
            if x > 0:
                u = x
                r -= s
                if r < 0:
                    r += p
            else:
                v = -x
                s -= r
                if s < 0:
                    s += p
    if r > p:
        r -= p
    if r < 0:
        r += p
    return r
