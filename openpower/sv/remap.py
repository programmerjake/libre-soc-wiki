# Finite State Machine version of the REMAP system.  much more likely
# to end up being actually used in actual hardware

# up to three dimensions permitted
xdim = 3
ydim = 2
zdim = 1

VL = xdim * ydim * zdim # set total (can repeat, e.g. VL=x*y*z*4)

lims = [xdim, ydim, zdim]
idxs = [0,0,0]   # starting indices
applydim = [1, 1]   # apply lower dims
order = [1,0,2]  # experiment with different permutations, here
offset = 0       # experiment with different offsetet, here
invxyz = [0,1,0] # inversion allowed

# pre-prepare the index state: run for "offset" times before
# actually starting.  this algorithm can also be used for re-entrancy
# if exceptions occur and a REMAP has to be started from where the
# interrupt left off.
for idx in range(offset):
    for i in range(3):
        idxs[order[i]] = idxs[order[i]] + 1
        if (idxs[order[i]] != lims[order[i]]):
            break
        idxs[order[i]] = 0

break_count = 0 # for pretty-printing

for idx in range(VL):
    ix = [0] * 3
    for i in range(3):
        ix[i] = idxs[i]
        if invxyz[i]:
            ix[i] = lims[i] - 1 - ix[i]
    new_idx = ix[2]
    if applydim[1]:
        new_idx = new_idx * ydim + ix[1]
    if applydim[0]:
        new_idx = new_idx * xdim + ix[0]
    print ("%d->%d" % (idx, new_idx)),
    break_count += 1
    if break_count == lims[order[0]]:
        print ("")
        break_count = 0
    # this is the exact same thing as the pre-preparation stage
    # above.  step 1: count up to the limit of the current dimension
    # step 2: if limit reached, zero it, and allow the *next* dimension
    # to increment.  repeat for 3 dimensions.
    for i in range(3):
        idxs[order[i]] = idxs[order[i]] + 1
        if (idxs[order[i]] != lims[order[i]]):
            break
        idxs[order[i]] = 0
