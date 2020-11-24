#! /bin/env python3
# see https://bugs.libre-soc.org/show_bug.cgi?id=532

# Feed this script the output of:
# powerpc64le-gnu-objdump -d -M raw --no-show-raw-insn ppc-prog

# It will print the occurrence count of each opcode,
# and under it, indented by one character,
# the occurrence count of each operand.

# Registers used as operands or as base addresses are counted
# separately; immediates and offsets are grouped per bit length;
# branch target offsets are grouped by range bit length.

import sys
import re

insn = re.compile('\s+(?P<addr>[0-9a-f]+):\s+(?P<opcode>[^ \n]+) *(?P<operands>.*)[\n]?')

opkind = re.compile('(?P<immediate>-?[0-9]+)|(?P<branch>[0-9a-f]+)(?: <.*>)?|(?P<offset>-?[0-9]+)\((?P<basereg>r[0-9]+)\)')

histogram = {}

def count(ops, op):
    match = opkind.fullmatch(op)

    if match is None:
        op = op
    elif match['immediate'] is not None:
        op = "%i-bit" % int (op).bit_length ()
    elif match['branch'] is not None:
        op = "%i-bit range" % (int (match['branch'], 16) - 
                               int(addr, 16)).bit_length ()
    elif match['offset'] is not None:
        count(ops, match['offset'])
        op = match['basereg']
    else:
        raise "unrecognized operand kind"

    if op not in ops:
        ops[op] = 1
    else:
        ops[op] += 1

for line in sys.stdin:
    match = insn.fullmatch(line)
    if match is None:
        continue

    addr = match['addr']
    opcode = match['opcode']
    operands = match['operands']

    if opcode not in histogram:
        ops = {}
        histogram[opcode] = [1,ops]
    else:
        histogram[opcode][0] += 1
        ops = histogram[opcode][1]

    if len(operands) > 0:
        for operand in operands.split(','):
            count(ops, operand)

intregcounts = {}
crregcounts = {}

# for each instruction print out a regcount.  first, sort by instr count
hist = list(histogram.items())
hist.sort(key = (lambda x : x[1][0]))

# now print each instruction and its register usage
for x in hist:
    print('%6i %s:' % (x[1][0], x[0]))
    ops = list(x[1][1].items())
    ops.sort(key = (lambda x : x[1]))

    # split out "-bit" from "-bit range" from "regs"

    # first "rNs" or "anything-weird"
    for x in ops:
        if '-bit' in x[0]:
            continue
        if x[0].startswith('cr'):
            continue
        print('\t%6i %s' % (x[1], x[0]))
        # total up integer register counts
        if not x[0].startswith('r'):
            continue
        if not x[0] in intregcounts:
            intregcounts[x[0]] = 0
        intregcounts[x[0]] += x[1]
    print()
    # TODO: FP regs.
    # ...

    # now Condition Registers
    for x in ops:
        if '-bit' in x[0]:
            continue
        if x[0].startswith('cr'):
            print('\t%6i %s' % (x[1], x[0]))
            if not x[0] in crregcounts:
                crregcounts[x[0]] = 0
            crregcounts[x[0]] += x[1]
    print()

    # now "N-bit immediates"
    for x in ops:
        if x[0].endswith('-bit'):
            print('\t%6i %s' % (x[1], x[0]))
    print()

    # finally "bit-range" immediates
    for x in ops:
        if '-bit range' in x[0]:
            print('\t%6i %s' % (x[1], x[0]))
    print()

# print out regs usage totals (TODO: FP)
for regcounts in [intregcounts, crregcounts]:
    regnums = list(regcounts.items())
    regnums.sort(key = (lambda x : x[1]))
    for x in regnums:
        print('%6i %s' % (x[1], x[0]))
    print()
