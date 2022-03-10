# a mish-mash of various GF(2^m) functions from different sources
# on the internet which help demonstrate arithmetic in GF(2^m)
# these are intended to be implemented in hardware, so the basic
# primitives need to be *real* basic: XOR, shift, AND, OR, etc.
#
# development discussion and links at:
# https://bugs.libre-soc.org/show_bug.cgi?id=782

from functools import reduce

# https://stackoverflow.com/questions/45442396/


def gf_degree(a):
    res = 0
    a >>= 1
    while (a != 0):
        a >>= 1
        res += 1
    return res


# useful constants used throughout this module
degree = mask1 = mask2 = polyred = None


def getGF2():
    """reconstruct the polynomial coefficients of g(x)
    """
    return polyred | mask1


# original at https://jhafranco.com/tag/binary-finite-field/
def setGF2(irPoly):
    """Define parameters of binary finite field GF(2^m)/g(x)
       - irPoly: coefficients of irreducible polynomial g(x)
    """
    # degree: extension degree of binary field
    global degree, mask1, mask2, polyred
    degree = gf_degree(irPoly)

    def i2P(sInt):
        """Convert an integer into a polynomial"""
        return [(sInt >> i) & 1
                for i in reversed(range(sInt.bit_length()))]

    mask1 = mask2 = 1 << degree
    mask2 -= 1
    polyred = reduce(lambda x, y: (x << 1) + y, i2P(irPoly)[1:])


# original at https://jhafranco.com/tag/binary-finite-field/
def multGF2(p1, p2):
    """Multiply two polynomials in GF(2^m)/g(x)"""
    p = 0
    while p2:
        if p2 & 1:
            p ^= p1
        p1 <<= 1
        if p1 & mask1:
            p1 ^= polyred
        p2 >>= 1
    return p & mask2


# https://github.com/jpahullo/python-multiprocessing/
# py_ecc/ffield.py
def divmodGF2(f, v):
    fDegree, vDegree = gf_degree(f), gf_degree(v)
    res, rem = 0, f
    i = fDegree
    mask = 1 << i
    while (i >= vDegree):
        if (mask & rem):
            res ^= (1 << (i - vDegree))
            rem ^= (v << (i - vDegree))
        i -= 1
        mask >>= 1
    return (res, rem)


# https://en.m.wikibooks.org/wiki/Algorithm_Implementation/Mathematics/Extended_Euclidean_algorithm
def xgcd(a, b):
    """return (g, x, y) such that a*x + b*y = g = gcd(a, b)"""
    x0, x1, y0, y1 = 0, 1, 1, 0
    while a != 0:
        (q, a), b = divmodGF2(b, a), a
        y0, y1 = y1, y0 ^ multGF2(q, y1)
        x0, x1 = x1, x0 ^ multGF2(q, x1)
    return b, x0, y0


# https://bugs.libre-soc.org/show_bug.cgi?id=782#c33
# https://ftp.libre-soc.org/ARITH18_Kobayashi.pdf
def gf_invert(a):

    s = getGF2()  # get the full polynomial (including the MSB)
    r = a
    v = 0
    u = 1
    j = 0

    for i in range(1, 2*degree+1):
        # could use count-trailing-1s here to skip ahead
        if r & mask1:          # test MSB of r
            if s & mask1:      # test MSB of s
                s ^= r
                v ^= u
            s <<= 1            # shift left 1
            if j == 0:
                r, s = s, r    # swap r,s
                u, v = v << 1, u  # shift v and swap
                j = 1
            else:
                u >>= 1        # right shift left
                j -= 1
        else:
            r <<= 1            # shift left 1
            u <<= 1            # shift left 1
            j += 1

    return u


if __name__ == "__main__":

    # Define binary field GF(2^3)/x^3 + x + 1
    setGF2(0b1011)  # degree 3

    # Evaluate the product (x^2 + x + 1)(x^2 + 1)
    x = multGF2(0b111, 0b101)
    print("%02x" % x)

    # Define binary field GF(2^8)/x^8 + x^4 + x^3 + x + 1
    # (used in Rijndael)
    # note that polyred has the MSB stripped!
    setGF2(0b100011011)  # degree 8

    # Evaluate the product (x^7 + x^2)(x^7 + x + 1)
    x = 0b10000100
    y = 0b10000011
    z = multGF2(x, y)
    print("%02x * %02x = %02x" % (x, y, z))

    # divide z by y into result/remainder
    res, rem = divmodGF2(z, y)
    print("%02x / %02x = (%02x, %02x)" % (z, y, res, rem))

    # reconstruct x by multiplying divided result by y and adding the remainder
    x1 = multGF2(res, y)
    print("%02x == %02x" % (z, x1 ^ rem))  # XOR is "add" in GF2

    # demo output of xgcd
    print(xgcd(x, y))

    # for i in range(1, 256):
    #   print (i, gf_invert(i))

    # show how inversion-and-multiply works.  answer here should be "x":
    # z = x * y, therefore z * (1/y) should equal "x"
    y1 = gf_invert(y)
    z1 = multGF2(z, y1)
    print(hex(polyred), hex(y1), hex(x), "==", hex(z1))
