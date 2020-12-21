#! /bin/env python3
# see https://bugs.libre-soc.org/show_bug.cgi?id=532

# Estimate ppc code compression with Libre-SOC encoding attempt v1alt.


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

# This script is intended to compare the compression ratio between v1,
# and an alternate mode-switching strategy that does away with 10-bit
# insns to enter compressed mode, and instead uses a major 6-bit
# opcode of a 32-bit insn to signal the insn encodes 10 mode bits, and
# a compressed insn in the remaining 16 bits.  These 10 bits each
# correspond to an upcoming insn, telling whether or not it's
# compressed, so that any compressible insns among the 10 subsequent
# insns can be encoded as such without any further overhead.

# This would enable us to use the mode-switching bits in 16-bit insns
# for other purposes, but this script does not attempt to do so, so as
# to make for a simpler, more direct comparison.


# At (visible) entry points, mode is forced to return to uncompressed
# mode.  Every branch target must be in uncompressed mode as well, but
# this script does not enforce that.  In this model, the mode bits are
# cleared when branches are taken: they are static, but they shall not
# carry over across branch targets.  Mode-switching insns can only
# appear in uncompressed mode, and they reset the mode bits for
# upcoming insns, rather than appending.

# The entire code stream is printed, without any attempt to modify the
# addresses that go along with or in them; we only insert markers for
# the transition points, and for the compressed instructions.

# The really useful information is printed at the end: a summary of
# transition and compressed-insn counts, and the achieved compression
# rate.

import sys
import re

modebits = 10

insn = re.compile('\s+(?P<addr>[0-9a-f]+):\s+(?P<opcode>[^ ]+) *(?P<operands>.*)')

# reg is a regkind (r, cr, fr) followed by a regnum
xreg = '(?P<reg>(?P<regkind>[cf]?r)(?P<regnum>[0-9]+))'

# immediate is a sequence of digits, possibly preceded by a negative sign
ximm = '(?P<immediate>-?[0-9]+)'

# branch is a branch target address; ignore an angle-bracketed label after it
xbrt = '(?P<branch>[0-9a-f]+)(?: <.*>)?'

# offset is like immediate, but followed by a parenthesized basereg
xoff = '(?P<offset>-?[0-9]+)\((?P<basereg>r[0-9]+)\)'

# creg is the cr, cond names one of its bits
crbit = '(?:4\*(?P<creg>cr[0-7])\+)?(?P<cond>gt|lt|eq|so)'

# Combine the above into alternatives, to easily classify operands by
# pattern matching.
opkind = re.compile('|'.join([xreg, ximm, xbrt, xoff, crbit]))

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
    elif match['cond'] is not None:
        if match['creg'] is None:
            creg = 'cr0'
        else:
            creg = match['creg']
        op = ('crbit', mapop(creg), ('cond', match['cond']), op)
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
def crbt(mop):
    return opclass(mop) is   'crbit'

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

# Return the register sub-mop if mop fits crbit.
def crbtreg(mop):
    if crbt(mop):
        return mop[1]
    raise "operand is not a condition register bit"

# Return the cond bit name if mop fits crbit.
def crbtcnd(mop):
    if crbt(mop):
        return mop[2]
    raise "operand is not a condition register bit"

# Following are predicates to be used in copcond, to tell the mode in
# which opcode with ops as operands is to be represented.

# TODO: use insn_histogram.py to show the best targets
# (remember to exclude nop - ori r0,r0,0 as this skews numbers)
# Registers representable in a made-up 3-bit mapping.
# It must contain 0 for proper working of at least storex.
#cregs3 = { 0, 31, 1, 2, 3, 4, 5, 6, 7 }
cregs3 = { 0, 9, 3, 1, 2, 31, 10, 30, 4 }
# Ditto in a 2-bit mapping.  It needs not contain 0, but it must be a
# subset of cregs3 for proper working of at least storex.
cregs2 = { 9, 3, 1, 2 }
# Use the same sets for FP for now.
cfregs3 = cregs3
cfregs2 = cregs2
ccregs2 = { 0, 1, 2, 3 }

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

# Return true iff mop is a condition register present in ccregs2
def rccregs2(mop):
    return opclass(mop) is 'cr' and regno(mop) in ccregs2

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
       and opclass(ops[0]) is 'r' and regno(ops[0]) is 0 \
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

# 2 bits for RT and RA.  RB is r0 in 10-bit, and 3 bits in 16-bit ???
# there's a general assumption that, if an insn can be represented in
# 10-bits, then it can also be represented in 16 bits.  This will not
# be the case if cregs3 can't represent register 0.  For
# register+offset addresses, we support 16-imm stdi, fstdi, with 3-bit
# immediates left-shifted by 3; stwi, fstsi, with 2-bit immediates
# left-shifted by 2; stdspi for 6-bit immediate left-shifted by 3
# biased by -256, and stwspi for 6-bit immediate left-shifted by 2
# also biased by -256.  fstdi and fstsi store in memory a
# floating-point register, the others do a general-purpose register.
def storexaddr(opcode, ops):
    # Canonicalize offset in ops[1] to reg, imm
    if rofp(ops[1]):
        ops = (ops[0], rofreg(ops[1]), rofset(ops[1]))
        shift = memshifts[opcode[-1]]
        if immval(ops[2]) & ((1 << shift) - 1) is not 0:
            return 0
        if rcregs3(ops[1]) and immbits(ops[2]) <= shift + 3:
            return 2
        if regno(ops[1]) is 1 and opclass(ops[0]) is not 'fr' \
           and (immval(ops[2]) - 256).bit_length() <= shift + 6:
            return 2
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

memshifts = { 'd': 3, 'w': 2, 'z': 2, 's': 2 }

# 3 bits for RA, 3 bits for RB, 3 bits for RT for 16-bit.  for 10-bit,
# RB and RT must match.  ??? It's not clear what that means WRT
# register mapping of different kinds of registers, e.g. when RT is a
# floating-point register..
# For register+offset addresses, we support 16-imm ldi, fldi, with
# 3-bit immediates left-shifted by 3; lwi, flsi, with 2-bit immediates
# left-shifted by 2; ldspi for 6-bit immediate left-shifted by 3
# biased by -256, and lwspi for 6-bit immediate left-shifted by 2 also
# biased by -256.  fldi and flsi load to floating-point registers, the
# others load to general-purpose registers.
def loadxaddr(opcode, ops):
    if rofp(ops[1]):
        ops = (ops[0], rofreg(ops[1]), rofset(ops[1]))
        shift = memshifts[opcode[-1]]
        if immval(ops[2]) & ((1 << shift) - 1) is not 0:
            return 0
        if rcregs3(ops[1]) and immbits(ops[2]) <= shift + 3:
            return 2
        if regno(ops[1]) is 1 and opclass(ops[0]) is not 'fr' \
           and (immval(ops[2]) - 256).bit_length() <= shift + 6:
            return 2
        # Otherwise require offset 0 for compression of non-indexed form.
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

# Move between CRs.  3 bits for destination, 3 bits for source in
# 16-bit mode.  That covers all possibilities.  For 10-bit mode, only
# 2 bits for destination.
def mcrfop(opcode, ops):
    if rccregs2(ops[0]):
        return 3
    return 1
# Logical ops between two CRs into one.  2 bits for destination, that
# must coincide with one of the inputs, 3 bits for the other input.
# 16-bit only.
def crops(opcode, ops):
    if rccregs2(ops[0]) and regno(ops[0]) is regno(ops[1]):
        return 1
    return 0

# 3 bits for general-purpose register; immediate identifies the
# special purpose register to move to: 8 for lr, 9 for ctr.  16-bit
# only.  mtspr imm,rN moves from rN to the spr; mfspr rN,imm moves
# from spr to rN.
def mtsprops(opcode, ops):
    if immval(ops[0]) in (8, 9) and rcregs3(ops[1]):
        return 1
    return 0
def mfsprops(opcode, ops):
    if immval(ops[1]) in (8, 9) and rcregs3(ops[0]):
        return 1
    return 0

# 3 bits for nonzero general-purpose register; the immediate is a
# per-CR mask (8-bits).  mtcr rN is mtcrf 0xFF, rN.  mfcr rN is a raw
# opcode, not an alias.
def mtcrfops(opcode, ops):
    if immval(ops[0]) is 255 and rcregs3(ops[1]) and regno(ops[1]) is not 0:
        return 1
    return 0
def mfcrops(opcode, ops):
    if rcregs3(ops[0]) and regno(ops[0]) is not 0:
        return 1
    return 0

# 3 bits for destination and source register, must be the same.  Full
# shift range fits.  16-imm format.
def shiftops(opcode, ops):
    if rcregs3(ops[0]) and regno(ops[0]) is regno(ops[1]):
        return 2
    return 0

# For 16-imm 'addis' and 'addi', we have 3 bits (nonzero) for the
# destination register, source register is implied 0, the immediate
# must either fit in signed 5-bit, left-shifted by 3, or in signed
# 7-bit without shift.  ??? That seems backwards.
def addiops(opcode, ops):
    if rcregs3(ops[0]) and regno(ops[0]) is not 0 \
       and regno(ops[1]) is 0 and imm8(ops[2]) \
       and immbits(ops[2]) <= 8 \
       and ((immval(ops[2]) & 7) is 0 or immbits(ops[2]) <= 7):
        return 2
    return maybenop(opcode, ops)

# cmpdi and cmpwi are aliases to uncompressed cmp CR#, L, RA, imm16,
# CR# being the target condition register, L being set for d rather
# than w.  In 16-imm, CR# must be zero, RA must fit in 3 bits, and the
# immediate must be 6 bits signed.
def cmpiops(opcode, ops):
    if regno(ops[0]) is 0 and immval(ops[1]) in (0,1) \
       and rcregs3(ops[2]) and immbits(ops[3]) <= 6:
        return 2
    return 0

# 16-imm bc, with or without LK, uses 3 bits for BI (CR0 and CR1 only),
# and 1 bit for BO1 (to tell BO 12 from negated 4).
def bcops(opcode, ops):
    if immval(ops[0]) in (4,12) and regno(crbtreg(ops[1])) <= 1 \
       and immbits(ops[2]) <= 8:
        return 2
    return 0

# 2 bits for BI and 3 bits for BO in 10-bit encoding; one extra bit
# for each in 16-bit.
def bclrops(opcode, ops):
    if immval(ops[0]) <= 15 and regno(crbtreg(ops[1])) <= 1 \
       and immbits(ops[2]) is 0:
        if immval(ops[0]) <= 7 and regno(crbtreg(ops[1])) is 0:
            return 3
        return 1
    return 0

# Map opcodes that might be compressed to a function that returns the
# best potential encoding kind for the insn, per the numeric coding
# below.
copcond = {
    'ori': maybenop,
    # 'attn': binutils won't ever print this
    'b': uncondbranch, 'bl': uncondbranch,
    'bc': bcops, 'bcl': bcops,
    'bclr': bclrops, 'bclrl': bclrops,
    # Stores and loads, including 16-imm ones
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
    # Condition register opcodes.
    'mcrf': mcrfop,
    'crnor': crops,
    'crandc': crops,
    'crxor': crops,
    'crnand': crops,
    'crand': crops,
    'creqv': crops,
    'crorc': crops,
    'cror': crops,
    # System opcodes.
    # 'cbank' is not a ppc opcode, not handled
    'mtspr': mtsprops, # raw opcode for 'mtlr', 'mtctr'
    'mfspr': mfsprops, # raw opcode for 'mflr', 'mfctr'
    'mtcrf': mtcrfops, # raw opcode for 'mtcr'
    'mfcr': mfcrops,
    # 16-imm opcodes.
    'sradi.': shiftops, 'srawi.': shiftops,
    'addi': addiops,
    'cmpi': cmpiops, # raw opcode for 'cmpwi', 'cmpdi'
    # 'setvli', 'setmvli' are not ppc opcodes, not handled.
}

# v1 has 4 kinds of insns:

# 0: uncompressed; leave input insn unchanged
# 1: 16-bit compressed, only in compressed mode
# 2: 16-imm, i.e., compressed insn that can't switch-out of compressed mode
# 3: 10-bit compressed, may switch to compressed mode

# In v1alt, we map 1, 2 and 3 to compressed (count[1]).  If we have a
# compressing insn, and we've run out of bits from the latest
# mode-switch insn, we output another (count[2]).

count = [0,0,0]
# Default comments for the insn kinds above.
comments = ['', '\t; 16-bit', '\t; 6+10-bit mode']

# This counts the remaining bits to use from the latest mode-switching
# insn.
remobits = 0

for line in sys.stdin:
    if line[-1] is '\n':
        line = line[:-1]

    match = insn.fullmatch(line)
    if match is None:
        print(line)
        # Switch to uncompressed mode at function boundaries
        remobits = 0
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

    if nexti is not 0:
        nexti = 1
        if remobits is 0:
            remobits = modebits + 1
            print('\t\th.nop\t\t; 16-bit mode-switching prefix')
            count[2] += 1

    count[nexti] += 1

    if comment is None:
        comment = comments[nexti]
    else:
        comment = '\t; ' + comment
    
    print(line + comment)

    if remobits > 0:
        remobits -= 1

transition_bytes = 2 * count[2]
compressed_bytes = 2 * count[1]
uncompressed_bytes = 4 * count[0]
total_bytes = transition_bytes + compressed_bytes + uncompressed_bytes
original_bytes = 2 * compressed_bytes + uncompressed_bytes

print()
print('Summary')
print('32-bit uncompressed instructions: %i' % count[0])
print('16-bit compressed instructions: %i' % count[1])
print('16-bit mode-switching nops: %i' % count[2])
print('Compressed size estimate: %i' % total_bytes)
print('Original size: %i' % original_bytes)
print('Compressed/original ratio: %f' % (total_bytes / original_bytes))
