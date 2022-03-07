from functools import reduce

def gf_degree(a) :
  res = 0
  a >>= 1
  while (a != 0) :
    a >>= 1;
    res += 1;
  return res

# constants used in the multGF2 function
degree = mask1 = mask2 = polyred = None

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
        

def getGF2():
    """reconstruct the polynomial coefficients of g(x)
    """
    return polyred | mask1


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


def divmodGF2(f, v):
    fDegree, vDegree = gf_degree(f), gf_degree(v)
    res, rem = 0, f
    i = fDegree
    mask = 1 << i
    while (i >= vDegree):
        if (mask & rem):
            res ^= (1 << (i - vDegree))
            rem ^= ( v << (i - vDegree))
        i -= 1
        mask >>= 1
    return (res, rem)


def xgcd(a, b):
    """return (g, x, y) such that a*x + b*y = g = gcd(a, b)"""
    x0, x1, y0, y1 = 0, 1, 1, 0
    while a != 0:
        (q, a), b = divmodGF2(b, a), a
        y0, y1 = y1, y0 ^ multGF2(q , y1)
        x0, x1 = x1, x0 ^ multGF2(q , x1)
    return b, x0, y0


# https://bugs.libre-soc.org/show_bug.cgi?id=782#c33
# https://ftp.libre-soc.org/ARITH18_Kobayashi.pdf
def gf_invert(a) :

    s = polyred
    r = a
    v = 0
    u = 1
    j = 0

    for i in range(1, 2*degree+1):
        if r & mask1:
            if s & mask1:
                s ^= r
                v ^= u
            s <<= 1 # shift left 1
            if j == 0:
                r, s = s, r # swap r,s
                u, v = v<<1, u # shift v and swap
                j = 1
            else:
                u >>= 1 # right shift left
                j -= 1
        else:
            r <<= 1 # shift left 1
            u <<= 1 # shift left 1
            j += 1

    return u


if __name__ == "__main__":
  
    # Define binary field GF(2^3)/x^3 + x + 1
    setGF2(0b1011) # degree 3

    # Evaluate the product (x^2 + x + 1)(x^2 + 1)
    x = multGF2(0b111, 0b101)
    print("%02x" % x)
    
    # Define binary field GF(2^8)/x^8 + x^4 + x^3 + x + 1
    # (used in the Advanced Encryption Standard-AES)
    # note that polyred has the MSB stripped!
    setGF2(0b100011011) # degree 8
    
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
    print("%02x == %02x" % (z, x1 ^ rem))


    print(xgcd(x, y))

    #for i in range(1, 256):
    #   print (i, gf_invert(i))

    y1 = gf_invert(y)
    z1 = multGF2(z, y1)
    print(hex(polyred), hex(y1), hex(z1))

