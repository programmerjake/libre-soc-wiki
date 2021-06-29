xdim = 3
ydim = 2
zdim = 1

lims = [xdim, ydim, zdim]
idxs = [0,0,0] # starting indices
order = [0,1,2] # experiment with different permutations, here
offs = 2     # experiment with different offset, here
applydim = 0
invxyz = [1,0,0]

for idx in range(offs):
    for i in range(3):
        idxs[order[i]] = idxs[order[i]] + 1
        if (idxs[order[i]] != lims[order[i]]):
            break
        print
        idxs[order[i]] = 0

break_count = 0

for idx in range(xdim * ydim * zdim):
    ix = [0] * 3
    for i in range(3):
        if i >= applydim:
            ix[i] = idxs[i]
        if invxyz[i]:
            ix[i] = lims[i] - 1 - ix[i]
    new_idx = ix[0] + ix[1] * xdim + ix[2] * xdim * ydim
    print new_idx,
    break_count += 1
    if break_count == lims[order[0]]:
        print
        break_count = 0
    for i in range(3):
        idxs[order[i]] = idxs[order[i]] + 1
        if (idxs[order[i]] != lims[order[i]]):
            break
        idxs[order[i]] = 0
