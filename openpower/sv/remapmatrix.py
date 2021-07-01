from remapyield import iterate_indices

def matrix_demo():
    X = [[1, 2, 3],
          [3, 4, 5],
         ]
    Y = [[6, 7],
          [8, 9],
          [10, 11],
         ]
    # 3x3 matrix
    X = [[12,7,3],
        [4 ,5,6],
        [7 ,8,9]]
    # 3x4 matrix
    Y = [[5,8,1,2],
        [6,7,3,0],
        [4,5,9,1]]
    xdim1 = len(X[0])
    ydim1 = len(X)
    xdim2 = len(Y[0])
    ydim2 = len(Y)
    # set up result matrix of correct size
    result = []
    for _ in range(ydim1):
        result.append([0]*xdim2)
    # iterate through rows of X
    for i in range(len(X)):
       # iterate through columns of Y
       for j in range(len(Y[0])):
           # iterate through rows of Y
           for k in range(len(Y)):
               result[i][j] += X[i][k] * Y[k][j]
    for r in result:
        print (r)

if __name__ == '__main__':
    matrix_demo()
