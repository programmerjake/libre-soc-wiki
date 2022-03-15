from .cldivrem import cldivrem
from .clmul import clmul
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


if __name__ == "__main__":
    unittest.main()
