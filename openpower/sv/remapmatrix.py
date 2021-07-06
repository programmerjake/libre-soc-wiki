from remapyield import iterate_indices
from functools import reduce
import operator


def iterate_triple(SVSHAPE0, SVSHAPE1, SVSHAPE2):
    # zip three iterators together, yields a synchronised
    # tuple of three indices at a time
    yield from zip(iterate_indices(SVSHAPE0),
                   iterate_indices(SVSHAPE1),
                   iterate_indices(SVSHAPE2))


def matrix_demo():
    #### test matrices 1
    # 3x2 matrix
    X1 = [[1, 2, 3],
          [3, 4, 5],
         ]
    # 2x3 matrix
    Y1 = [[6, 7],
          [8, 9],
          [10, 11],
         ]

    #### test matrices 2
    # 3x3 matrix
    X2 = [[12,7,3],
        [4 ,5,6],
        [7 ,8,9],
        ]
    # 3x4 matrix
    Y2 = [[5,8,1,2],
        [6,7,3,0],
        [4,5,9,1]]

    #### test matrices 3
    # 3x4 matrix
    X3 = [[12,7,3],
        [4 ,5,6],
        [7 ,8,9],
        [2 ,0,1]]
    # 3x5 matrix
    Y3 = [[5,8,1,2,3],
        [6,7,3,0,9],
        [4,5,9,1,2]]

    # pick one of the above (crude, non-automated, but it works, hey)
    X = X2
    Y = Y2

    # get the dimensions of the 2 matrices
    xdim1 = len(X[0])
    ydim1 = len(X)
    xdim2 = len(Y[0])
    ydim2 = len(Y)

    # print out X and Y
    print ("X:")
    for r in X:
        print ("\t", r)
    print ("Y:")
    for r in Y:
        print ("\t", r)

    # first, calculate the result matrix manually.
    # set up result matrix of correct size
    result = []
    for _ in range(ydim1):
        result.append([0]*xdim2)
    # iterate through rows of Y
    count = 0
    for k in range(len(Y)):       # ydim2
        # iterate through rows of X
        for i in range(len(X)):              # ydim1
            # iterate through columns of Y
            for j in range(len(Y[0])):        # xdim2
                print ("order %d    res %d   X %d   Y %d" % \
                        (count,
                         (i*xdim2)+j, # result linear array index
                         (i*xdim1)+k,  # X linear array index
                         (k*xdim2)+j))   # Y linear array index
                result[i][j] += X[i][k] * Y[k][j]
                count += 1
    print ("expected result")
    for r in result:
        print ("\t", r)

    # now. flatten the X and Y matrices into linear 1D Arrays.
    # linear rows are sequentially-packed first (inner loop),
    # columns next (outer loop):
    #   0 1 2 3
    #   4 5 6 7
    #   8 9 10 11
    # =>
    #   0 1 2 3 4 .... 10 11
    xf = reduce(operator.add, X)
    yf = reduce(operator.add, Y)
    print ("flattened X,Y")
    print ("\t", xf)
    print ("\t", yf)
    # and create a linear result2, same scheme
    result2 = [0] * (ydim1*xdim2)

    ########
    # now create the schedule. we use three generators, zipped
    # together

    print ("xdim2 ydim1 ydim2", xdim2, ydim1, ydim2)

    class SVSHAPE:
        pass
    # result uses SVSHAPE0
    SVSHAPE0 = SVSHAPE()
    SVSHAPE0.lims = [xdim2, ydim1, ydim2]
    SVSHAPE0.order = [0,1,2]  # result iterates through i and j (modulo)
    SVSHAPE0.mode = 0b00
    SVSHAPE0.skip = 0b11      # select 1st 2 dimensions (skip 3rd)
    SVSHAPE0.offset = 0       # no offset
    SVSHAPE0.invxyz = [0,0,0] # no inversion
    # X uses SVSHAPE1
    SVSHAPE1 = SVSHAPE()
    SVSHAPE1.lims = [xdim2, ydim1, ydim2]
    SVSHAPE1.order = [0,2,1]  # X iterates through i and k
    SVSHAPE1.mode = 0b00
    SVSHAPE1.skip = 0b01      # skip middle dimension
    SVSHAPE1.offset = 0       # no offset
    SVSHAPE1.invxyz = [0,0,0] # no inversion
    # y-selector uses SHAPE2
    SVSHAPE2 = SVSHAPE()
    SVSHAPE2.lims = [xdim2, ydim1, ydim2]
    SVSHAPE2.order = [0,2,1]  # X iterates through i and k
    SVSHAPE2.mode = 0b00
    SVSHAPE2.skip = 0b11      # select 1st 2 dimensions (skip 3rd)
    SVSHAPE2.offset = 0       # no offset
    SVSHAPE2.invxyz = [0,0,0] # no inversion


    # perform the iteration over the *linear* arrays using the
    # schedules
    VL = ydim2 * xdim2 * ydim1
    i = 0
    for i, idxs in enumerate(iterate_triple(SVSHAPE0, SVSHAPE1, SVSHAPE2)):
        if i == VL:
            break
        r_idx, x_idx, y_idx = idxs
        new_result = result2[r_idx] + xf[x_idx] * yf[y_idx]
        print ("idxs", i, idxs, len(result2), len(xf), len(yf),
               "  results  ", result2[r_idx], xf[x_idx], yf[y_idx], new_result)
        result2[r_idx] = new_result

    # now print out sections of result array, assuming elements of a "row"
    # are in sequence (inner loop), columns are outer
    for i in range(0, len(result2), xdim2):
        print ("\t", result2[i:i+xdim2])

if __name__ == '__main__':
    matrix_demo()
