#! /bin/env python3
# see https://bugs.libre-soc.org/show_bug.cgi?id=532

# Estimate ppc code compression with Libre-SOC encoding attempt v2.


# Copyright 2020 Alexandre Oliva
# Copyright 2020 Luke Kenneth Casson Leighton

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
# are tuned for the simpler model that uses 1-byte nops for
# transitions in and out of compressed mode, placing compressed-mode
# insns at odd addresses.  At (visible) entry points, mode is forced
# to return to uncompressed mode.

# The entire code stream is printed, without any attempt to modify the
# addresses that go along with or in them; we only insert markers for
# the transition points, and for the compressed instructions.

# The really useful information is printed at the end: a summary of
# transition and compressed-insn counts, and the achieved compression
# rate.

import sys
import re

insn = re.compile('\s+(?P<addr>[0-9a-f]+):\s+(?P<opcode>[^ ]+) *(?P<operands>.*)')

opkind = re.compile('(?P<reg>(?P<regkind>[cf]?r)(?P<regnum>[0-9]+))|(?P<immediate>-?[0-9]+)|(?P<branch>[0-9a-f]+)(?: <.*>)?|(?P<offset>-?[0-9]+)\((?P<basereg>r[0-9]+)\)')

def mapop(op):
    match = opkind.fullmatch(op)

    if match is None:
        op = ('other', op)
    elif match['reg'] is not None:
        op = (match['regkind'], int(match['regnum']))
    elif match['immediate'] is not None:
        op = ('imm', int (op).bit_length ())
    elif match['branch'] is not None:
        op = ('pcoff', (int (match['branch'], 16)
                        - int (addr, 16)).bit_length ())
    elif match['offset'] is not None:
        op = ('ofst', mapop(match['offset']), mapop(match['basereg']))
    else:
        raise "unrecognized operand kind"

    return op

def opclass(mop):
    return mop[0]
def regno(mop):
    if mop[0] in { 'r', 'fr', 'cr' }:
        return mop[1]
    else:
        raise "operand is not a register"

def immbits(mop):
    if mop[0] is 'imm':
        return mop[1]
    else:
        raise "operand is not an immediate"

# Following are predicates to be used in copcond, to tell the mode in
# which opcode with ops as operands is to be represented

# Any occurrence of the opcode can be compressed.
def anyops(opcode, ops):
    return 1

# Compress iff first and second operands are the same.
def same01(opcode, ops):
    if ops[0] == ops[1]:
        return 1
    else:
        return 0

# Registers representable in a made-up 3-bit mapping.
cregs2 = { 9, 1, 2, 3, 31, 10, 30, 4 }

# Return true iff mop is a regular register present in cregs2
def bin2regs3(mop):
    return opclass(mop) is 'r' and regno(mop) in cregs2

# Return true iff mop is an immediate of at most 8 bits.
def imm8(mop):
    return opclass(mop) is 'imm' and immbits(mop) <= 8

# Compress binary opcodes iff the first two operands (output and first
# input operand) are registers representable in 3 bits in compressed
# mode, and the immediate operand can be represented in 8 bits.
def bin2regs3imm8(opcode, ops):
    if bin2regs3(ops[0]) and bin2regs3(ops[1]) and imm8(ops[2]):
        return 1
    else:
        return 0

# Map opcodes that might be compressed to a function that returns the
# mode (index into mode_list below) in which the insn is to be
# represented.  Those not mentioned in copcond are assumed
# Uncomopressed.
copcond = {
    # Pretending anything goes, just for demonstration purposes.
    'mr': anyops,
    'ld': anyops,
    'std': anyops,
    # Output and first input operand must coincide for these.
    'add': same01,
    'sub': same01,
    # Limiting register and operand range:
    'addi': bin2regs3imm8
    # Anything else is uncompressed.
}

enter_compressed = 0
leave_compressed = 0
count_compressed = 0
count_uncompressed = 0
current_mode = 0
mode_list = ['Uncompressed', 'Compressed'] # for documentation purposes only

for line in sys.stdin:
    if line[-1] is '\n':
        line = line[:-1]

    match = insn.fullmatch(line)
    if match is None:
        print(line)
        # Switch to uncompressed mode at function boundaries
        if current_mode is not 0:
            print('<leave compressed mode>')
            current_mode = 0
            leave_compressed += 1
        continue

    addr = match['addr']
    opcode = match['opcode']
    operands = match['operands']

    if opcode in copcond:
        this_mode = copcond[opcode](opcode,
                                    [mapop(op) for op in operands.split(',')])
    else:
        this_mode = 0

    if this_mode is 1:
        if current_mode is not 1:
            print('\t\tcin.nop')
            current_mode = 1
            enter_compressed += 1
        print(line + ' (c)')
        count_compressed += 1
    else:
        if current_mode is not 0:
            print('\t\tcout.nop')
            current_mode = 0
            leave_compressed += 1
        print(line)
        count_uncompressed += 1

transition_bytes = 1 * enter_compressed + 1 * leave_compressed
compressed_bytes = 2 * count_compressed
uncompressed_bytes = 4 * count_uncompressed
total_bytes = transition_bytes + compressed_bytes + uncompressed_bytes
original_bytes = 2 * compressed_bytes + uncompressed_bytes

print()
print('Summary')
print('Compressed instructions: %i' % count_compressed)
print('Uncompressed instructions: %i' % count_uncompressed)
print('Transitions into compressed mode: %i' % enter_compressed)
print('Transitions out of compressed mode: %i' % leave_compressed)
print('Compressed size estimate: %i' % total_bytes)
print('Original size: %i' % original_bytes)
print('Compressed/original ratio: %f' % (total_bytes / original_bytes))
