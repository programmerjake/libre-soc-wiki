#! /bin/env python3
# see https://bugs.libre-soc.org/show_bug.cgi?id=532

# Estimate ppc code compression with Libre-SOC encoding attempt v1.


# Copyright 2020 Alexandre Oliva

# This script is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.

# This script is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this script; see the file COPYING3.  If not see
# <http://www.gnu.org/licenses/>.

# Skeleton originally by Alexandre Oliva <oliva@gnu.org>.


# Feed this script the output of objdump -M raw --no-show-raw-insn ppc-prog

# It will look for insns that can be represented in compressed mode,
# according to the encoding rules in the copcond dictionary below.

# Nothing is assumed as to the actual bit-encoding of the insns, this
# is just to experiment with insn selection and get a quick feedback
# loop for the encoding options in compressed mode.

# In this script, the computations of encoding modes and transitions
# are those for attempt 1 encoding, that encompasses:

# - a 16-bit insn (with 10-bit payload) that may switch to compressed
# mode or return to 32-bit mode;

# - 16-bit insns in compressed mode, each with 2 bits devoted to
# encoding one of the following possibilities:

# -- switch back to uncompressed mode at the next insn

# -- interpret the next insn in uncompressed mode, then return to
# compressed mode

# -- remain in 16-bit mode for the next insn

# - a 16-bit immediate insn in compressed mode, that must be followed
# by another compressed insn

# At (visible) entry points, mode is forced to return to uncompressed
# mode.  Every branch target must be in uncompressed mode as well, but
# this script does not enforce that.

# The entire code stream is printed, without any attempt to modify the
# addresses that go along with or in them; we only insert markers for
# the transition points, and for the compressed instructions.

# The really useful information is printed at the end: a summary of
# transition and compressed-insn counts, and the achieved compression
# rate.

import sys
import re

insn = re.compile('\s+(?P<addr>[0-9a-f]+):\s+(?P<opcode>[^ ]+) *(?P<operands>.*)')

# reg is a regkind (r, cr, fr) followed by a regnum
xreg = '(?P<reg>(?P<regkind>[cf]?r)(?P<regnum>[0-9]+))'

# immediate is a sequence of digits, possibly preceded by a negative sign
ximm = '(?P<immediate>-?[0-9]+)'

# branch is a branch target address; ignore an angle-bracketed label after it
xbrt = '(?P<branch>[0-9a-f]+)(?: <.*>)?'

# offset is like immediate, but followed by a parenthesized basereg
xoff = '(?P<offset>-?[0-9]+)\((?P<basereg>r[0-9]+)\)'

# Combine the above into alternatives, to easily classify operands by
# pattern matching.
opkind = re.compile('|'.join([xreg, ximm, xbrt, xoff]))

# Pre-parse and classify op into a mop, short for mapped op.
def mapop(op):
    match = opkind.fullmatch(op)

    if match is None:
        op = ('other', op)
    elif match['reg'] is not None:
        op = (match['regkind'], int(match['regnum']), op)
    elif match['immediate'] is not None:
        op = ('imm', int (op).bit_length (), op)
    elif match['branch'] is not None:
        op = ('pcoff', (int (match['branch'], 16)
                        - int (addr, 16)).bit_length (), op, addr)
    elif match['offset'] is not None:
        op = ('ofst', mapop(match['offset']), mapop(match['basereg']), op)
    # FIXME: cr exprs not handled
    else:
        raise "unrecognized operand kind"

    return op

# Accessor to enable the mapop representation to change easily.
def opclass(mop):
    return mop[0]

# Some opclass predicates, for the same reason.
def regp(mop):
    return opclass(mop) in { 'r', 'fr', 'cr' } \
        or (opclass(mop) is  'imm' and mop[1] is 0)
def immp(mop):
    return opclass(mop) in { 'imm', 'pcoff' }
def rofp(mop):
    return opclass(mop) is   'ofst'

# Some more accessors.

# Return the reg number if mop fits regp.
def regno(mop):
    if regp(mop) \
       or (immp(mop) and mop[1] is 0):
        return mop[1]
    raise "operand is not a register"

def immval(mop):
    if immp(mop):
        return int(mop[2])
    raise "operand is not an immediate"

# Return the immediate length if mop fits immp.
def immbits(mop):
    if immp(mop):
        return mop[1]
    raise "operand is not an immediate"

# Return the register sub-mop if mop fits rofp.
def rofreg(mop):
    if rofp(mop):
        return mop[2]
    raise "operand is not an offset"

# Return the offset sub-opt if mop fits rofp.
def rofset(mop):
    if rofp(mop):
        return mop[1]
    raise "operand is not an offset"

# Following are predicates to be used in copcond, to tell the mode in
# which opcode with ops as operands is to be represented.

# TODO: use insn_histogram.py to show the best targets
# (remember to exclude nop - ori r0,r0,0 as this skews numbers)
# Registers representable in a made-up 3-bit mapping.
# It must contain 0 for proper working of at least storex.
cregs3 = { 0, 31, 1, 2, 3, 4, 5, 6, 7 }
# Ditto in a 2-bit mapping.  It needs not contain 0, but it must be a
# subset of cregs3 for proper working of at least storex.
cregs2 = { 2, 3, 4, 5 }
# Use the same sets for FP for now.
cfregs3 = cregs3
cfregs2 = cregs2

# Return true iff mop is a regular register present in cregs2
def rcregs2(mop):
    return opclass(mop) in { 'r', 'imm' } and regno(mop) in cregs2

# Return true iff mop is a regular register present in cregs3
def rcregs3(mop):
    return opclass(mop) in { 'r', 'imm' } and regno(mop) in cregs3

# Return true iff mop is a floating-point register present in cfregs2
def rcfregs2(mop):
    return opclass(mop) is 'fr' and regno(mop) in cfregs2

# Return true iff mop is a floating-point register present in cfregs3
def rcfregs3(mop):
    return opclass(mop) is 'fr' and regno(mop) in cfregs3


# Return true iff mop is an immediate of at most 8 bits.
def imm8(mop):
    return immp(mop) and immbits(mop) <= 8

# Return true iff mop is an immediate of at most 12 bits.
def imm12(mop):
    return immp(mop) and immbits(mop) <= 12

# Compress binary opcodes iff the first two operands (output and first
# input operand) are registers representable in 3 bits in compressed
# mode, and the immediate operand can be represented in 8 bits.
def bin2regs3imm8(opcode, ops):
    if rcregs3(ops[0]) and rcregs3(ops[1]) and imm8(ops[2]):
        return 1
    return 0

# Recognize do-nothing insns, particularly ori r0,r0,0.
def maybenop(opcode, ops):
    if opcode in ['ori', 'addi'] and regno(ops[0]) is regno(ops[1]) \
       and ops[0][0] is 'r' and regno(ops[0]) is 0 \
       and imm8(ops[2]) and immbits(ops[2]) is 0:
        return 3
    return 0

# Recognize an unconditional branch, that can be represented with a
# 6-bit operand in 10-bit mode, an an additional 4 bits in 16-bit
# mode.  In both cases, the offset is shifted left by 2 bits.
def uncondbranch(opcode, ops):
    if imm8(ops[0]):
        return 3
    if imm12(ops[0]):
        return 1
    return 0

# 2 bits for RT and RA.  RB is r0 in 10-bit, and 3 bits in 16-bit
# ??? there's a general assumption that, if an insn can be represented
# in 10-bits, then it can also be represented in 10 bits.
# This will not be the case if cregs3 can't represent register 0.
def storexaddr(opcode, ops):
    # Canonicalize offset in ops[1] to reg, imm
    if rofp(ops[1]):
        ops = (ops[0], rofreg(ops[1]), rofset(ops[1]))
        # Require offset 0 for compression of non-indexed form.
        if not regp(ops[2]):
            return 0
    # If any of the registers is zero, and the other fits in cregs2,
    # it fits in 10-bit.
    if (rcregs2(ops[1]) and regno(ops[2]) is 0) \
       or (regno(ops[1]) is 0 and rcregs2(ops[2])):
        return 3
    # For 16-bit one must fit rcregs2 and the other rcregs3.
    if (rcregs2(ops[1]) and rcregs3(ops[2])) \
       or (rcregs3(ops[1]) and rcregs2(ops[2])):
        return 1
    return 0
def rstorex(opcode, ops):
    if rcregs2(ops[0]):
        return storexaddr(opcode, ops)
    return 0
def frstorex(opcode, ops):
    if rcfregs2(ops[0]):
        return storexaddr(opcode, ops)
    return 0

# 3 bits for RA, 3 bits for RB, 3 bits for RT for 16-bit.  for 10-bit,
# RB and RT must match.  ??? It's not clear what that means WRT
# register mapping of different kinds of registers, e.g. when RT is a
# floating-point register..
def loadxaddr(opcode, ops):
    if rofp(ops[1]):
        ops = (ops[0], rofreg(ops[1]), rofset(ops[1]))
        # Require offset 0 for compression of non-indexed form.
        if not regp(ops[2]):
            return 0
    if rcregs3(ops[1]) and rcregs3(ops[2]):
        if regno(ops[0]) in { regno(ops[1]), regno(ops[2]) }:
            return 3
        return 1
    return 0
def rloadx(opcode, ops):
    if rcregs3(ops[0]):
        return loadxaddr(opcode, ops)
    return 0
def frloadx(opcode, ops):
    if rcfregs3(ops[0]):
        return loadxaddr(opcode, ops)
    return 0
    
# 3 bits for RA, 3 bits for RB, 3 bits for RT for 16-bit.  for 10-bit,
# RB and RT must match.  RA must not be zero, but in 16-bit mode we
# can swap RA and RB to make it fit.
def addop(opcode, ops):
    if rcregs3(ops[0]) and rcregs3(ops[1]) and rcregs3(ops[2]):
        if regno(ops[0]) in { regno(ops[1]), regno(ops[2]) }:
            return 3
        if regno(ops[1]) is not 0 or regno(ops[2]) is not 0:
            return 1
    return 0

# 3 bits for RA, 3 bits for RB, 3 bits for RT for 16-bit.  for 10-bit,
# RA and RT must match.  ??? The spec says RB, but the actual opcode
# is subf., subtract from, and it subtracts RA from RB.  'neg.' would
# make no sense as described there if we didn't use RA.
def subfop(opcode, ops):
    if rcregs3(ops[0]) and rcregs3(ops[1]) and rcregs3(ops[2]):
        if regno(ops[0]) is regno(ops[1]):
            return 3
        return 1
    return 0
def negop(opcode, ops):
    if rcregs3(ops[0]) and rcregs3(ops[1]):
        return 3
    return 0

# 3 bits for RA and 3 bits for RB.  L (op1) must be 1 for 10-bit.
# op0 is a cr, must be zero for 10-bit.
def cmpop(opcode, ops):
    if rcregs3(ops[2]) and rcregs3(ops[3]):
        if regno(ops[0]) is 0 and immval(ops[1]) is 1:
            return 3
        return 1
    return 0

# 3 bits for RS, 3 bits for RB, 3 bits for RS, 16-bit only.
def sldop(opcode, ops):
    if rcregs3(ops[0]) and rcregs3(ops[1]) and rcregs3(ops[2]):
        return 1
    return 0
# same as sld, except RS must be nonzero.
def srdop(opcode, ops):
    if regno(ops[1]) is not 0:
        return sldop(opcode, ops)
    return 0
# same as sld, except RS is given by RA, so they must be the same.
def sradop(opcode, ops):
    if regno(ops[0]) is regno(ops[1]):
        return sldop(opcode, ops)
    return 0

# binary logical ops: and, nand, or, nor.
# 3 bits for RA (nonzero), 3 bits for RB, 3 bits for RT in 16-bit mode.
# RT is implicitly RB in 10-bit mode.
def binlog1016ops(opcode, ops):
    if rcregs3(ops[0]) and rcregs3(ops[1]) and rcregs3(ops[2]) \
       and regno(ops[1]) is not 0:
        # mr RT, RB AKA or RT, RB, RB takes the 10-bit encoding
        # of the 16-bit nor; we've already ruled out r0 as RB above.
        if regno(ops[0]) is regno(ops[2]) and opcode is not 'nor':
            return 3
        # or and and, with two identical inputs, stand for mr.
        # nor and nand, likewise, stand for not, that has its
        # own unary 10-bit encoding.
        if regno(ops[1]) is regno(ops[2]):
            return 3
        return 1
    return 0
# 3 bits for RB, 3 bits for RT in 16-bit mode.
# RT is implicitly RB in 10-bit mode.
def unlog1016ops(opcode, ops):
    if rcregs3(ops[0]) and rcregs3(ops[1]):
        if regno(ops[0]) is regno(ops[1]):
            return 3
        return 1
    return 0
# 16-bit only logical ops; no 10-bit encoding available
# same constraints as the 1016 ones above.
def binlog16ops(opcode, ops):
    if rcregs3(ops[0]) and rcregs3(ops[1]) and rcregs3(ops[2]) \
       and regno(ops[1]) is not 0:
        return 1
    return 0
def unlog16ops(opcode, ops):
    if rcregs3(ops[0]) and rcregs3(ops[1]):
        return 1
    return 0

# binary floating-point ops
# 3 bits for FRA (nonzero), 3 bits for FRB, 3 bits for FRT in 16-bit mode.
# FRT is implicitly FRB in 10-bit mode.
def binfp1016ops(opcode, ops):
    if rcfregs3(ops[0]) and rcfregs3(ops[1]) and rcfregs3(ops[2]) \
       and regno(ops[1]) is not 0:
        if regno(ops[0]) is regno(ops[2]):
            return 3
        return 1
    return 0
def unfp1016ops(opcode, ops):
    if rcfregs3(ops[0]) and rcfregs3(ops[1]):
        if regno(ops[0]) is regno(ops[1]):
            return 3
        return 1
    return 0
def binfp16ops(opcode, ops):
    if rcfregs3(ops[0]) and rcfregs3(ops[1]) and rcfregs3(ops[2]) \
       and regno(ops[1]) is not 0:
        return 1
    return 0
def unfp16ops(opcode, ops):
    if rcfregs3(ops[0]) and rcfregs3(ops[1]):
        return 1
    return 0

def cnvfp16ops(opcode, ops):
    if rcfregs2(ops[0]) and rcfregs2(ops[1]):
        return 1
    return 0

# Map opcodes that might be compressed to a function that returns the
# best potential encoding kind for the insn, per the numeric coding
# below.
copcond = {
    'ori': maybenop, 'addi': maybenop,
    # 'attn': binutils won't ever print this
    'b': uncondbranch, 'bl': uncondbranch,
    # 'bc', 'bcl': only in 16-imm mode, not implemented yet
    # 'bclr', 'bclrl': available in 10- or 16-bit, not implemented yet
    # 16-imm opcodes not implemented yet.
    'stdx': rstorex, 'stwx': rstorex,
    'std': rstorex, 'stw': rstorex, # only offset zero
    'stfdx': frstorex, 'stfsx': frstorex,
    'stfd': frstorex, 'stfs': frstorex, # only offset zero
    # Assuming lwz* rather than lwa*.
    'ldx': rloadx, 'lwzx': rloadx,
    'ld': rloadx, 'lwz': rloadx, # only offset zero
    'lfdx': rloadx, 'lfsx': rloadx,
    'lfd': rloadx, 'lfs': rloadx, # only offset zero
    'add': addop,
    'subf.': subfop, 'neg.': negop,
    # Assuming cmpl stands for cmpd, i.e., cmp with L=1.
    # cmpw is cmp with L=0, 16-bit only.
    'cmp': cmpop,
    'sld.': sldop, 'srd.': srdop, 'srad.': sradop,
    'and': binlog1016ops, 'nand': binlog1016ops,
    'or': binlog1016ops, 'nor': binlog1016ops,
    # assuming popcnt and cntlz mean the *d opcodes.
    'popcntd': unlog1016ops, 'cntlzd': unlog1016ops, 'extsw': unlog1016ops,
    # not RT, RB is mapped to nand/nor RT, RB, RB.
    'xor': binlog16ops, 'eqv': binlog16ops,
    # 'setvl.': unlog16ops, # ??? What's 'setvl.'?
    # assuming cnttz mean the *d opcode.
    'cnttzd': unlog16ops, 'extsb': unlog16ops, 'extsh': unlog16ops,
    'fsub.': binfp1016ops, 'fadd': binfp1016ops, 'fmul': binfp1016ops,
    'fneg.': unfp1016ops,
    'fdiv': binfp16ops,
    'fabs.': unfp16ops, 'fmr.': unfp16ops,
    # ??? are these the intended fp2int and int2fp, for all
    # combinations of signed/unsigned float/double?
    'fcfid': cnvfp16ops, 'fctidz': cnvfp16ops,
    'fcfidu': cnvfp16ops, 'fctiduz': cnvfp16ops,
    'fcfids': cnvfp16ops, 'fctiwz': cnvfp16ops,
    'fcfidus': cnvfp16ops, 'fctiwuz': cnvfp16ops,
    # Not implemented yet:
    # 10- and 16-bit:
    # 'mcrf':
    # 'cbank':
    # 16-bit only:
    # 'crnor':
    # 'crandc':
    # 'crxor':
    # 'crnand':
    # 'crand':
    # 'creqv':
    # 'crorc':
    # 'cror':
    # 'mtlr':
    # 'mtctr':
    # 'mflr':
    # 'mfctr':
    # 'mtcr':
    # 'mfcr':
}

# We have 4 kinds of insns:

# 0: uncompressed; leave input insn unchanged
# 1: 16-bit compressed, only in compressed mode
# 2: 16-imm, i.e., compressed insn that can't switch-out of compressed mode
# 3: 10-bit compressed, may switch to compressed mode

# count[0:3] count the occurrences of the base kinds.
# count[4] counts extra 10-bit nop-switches to compressed mode,
#   tentatively introduced before insns that can be 16-bit encoded.
# count[5] counts extra 10-bit nop-switches to compressed mode,
#   tentatively introduced before insns that can be 16-imm encoded.
# count[6] counts extra 16-bit nop-switches back to uncompressed,
#   introduced after a 16-imm insn.
count = [0,0,0,0,0,0,0]
# Default comments for the insn kinds above.
comments = ['', '\t; 16-bit', '\t; 16-imm', '\t; 10-bit']

# curi stands for the insn kind that we read and processed in the
# previous iteration of the loop, and previ is the one before it.  the
# one we're processing in the current iteration will be stored in
# nexti until we make it curi at the very end of the loop.
previ = curi = 0

for line in sys.stdin:
    if line[-1] is '\n':
        line = line[:-1]

    match = insn.fullmatch(line)
    if match is None:
        print(line)
        # Switch to uncompressed mode at function boundaries
        previ = curi = 0
        continue

    addr = match['addr']
    opcode = match['opcode']
    operands = match['operands']

    if opcode in copcond:
        nexti = copcond[opcode](opcode,
                               [mapop(op) for op in operands.split(',')])
    else:
        nexti = 0

    comment = None

    if curi is 0:
        if nexti is 0:
            True # Uncompressed mode for good.
        elif nexti is 1:
            # If curi was not a single uncompressed mode insn,
            # tentatively encode a 10-bit nop to enter compressed
            # mode, and then 16-bit.  It takes as much space as
            # encoding as 32-bit, but offers more possibilities for
            # subsequent compressed encodings.  A compressor proper
            # would have to go back and change the encoding
            # afterwards, but wé re just counting.
            if previ is not 1:
                print('\t\th.nop\t\t; 10-bit (tentative)')
                count[4] += 1
                comment = '16-bit (tentative)'
            else:
                comment = '16-bit auto-back'
        elif nexti is 2:
            # We can use compressed encoding for the 16-imm nexti
            # after an uncompressed insn without penalty if it's the
            # single-insn uncompressed mode slot.  For other
            # configurations, we can either remain in uncompressed
            # mode, or switch to compressed mode with a 10-bit nop.
            if previ is not 1:
                print('\t\th.nop\t\t; 10-bit (tentative)')
                count[5] += 1
                comment = '16-imm (tentative), vs uncompressed'
            else:
                comment = '16-imm auto-back'
        elif nexti is 3:
            # If previ was 16-bit compressed, curi would be in the
            # single-insn uncompressed slot, so nexti could be encoded
            # as 16-bit, enabling another 1-insn uncompressed slot
            # after nexti that a 10-bit insn wouldn't, so make it so.
            if previ is 1:
                nexti = 1
                comment = '16-bit auto-back, vs 10-bit'
    elif curi is 1:
        # After a 16-bit insn, anything goes.  If it remains in 16-bit
        # mode, we can have 1 or 2 as nexti; if it returns to 32-bit
        # mode, we can have 0 or 3.  Using 1 instead of 3 makes room
        # for a subsequent single-insn compressed mode, so prefer
        # that.
        if nexti is 3:
            nexti = 1
            comment = '16-bit, vs 10-bit'
    elif curi is 2:
        # After a 16-imm insn, we can only switch back to uncompressed
        # mode with a 16-bit nop.
        if nexti is 0:
            print('\t\tc.nop\t\t; forced switch back to uncompressed mode')
            count[6] += 1
            previ = curi
            curi = 1
        elif nexti is 3:
            nexti = 1
    elif curi is 3:
        # After a 10-bit insn, another insn that could be encoded as
        # 10-bit might as well be encoded as 16-bit, to make room for
        # a single-insn uncompressed insn afterwards.
        if nexti is 3:
            nexti = 1
            comment = '16-bit, vs 10-bit'
    else:
        raise "unknown mode for previious insn"

    count[nexti] += 1

    if comment is None:
        comment = comments[nexti]
    else:
        comment = '\t; ' + comment
    
    print(line + comment)

    previ = curi
    curi = nexti

transition_bytes = 2 * (count[4] + count[5] + count[6])
compressed_bytes = 2 * (count[1] + count[3])
uncompressed_bytes = 4 * (count[0] + count[2])
total_bytes = transition_bytes + compressed_bytes + uncompressed_bytes
original_bytes = 2 * compressed_bytes + uncompressed_bytes

print()
print('Summary')
print('32-bit uncompressed instructions: %i' % count[0])
print('16-bit compressed instructions: %i' % count[1])
print('16-imm compressed-mode instructions: %i' % count[2])
print('10-bit compressed instructions: %i' % count[3])
print('10-bit mode-switching nops: %i' % count[4])
print('10-bit mode-switching nops for imm-16: %i' % count[5])
print('16-bit mode-switching nops after imm-16: %i' % count[6])
print('Compressed size estimate: %i' % total_bytes)
print('Original size: %i' % original_bytes)
print('Compressed/original ratio: %f' % (total_bytes / original_bytes))
