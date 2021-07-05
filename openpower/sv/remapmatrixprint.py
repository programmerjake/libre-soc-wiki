# a "yield" version of the REMAP algorithm. a little easier to read
# than the Finite State Machine version

from remapyield import iterate_indices


def matrixscheduledemo():
    ydim2, xdim2, ydim1 = (3, 4, 3)

    print ("ydim2 xdim2 ydim1", ydim2, xdim2, ydim1)

    # got this from running an earlier version
    expected = [
        ( 0 , (0, 0, 0) ),
        ( 1 , (1, 0, 1) ),
        ( 2 , (2, 0, 2) ),
        ( 3 , (3, 0, 3) ),
        ( 4 , (4, 3, 0) ),
        ( 5 , (5, 3, 1) ),
        ( 6 , (6, 3, 2) ),
        ( 7 , (7, 3, 3) ),
        ( 8 , (8, 6, 0) ),
        ( 9 , (9, 6, 1) ),
        ( 10 , (10, 6, 2) ),
        ( 11 , (11, 6, 3) ),
        ( 12 , (0, 1, 4) ),
        ( 13 , (1, 1, 5) ),
        ( 14 , (2, 1, 6) ),
        ( 15 , (3, 1, 7) ),
        ( 16 , (4, 4, 4) ),
        ( 17 , (5, 4, 5) ),
        ( 18 , (6, 4, 6) ),
        ( 19 , (7, 4, 7) ),
        ( 20 , (8, 7, 4) ),
        ( 21 , (9, 7, 5) ),
        ( 22 , (10, 7, 6) ),
        ( 23 , (11, 7, 7) ),
        ( 24 , (0, 2, 8) ),
        ( 25 , (1, 2, 9) ),
        ( 26 , (2, 2, 10) ),
        ( 27 , (3, 2, 11) ),
        ( 28 , (4, 5, 8) ),
        ( 29 , (5, 5, 9) ),
        ( 30 , (6, 5, 10) ),
        ( 31 , (7, 5, 11) ),
        ( 32 , (8, 8, 8) ),
        ( 33 , (9, 8, 9) ),
        ( 34 , (10, 8, 10) ),
        ( 35 , (11, 8, 11) ),
    ]

    class SVSHAPE:
        pass
    # result uses SVSHAPE0
    SVSHAPE0 = SVSHAPE()
    SVSHAPE0.lims = [xdim2, ydim2, 1]
    SVSHAPE0.order = [0,1,2]  # result iterates through i and j (modulo)
    SVSHAPE0.mode = 0b00
    SVSHAPE0.skip = 0b00
    SVSHAPE0.offset = 0       # no offset
    SVSHAPE0.invxyz = [0,0,0] # no inversion
    # X uses SVSHAPE1
    SVSHAPE1 = SVSHAPE()
    SVSHAPE1.lims = [xdim2, ydim2, ydim1]
    SVSHAPE1.order = [0,2,1]  # X iterates through i and k
    SVSHAPE1.mode = 0b00
    SVSHAPE1.skip = 0b01
    SVSHAPE1.offset = 0       # no offset
    SVSHAPE1.invxyz = [0,0,0] # no inversion
    # y-selector uses SHAPE2
    SVSHAPE2 = SVSHAPE()
    SVSHAPE2.lims = [xdim2, ydim2, ydim1]
    SVSHAPE2.order = [0,2,1]  # X iterates through i and k
    SVSHAPE2.mode = 0b00
    SVSHAPE2.skip = 0b11
    SVSHAPE2.offset = 0       # no offset
    SVSHAPE2.invxyz = [0,0,0] # no inversion

    # perform the iteration over the *linear* arrays using the
    # schedules
    VL = ydim2 * xdim2 * ydim1
    i = 0
    for i, idxs in enumerate(zip(iterate_indices(SVSHAPE0),
                                 iterate_indices(SVSHAPE1),
                                 iterate_indices(SVSHAPE2))):

        if i == VL:
            break
        print ("(", i, ",", idxs, "),", "expected", expected[i])
        if expected[i] != (i, idxs):
            print ("row incorrect")


# run the demo
if __name__ == '__main__':
    matrixscheduledemo()
