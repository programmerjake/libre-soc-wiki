def lut2(imm, a, b):
    idx = b << 1 | a
    return (imm>>idx) & 1

def dorow(imm8, step_i, chunk_size):
    step_o = 0
    for j in range(64):
        if (j&chunk_size) == 0:
           imm = (imm8 & 0b1111)
        else:
           imm = (imm8>>4)
        a = (step_i>>j)&1
        b = (step_i>>(j ^ chunk_size))&1
        res = lut2(imm, a, b)
        #print(j, bin(imm), a, b, res)
        step_o |= (res<<j)
    #print ("  ", chunk_size, bin(step_o))
    return step_o

def grevlut64(RA, RB, imm, iv):
    x = 0
    if RA is None: # RA=0
        x = 0x5555555555555555
    else:
        x = RA
    if (iv): x = ~x;
    shamt = RB & 63;
    #print (bin(shamt), bin(63))
    for i in range(6):
        step = 1<<i
        if (shamt & step):
            x = dorow(imm, x, step)
    return x & ((1<<64)-1)


if __name__ == '__main__':
    # answer: 8888888...
    RB = 0b0000
    imm = 0b11000110
    x = grevlut64(None, RB, imm, 1)
    print ("grevlut", bin(RB), bin(imm), hex(x), "\n", bin(x))

    # answer: 8888888...
    RB = 0b0010
    imm = 0b11000110
    x = grevlut64(None, RB, imm, 1)
    print ("grevlut", bin(RB), bin(imm), hex(x), "\n", bin(x))

    # answer: 80808080...
    RB = 0b00110
    imm = 0b11000110
    x = grevlut64(None, RB, imm, 1)
    print ("grevlut", bin(RB), bin(imm), hex(x), "\n", bin(x))

    # answer: 80008000...
    RB = 0b01110
    imm = 0b11000110
    x = grevlut64(None, RB, imm, 1)
    print ("grevlut", bin(RB), bin(imm), hex(x), "\n", bin(x))
    print()

    # answer: 01010101...
    RB = 0b00110
    imm = 0b01101100
    x = grevlut64(None, RB, imm, 0)
    print ("grevlut", bin(RB), bin(imm), hex(x), "\n", bin(x))

    # answer: 00010001...
    RB = 0b01110
    imm = 0b01101100
    x = grevlut64(None, RB, imm, 0)
    print ("grevlut", bin(RB), bin(imm), hex(x), "\n", bin(x))
    print()

    for RB in range(64):
        imm = 0b11000110
        x = grevlut64(None, RB, imm, 1)
        print ("grevlut", bin(RB), bin(imm), hex(x), "\n", bin(x))
    print()

    for RB in range(64):
        imm = 0b01101100
        x = grevlut64(None, RB, imm, 0)
        print ("grevlut", bin(RB), bin(imm), hex(x), "\n", bin(x))
    print()

    for RB in range(64):
        imm = 0b10011010
        x = grevlut64(None, RB, imm, 1)
        print ("grevlut", bin(RB), bin(imm), hex(x), "\n", bin(x))
    print()

    for RB in range(64):
        imm = 0b01011010
        x = grevlut64(None, RB, imm, 1)
        print ("grevlut", bin(RB), bin(imm), hex(x), "\n", bin(x))
    print()

