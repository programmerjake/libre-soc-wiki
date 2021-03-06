# FFT and convolution test (Python), "generators" version
#
# Copyright (c) 2020 Project Nayuki. (MIT License)
# https://www.nayuki.io/page/free-small-fft-in-multiple-languages
#
# Copyright (C) 2021 Luke Kenneth Casson Leighton <lkcl@lkcl.net>
# https://libre-soc.org/openpower/sv/remap/
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# - The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software.
# - The Software is provided "as is", without warranty of any kind, express or
#   implied, including but not limited to the warranties of merchantability,
#   fitness for a particular purpose and noninfringement. In no event shall the
#   authors or copyright holders be liable for any claim, damages or other
#   liability, whether in an action of contract, tort or otherwise, arising
#   from, out of or in connection with the Software or the use or other
#   dealings in the Software.
#

import cmath, math, random
from copy import deepcopy
from remap_fft_yield import iterate_indices


#
# Computes the discrete Fourier transform (DFT) or inverse transform of the
# given complex vector, returning the result as a new vector.
# The vector can have any length. This is a wrapper function. The inverse
# transform does not perform scaling, so it is not a true inverse.
#
def transform(vec, inverse, generators=False):
    n = len(vec)
    if n == 0:
        return []
    elif n & (n - 1) == 0:  # Is power of 2
        return transform_radix2(vec, inverse, generators)
    else:  # More complicated algorithm for arbitrary sizes
        assert False


#
# Computes the discrete Fourier transform (DFT) of the given complex vector,
# returning the result as a new vector.
# The vector's length must be a power of 2. Uses the Cooley-Tukey
# decimation-in-time radix-2 algorithm.
#
def transform_radix2(vec, inverse, generators_mode):
    # Returns the integer whose value is the reverse of the lowest 'width'
    # bits of the integer 'val'.
    def reverse_bits(val, width):
        result = 0
        for _ in range(width):
            result = (result << 1) | (val & 1)
            val >>= 1
        return result

    # Initialization
    n = len(vec)
    levels = n.bit_length() - 1
    if 2**levels != n:
        raise ValueError("Length is not a power of 2")
    # Now, levels = log2(n)
    coef = (2 if inverse else -2) * cmath.pi / n
    exptable = [cmath.rect(1, i * coef) for i in range(n // 2)]
    # Copy with bit-reversed permutation
    vec = [vec[reverse_bits(i, levels)] for i in range(n)]

    #
    # Radix-2 decimation-in-time FFT
    #
    if generators_mode:
        # loop using SVP64 REMAP "generators"
        # set the dimension sizes here

        # set total. err don't know how to calculate how many there are...
        # do it manually for now
        VL = 0
        size = 2
        while size <= n:
            halfsize = size // 2
            tablestep = n // size
            for i in range(0, n, size):
                for j in range(i, i + halfsize):
                    VL += 1
            size *= 2

        # set up an SVSHAPE
        class SVSHAPE:
            pass
        # j schedule
        SVSHAPE0 = SVSHAPE()
        SVSHAPE0.lims = [n, 0, 0]
        SVSHAPE0.order = [0,1,2]
        SVSHAPE0.mode = 0b01      # FFT mode
        SVSHAPE0.skip = 0b00
        SVSHAPE0.offset = 0
        SVSHAPE0.invxyz = [0,0,0] # inversion if desired
        # j+halfstep schedule
        SVSHAPE1 = deepcopy(SVSHAPE0)
        SVSHAPE1.skip = 0b01
        # k schedule
        SVSHAPE2 = deepcopy(SVSHAPE0)
        SVSHAPE2.skip = 0b10

        # enumerate over the iterator function, getting 3 *different* indices
        for idx, (jl, jh, k) in enumerate(zip(iterate_indices(SVSHAPE0),
                                              iterate_indices(SVSHAPE1),
                                              iterate_indices(SVSHAPE2))):
            if idx >= VL:
                break
            # exact same actual computation, just embedded in a single
            # for-loop but using triple generators to create the schedule
            temp1 = vec[jh] * exptable[k]
            temp2 = vec[jl]
            vec[jh] = temp2 - temp1
            vec[jl] = temp2 + temp1
    else:
        # loop using standard python nested for-loops
        size = 2
        while size <= n:
            halfsize = size // 2
            tablestep = n // size
            for i in range(0, n, size):
                k = 0
                for j in range(i, i + halfsize):
                    # exact same actual computation, just embedded in
                    # triple-nested for-loops
                    jl, jh = j, j+halfsize
                    temp1 = vec[jh] * exptable[k]
                    temp2 = vec[jl]
                    vec[jh] = temp2 - temp1
                    vec[jl] = temp2 + temp1
                    k += tablestep
            size *= 2
    return vec


#
# Computes the circular convolution of the given real or complex vectors,
# returning the result as a new vector. Each vector's length must be the same.
# realoutput=True: Extract the real part of the convolution, so that the
# output is a list of floats. This is useful if both inputs are real.
# realoutput=False: The output is always a list of complex numbers
# (even if both inputs are real).
#
def convolve(xvec, yvec, realoutput=True):
    assert len(xvec) == len(yvec)
    n = len(xvec)
    xvec = transform(xvec, False)
    yvec = transform(yvec, False)
    for i in range(n):
        xvec[i] *= yvec[i]
    xvec = transform(xvec, True)

    # Scaling (because this FFT implementation omits it) and postprocessing
    if realoutput:
        return [(val.real / n) for val in xvec]
    else:
        return [(val / n) for val in xvec]


###################################
# ---- Main and test functions ----
###################################

def main():
    global _maxlogerr

    # Test power-of-2 size FFTs
    for i in range(0, 12 + 1):
        _test_fft(1 << i)

    # Test power-of-2 size convolutions
    for i in range(0, 12 + 1):
        _test_convolution(1 << i)

    print()
    print(f"Max log err = {_maxlogerr:.1f}")
    print(f"Test {'passed' if _maxlogerr < -10 else 'failed'}")


def _test_fft(size):
    input = _random_vector(size)
    expect = _naive_dft(input, False)
    actual = transform(input, False, False)
    actual_generated = transform(input, False, True)
    assert actual == actual_generated # check generator-version is identical

    err_gen = _log10_rms_err(actual, actual_generated) # superfluous but hey
    err = _log10_rms_err(expect, actual)

    actual = [(x / size) for x in expect]
    actual = transform(actual, True)
    err = max(_log10_rms_err(input, actual), err)
    print(f"fftsize={size:4d}  logerr={err:5.1f} generr={err_gen:5.1f}")


def _test_convolution(size):
    input0 = _random_vector(size)
    input1 = _random_vector(size)
    expect = _naive_convolution(input0, input1)
    actual = convolve(input0, input1, False)
    print(f"convsize={size:4d}  logerr={_log10_rms_err(expect, actual):5.1f}")


# ---- Naive reference computation functions ----

def _naive_dft(input, inverse):
    n = len(input)
    output = []
    if n == 0:
        return output
    coef = (2 if inverse else -2) * math.pi / n
    for k in range(n):  # For each output element
        s = 0
        for t in range(n):  # For each input element
            s += input[t] * cmath.rect(1, (t * k % n) * coef)
        output.append(s)
    return output


def _naive_convolution(xvec, yvec):
    assert len(xvec) == len(yvec)
    n = len(xvec)
    result = [0] * n
    for i in range(n):
        for j in range(n):
            result[(i + j) % n] += xvec[i] * yvec[j]
    return result


# ---- Utility functions ----

_maxlogerr = -math.inf

def _log10_rms_err(xvec, yvec):
    global _maxlogerr
    assert len(xvec) == len(yvec)
    err = 10.0**(-99 * 2)
    for (x, y) in zip(xvec, yvec):
        err += abs(x - y) ** 2
    err = math.sqrt(err / max(len(xvec), 1))  # a root mean square (RMS) error
    err = math.log10(err)
    _maxlogerr = max(err, _maxlogerr)
    return err


def _random_vector(n):
    return [complex(random.uniform(-1.0, 1.0),
                    random.uniform(-1.0, 1.0)) for _ in range(n)]


if __name__ == "__main__":
    main()
