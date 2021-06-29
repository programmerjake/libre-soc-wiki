xdim = 3
ydim = 2
zdim = 1

VL = xdim * ydim * zdim # set total (can repeat, e.g. VL=x*y*z*4)

lims = [xdim, ydim, zdim]
idxs = [0,0,0] # starting indices
order = [1,0,2] # experiment with different permutations, here
offset = 0     # experiment with different offsetet, here
invxyz = [0,1,0]

for idx in range(offset):
    for i in range(3):
        idxs[order[i]] = idxs[order[i]] + 1
        if (idxs[order[i]] != lims[order[i]]):
            break
        print
        idxs[order[i]] = 0

break_count = 0 # for pretty-printing

for idx in range(VL):
    ix = [0] * 3
    for i in range(3):
        ix[i] = idxs[i]
        if invxyz[i]:
            ix[i] = lims[i] - 1 - ix[i]
    new_idx = ix[0] + ix[1] * xdim + ix[2] * xdim * ydim
    print ("%d->%d" % (idx, new_idx)),
    break_count += 1
    if break_count == lims[order[0]]:
        print ("")
        break_count = 0
    for i in range(3):
        idxs[order[i]] = idxs[order[i]] + 1
        if (idxs[order[i]] != lims[order[i]]):
            break
        idxs[order[i]] = 0
