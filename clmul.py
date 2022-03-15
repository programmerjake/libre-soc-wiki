def clmul(a, b):
    x = 0
    i = 0
    while b >> i != 0:
        if (b >> i) & 1:
            x ^= a << i
        i += 1
    return x
