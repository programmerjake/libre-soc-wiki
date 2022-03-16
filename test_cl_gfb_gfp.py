from .state import ST
from .cldivrem import cldivrem
from .clmul import clmul
from .gfbmul import gfbmul
from .gfbmadd import gfbmadd
from .gfbinv import gfbinv
from .pack_poly import pack_poly, unpack_poly
import unittest


class GF2Poly:
    """Polynomial with GF(2) coefficients.

    `self.coefficients`: a list where `coefficients[-1] != 0`.
    `coefficients[i]` is the coefficient for `x ** i`.
    """

    def __init__(self, coefficients=None):
        self.coefficients = []
        if coefficients is not None:
            if not isinstance(coefficients, (tuple, list)):
                coefficients = list(coefficients)
            # reversed to resize self.coefficients once
            for i in reversed(range(len(coefficients))):
                self[i] = coefficients[i]

    def __len__(self):
        return len(self.coefficients)

    @property
    def degree(self):
        return len(self) - 1

    @property
    def lc(self):
        """leading coefficient."""
        return 0 if len(self) == 0 else self.coefficients[-1]

    def __getitem__(self, key):
        assert key >= 0
        if key < len(self):
            return self.coefficients[key]
        return 0

    def __setitem__(self, key, value):
        assert key >= 0
        assert value == 0 or value == 1
        if key < len(self):
            self.coefficients[key] = value
            while len(self) and self.coefficients[-1] == 0:
                self.coefficients.pop()
        elif value != 0:
            self.coefficients += [0] * (key + 1 - len(self))
            self.coefficients[key] = value

    def __repr__(self):
        return f"GF2Poly({self.coefficients})"

    def __iadd__(self, rhs):
        for i in range(max(len(self), len(rhs))):
            self[i] ^= rhs[i]
        return self

    def __add__(self, rhs):
        return GF2Poly(self).__iadd__(rhs)

    def __isub__(self, rhs):
        return self.__iadd__(rhs)

    def __sub__(self, rhs):
        return self.__add__(rhs)

    def __iter__(self):
        return iter(self.coefficients)

    def __mul__(self, rhs):
        retval = GF2Poly()
        # reversed to resize retval.coefficients once
        for i in reversed(range(len(self))):
            if self[i]:
                for j in reversed(range(len(rhs))):
                    retval[i + j] ^= rhs[j]
        return retval

    def __ilshift__(self, amount):
        """multiplies `self` by the polynomial `x**amount`"""
        if len(self) != 0:
            self.coefficients[:0] = [0] * amount
        return self

    def __lshift__(self, amount):
        """returns the polynomial `self * x**amount`"""
        return GF2Poly(self).__ilshift__(amount)

    def __irshift__(self, amount):
        """divides `self` by the polynomial `x**amount`, discarding the
            remainder.
        """
        if amount < len(self):
            del self.coefficients[:amount]
        else:
            del self.coefficients[:]
        return self

    def __rshift__(self, amount):
        """divides `self` by the polynomial `x**amount`, discarding the
            remainder.
        """
        return GF2Poly(self).__irshift__(amount)

    def __divmod__(self, divisor):
        # based on https://en.wikipedia.org/wiki/Polynomial_greatest_common_divisor#Euclidean_division
        assert isinstance(divisor, GF2Poly)
        if len(divisor) == 0:
            raise ZeroDivisionError
        q = GF2Poly()
        r = GF2Poly(self)
        while r.degree >= divisor.degree:
            shift = r.degree - divisor.degree
            q[shift] ^= 1
            r -= divisor << shift
        return q, r

    def __floordiv__(self, divisor):
        q, r = divmod(self, divisor)
        return q

    def __mod__(self, divisor):
        q, r = divmod(self, divisor)
        return r

    def __pow__(self, exponent, modulus=None):
        assert isinstance(exponent, int) and exponent >= 0
        assert modulus is None or isinstance(modulus, GF2Poly)
        retval = GF2Poly([1])
        pow2 = GF2Poly(self)
        while exponent != 0:
            if exponent & 1:
                retval *= pow2
                if modulus is not None:
                    retval %= modulus
                exponent &= ~1
            else:
                pow2 *= pow2
                if modulus is not None:
                    pow2 %= modulus
                exponent >>= 1
        return retval

    def __eq__(self, rhs):
        if isinstance(rhs, GF2Poly):
            return self.coefficients == rhs.coefficients
        return NotImplemented


class TestGF2Poly(unittest.TestCase):
    def test_add(self):
        a = GF2Poly([1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1])
        b = GF2Poly([0, 0, 1, 0, 1, 1, 1, 1, 1, 0, 0])
        c = a + b
        self.assertEqual(a, GF2Poly([1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1]))
        self.assertEqual(b, GF2Poly([0, 0, 1, 0, 1, 1, 1, 1, 1]))
        self.assertEqual(c, GF2Poly([1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1]))
        c = b + a
        self.assertEqual(a, GF2Poly([1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1]))
        self.assertEqual(b, GF2Poly([0, 0, 1, 0, 1, 1, 1, 1, 1]))
        self.assertEqual(c, GF2Poly([1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1]))
        a = GF2Poly([1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1])
        b = GF2Poly([0, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1])
        c = a + b
        self.assertEqual(a, GF2Poly([1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1]))
        self.assertEqual(b, GF2Poly([0, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1]))
        self.assertEqual(c, GF2Poly([1, 0, 1, 1, 1, 0, 0, 1]))
        c = a - b
        self.assertEqual(c, GF2Poly([1, 0, 1, 1, 1, 0, 0, 1]))
        c = b - a
        self.assertEqual(c, GF2Poly([1, 0, 1, 1, 1, 0, 0, 1]))

    def test_shift(self):
        a = GF2Poly([1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1])
        c = a << 0
        self.assertEqual(a, GF2Poly([1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1]))
        self.assertEqual(c, GF2Poly([1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1]))
        c = a << 5
        self.assertEqual(a, GF2Poly([1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1]))
        self.assertEqual(c, GF2Poly(
            [0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1]))
        c = a << 10
        self.assertEqual(a, GF2Poly([1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1]))
        self.assertEqual(c, GF2Poly(
            [0] * 10 + [1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1]))
        c = a >> 0
        self.assertEqual(a, GF2Poly([1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1]))
        self.assertEqual(c, GF2Poly([1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1]))
        c = a >> 5
        self.assertEqual(a, GF2Poly([1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1]))
        self.assertEqual(c, GF2Poly([1, 1, 0, 1, 0, 1]))
        c = a >> 10
        self.assertEqual(a, GF2Poly([1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1]))
        self.assertEqual(c, GF2Poly([1]))
        c = a >> 11
        self.assertEqual(a, GF2Poly([1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1]))
        self.assertEqual(c, GF2Poly([]))
        c = a >> 100
        self.assertEqual(a, GF2Poly([1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1]))
        self.assertEqual(c, GF2Poly([]))

    def test_mul(self):
        a = GF2Poly([1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1])
        b = GF2Poly([0, 0, 1, 0, 1, 1, 1, 1, 1])
        c = a * b
        expected = GF2Poly([0, 0, 1, 0, 1, 0, 1, 1, 1, 0,
                            0, 1, 0, 1, 1, 0, 0, 1, 1])
        self.assertEqual(a, GF2Poly([1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1]))
        self.assertEqual(b, GF2Poly([0, 0, 1, 0, 1, 1, 1, 1, 1]))
        self.assertEqual(c, expected)

    def test_divmod(self):
        a = GF2Poly([1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1])
        b = GF2Poly([0, 0, 1, 0, 1, 1, 1, 1, 1])
        q, r = divmod(a, b)
        self.assertEqual(a, GF2Poly([1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1]))
        self.assertEqual(b, GF2Poly([0, 0, 1, 0, 1, 1, 1, 1, 1]))
        self.assertEqual(q, GF2Poly([1, 1, 1]))
        self.assertEqual(r, GF2Poly([1, 0, 1, 0, 0, 1, 0, 1]))
        q = a // b
        self.assertEqual(q, GF2Poly([1, 1, 1]))
        r = a % b
        self.assertEqual(r, GF2Poly([1, 0, 1, 0, 0, 1, 0, 1]))

    def test_pow(self):
        b = GF2Poly([0, 1])
        for e in range(8):
            expected = GF2Poly([0] * e + [1])
            with self.subTest(b=str(b), e=e, expected=str(expected)):
                v = b ** e
                self.assertEqual(b, GF2Poly([0, 1]))
                self.assertEqual(v, expected)

        # AES's finite field reducing polynomial
        m = GF2Poly([1, 1, 0, 1, 1, 0, 0, 0, 1])
        period = 2 ** m.degree - 1
        b = GF2Poly([1, 1, 0, 0, 1, 0, 1])
        e = period - 1
        expected = GF2Poly([0, 1, 0, 1, 0, 0, 1, 1])
        v = pow(b, e, m)
        self.assertEqual(m, GF2Poly([1, 1, 0, 1, 1, 0, 0, 0, 1]))
        self.assertEqual(b, GF2Poly([1, 1, 0, 0, 1, 0, 1]))
        self.assertEqual(v, expected)

        # test that pow doesn't take inordinately long when given a modulus.
        # adding a multiple of `period` should leave results unchanged.
        e += period * 10 ** 15
        v = pow(b, e, m)
        self.assertEqual(m, GF2Poly([1, 1, 0, 1, 1, 0, 0, 0, 1]))
        self.assertEqual(b, GF2Poly([1, 1, 0, 0, 1, 0, 1]))
        self.assertEqual(v, expected)


class GFB:
    def __init__(self, value, red_poly=None):
        if isinstance(value, GFB):
            # copy value
            assert red_poly is None
            self.red_poly = GF2Poly(value.red_poly)
            self.value = GF2Poly(value.value)
            return
        assert isinstance(value, GF2Poly)
        assert isinstance(red_poly, GF2Poly)
        assert red_poly.degree > 0
        self.value = value % red_poly
        self.red_poly = red_poly

    def __repr__(self):
        return f"GFB({self.value}, {self.red_poly})"

    def __add__(self, rhs):
        assert isinstance(rhs, GFB)
        assert self.red_poly == rhs.red_poly
        return GFB((self.value + rhs.value) % self.red_poly, self.red_poly)

    def __sub__(self, rhs):
        return self.__add__(rhs)

    def __eq__(self, rhs):
        if isinstance(rhs, GFB):
            return self.value == rhs.value and self.red_poly == rhs.red_poly
        return NotImplemented

    def __mul__(self, rhs):
        assert isinstance(rhs, GFB)
        assert self.red_poly == rhs.red_poly
        return GFB((self.value * rhs.value) % self.red_poly, self.red_poly)

    def __div__(self, rhs):
        assert isinstance(rhs, GFB)
        assert self.red_poly == rhs.red_poly
        return self * rhs ** -1

    @property
    def __pow_period(self):
        period = (1 << self.red_poly.degree) - 1
        assert period > 0, "internal logic error"
        return period

    def __pow__(self, exponent):
        assert isinstance(exponent, int)
        if len(self.value) == 0:
            if exponent < 0:
                raise ZeroDivisionError
            else:
                return GFB(self)
        exponent %= self.__pow_period
        return GFB(pow(self.value, exponent, self.red_poly), self.red_poly)


class TestGFBClass(unittest.TestCase):
    def test_add(self):
        # AES's finite field reducing polynomial
        red_poly = GF2Poly([1, 1, 0, 1, 1, 0, 0, 0, 1])
        a = GFB(GF2Poly([0, 1, 0, 1]), red_poly)
        b = GFB(GF2Poly([0, 0, 0, 0, 0, 0, 1, 1]), red_poly)
        expected = GFB(GF2Poly([0, 1, 0, 1, 0, 0, 1, 1]), red_poly)
        c = a + b
        self.assertEqual(red_poly, GF2Poly([1, 1, 0, 1, 1, 0, 0, 0, 1]))
        self.assertEqual(a, GFB(GF2Poly([0, 1, 0, 1]), red_poly))
        self.assertEqual(b, GFB(GF2Poly([0, 0, 0, 0, 0, 0, 1, 1]), red_poly))
        self.assertEqual(c, expected)
        c = a - b
        self.assertEqual(red_poly, GF2Poly([1, 1, 0, 1, 1, 0, 0, 0, 1]))
        self.assertEqual(a, GFB(GF2Poly([0, 1, 0, 1]), red_poly))
        self.assertEqual(b, GFB(GF2Poly([0, 0, 0, 0, 0, 0, 1, 1]), red_poly))
        self.assertEqual(c, expected)
        c = b - a
        self.assertEqual(red_poly, GF2Poly([1, 1, 0, 1, 1, 0, 0, 0, 1]))
        self.assertEqual(a, GFB(GF2Poly([0, 1, 0, 1]), red_poly))
        self.assertEqual(b, GFB(GF2Poly([0, 0, 0, 0, 0, 0, 1, 1]), red_poly))
        self.assertEqual(c, expected)

    def test_mul(self):
        # AES's finite field reducing polynomial
        red_poly = GF2Poly([1, 1, 0, 1, 1, 0, 0, 0, 1])
        a = GFB(GF2Poly([0, 1, 0, 1, 0, 0, 1, 1]), red_poly)
        b = GFB(GF2Poly([1, 1, 0, 0, 1, 0, 1]), red_poly)
        expected = GFB(GF2Poly([1]), red_poly)
        c = a * b
        self.assertEqual(red_poly, GF2Poly([1, 1, 0, 1, 1, 0, 0, 0, 1]))
        self.assertEqual(a, GFB(GF2Poly([0, 1, 0, 1, 0, 0, 1, 1]), red_poly))
        self.assertEqual(b, GFB(GF2Poly([1, 1, 0, 0, 1, 0, 1]), red_poly))
        self.assertEqual(c, expected)

    def test_pow(self):
        # AES's finite field reducing polynomial
        red_poly = GF2Poly([1, 1, 0, 1, 1, 0, 0, 0, 1])
        period = 2 ** red_poly.degree - 1
        b = GFB(GF2Poly([1, 1, 0, 0, 1, 0, 1]), red_poly)
        e = period - 1
        expected = GFB(GF2Poly([0, 1, 0, 1, 0, 0, 1, 1]), red_poly)
        v = b ** e
        self.assertEqual(red_poly, GF2Poly([1, 1, 0, 1, 1, 0, 0, 0, 1]))
        self.assertEqual(b, GFB(GF2Poly([1, 1, 0, 0, 1, 0, 1]), red_poly))
        self.assertEqual(v, expected)
        e = -1
        v = b ** e
        self.assertEqual(red_poly, GF2Poly([1, 1, 0, 1, 1, 0, 0, 0, 1]))
        self.assertEqual(b, GFB(GF2Poly([1, 1, 0, 0, 1, 0, 1]), red_poly))
        self.assertEqual(v, expected)

        # test that pow doesn't take inordinately long when given a modulus.
        # adding a multiple of `period` should leave results unchanged.
        e += period * 10 ** 15
        v = b ** e
        self.assertEqual(red_poly, GF2Poly([1, 1, 0, 1, 1, 0, 0, 0, 1]))
        self.assertEqual(b, GFB(GF2Poly([1, 1, 0, 0, 1, 0, 1]), red_poly))
        self.assertEqual(v, expected)


class TestCL(unittest.TestCase):
    def test_cldivrem(self):
        n_width = 8
        d_width = 4
        width = max(n_width, d_width)
        for nv in range(2 ** n_width):
            n = GF2Poly(unpack_poly(nv))
            for dv in range(1, 2 ** d_width):
                d = GF2Poly(unpack_poly(dv))
                with self.subTest(n=str(n), nv=nv, d=str(d), dv=dv):
                    q_expected, r_expected = divmod(n, d)
                    self.assertEqual(q_expected * d + r_expected, n)
                    q, r = cldivrem(nv, dv, width)
                    q_expected = pack_poly(q_expected.coefficients)
                    r_expected = pack_poly(r_expected.coefficients)
                    self.assertEqual((q, r), (q_expected, r_expected))

    def test_clmul(self):
        a_width = 5
        b_width = 5
        for av in range(2 ** a_width):
            a = GF2Poly(unpack_poly(av))
            for bv in range(2 ** b_width):
                b = GF2Poly(unpack_poly(bv))
                with self.subTest(a=str(a), av=av, b=str(b), bv=bv):
                    expected = a * b
                    product = clmul(av, bv)
                    expected = pack_poly(expected.coefficients)
                    self.assertEqual(product, expected)


class TestGFBInstructions(unittest.TestCase):
    @staticmethod
    def init_aes_red_poly():
        # AES's finite field reducing polynomial
        red_poly = GF2Poly([1, 1, 0, 1, 1, 0, 0, 0, 1])
        ST.reinit(GFBREDPOLY=pack_poly(red_poly.coefficients))
        return red_poly

    def test_gfbmul(self):
        # AES's finite field reducing polynomial
        red_poly = self.init_aes_red_poly()
        a_width = 8
        b_width = 4
        for av in range(2 ** a_width):
            a = GFB(GF2Poly(unpack_poly(av)), red_poly)
            for bv in range(2 ** b_width):
                b = GFB(GF2Poly(unpack_poly(bv)), red_poly)
                expected = a * b
                with self.subTest(a=str(a), av=av, b=str(b), bv=bv, expected=str(expected)):
                    product = gfbmul(av, bv)
                    expectedv = pack_poly(expected.value.coefficients)
                    self.assertEqual(product, expectedv)

    def test_gfbmadd(self):
        # AES's finite field reducing polynomial
        red_poly = self.init_aes_red_poly()
        a_width = 5
        b_width = 4
        c_width = 4
        for av in range(2 ** a_width):
            a = GFB(GF2Poly(unpack_poly(av)), red_poly)
            for bv in range(2 ** b_width):
                b = GFB(GF2Poly(unpack_poly(bv)), red_poly)
                for cv in range(2 ** c_width):
                    c = GFB(GF2Poly(unpack_poly(cv)), red_poly)
                    expected = a * b + c
                    with self.subTest(a=str(a), av=av,
                                      b=str(b), bv=bv,
                                      c=str(c), cv=cv,
                                      expected=str(expected)):
                        result = gfbmadd(av, bv, cv)
                        expectedv = pack_poly(expected.value.coefficients)
                        self.assertEqual(result, expectedv)

    def test_gfbinv(self):
        # AES's finite field reducing polynomial
        red_poly = self.init_aes_red_poly()
        width = 8
        for av in range(2 ** width):
            a = GFB(GF2Poly(unpack_poly(av)), red_poly)
            expected = a ** -1 if av != 0 else GFB(GF2Poly(), red_poly)
            with self.subTest(a=str(a), av=av, expected=str(expected)):
                result = gfbinv(av)
                expectedv = pack_poly(expected.value.coefficients)
                self.assertEqual(result, expectedv)


if __name__ == "__main__":
    unittest.main()
