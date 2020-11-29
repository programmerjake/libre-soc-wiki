#! /bin/env python3

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

# -- take the 16 bits that would be the next compressed insn as an
# extension to the present 16-bit insn, and remain in 16-bit mode for
# the subsequent 16-bits

# At (visible) entry points, mode is forced to return to uncompressed
# mode.

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
        op = (match['regkind'], int(match['regnum']), op)
    elif match['immediate'] is not None:
        op = ('imm', int (op).bit_length (), op)
    elif match['branch'] is not None:
        op = ('pcoff', (int (match['branch'], 16)
                        - int (addr, 16)).bit_length (), op, addr)
    elif match['offset'] is not None:
        op = ('ofst', mapop(match['offset']), mapop(match['basereg']), op)
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
cregs2 = { 1, 2, 3, 4, 5, 6, 7, 31 }

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
# best potential encoding kind for the insn, per the numeric coding
# below.
copcond = {
    
}

# We have 4 kinds of insns:

# 0: uncompressed; leave input insn unchanged
# 1: 16-bit compressed, only in compressed mode
# 2: 16-bit extended by another 16-bit, only in compressed mode
# 3: 10-bit compressed, may switch to compressed mode

# count[0:3] count the occurrences of the base kinds.
# count[4] counts extra 10-bit nop-switches to compressed mode,
# tentatively introduced before insns that can be 16-bit encoded.
count = [0,0,0,0,0]
# Default comments for the insn kinds above.  2 is always tentative.
comments = ['', '\t; 16-bit', '\t; tentative 16+16-bit', '\t; 10-bit']

# cur stands for the insn kind that we read and processed in the
# previous iteration of the loop, and prev is the one before it.  the
# one we're processing in the current iteration will be stored in
# next until we make it cur at the very end of the loop.
prev = cur = 0

for line in sys.stdin:
    if line[-1] is '\n':
        line = line[:-1]

    match = insn.fullmatch(line)
    if match is None:
        print(line)
        # Switch to uncompressed mode at function boundaries
        prev = prev2 = 0
        continue

    addr = match['addr']
    opcode = match['opcode']
    operands = match['operands']

    if opcode in copcond:
        next = copcond[opcode](opcode,
                               [mapop(op) for op in operands.split(',')])
    else:
        next = 0

    comment = None

    if cur is 0:
        if next is 0:
            True # Uncompressed mode for good.
        elif next is 1:
            # If cur was not a single uncompressed mode insn,
            # tentatively encode a 10-bit nop to enter compressed
            # mode, and then 16-bit.  It takes as much space as
            # encoding as 32-bit, but offers more possibilities for
            # subsequent compressed encodings.  A compressor proper
            # would have to go back and change the encoding
            # afterwards, but wé re just counting.
            if prev is not 1:
                print('\t\th.nop\t\t; tentatively switch to compressed mode')
                count[4] += 1
                comment = 'tentatively compressed to 16-bit'
        elif next is 2:
            # We can use compressed encoding for next after an
            # uncompressed insn only if it's the single-insn
            # uncompressed mode slot.  For anything else, we're better
            # off using uncompressed encoding for next, since it makes
            # no sense to spend a 10-bit nop to switch to compressed
            # mode for a 16+16-bit insn.  If subsequent insns would
            # benefit from compressed encoding, we can switch then.
            if prev is not 1:
                next = 0
                comment = 'not worth a nop for 16+16-bit'
        elif next is 3:
            # If prev was 16-bit compressed, cur would be in the
            # single-insn uncompressed slot, so next could be encoded
            # as 16-bit, enabling another 1-insn uncompressed slot
            # after next that a 10-bit insn wouldn't, so make it so.
            if prev is 1:
                next = 1
                comment = '16-bit, could be 10-bit'
    elif cur is 1:
        # After a 16-bit insn, anything goes.  If it remains in 16-bit
        # mode, we can have 1 or 2 as next; if it returns to 32-bit
        # mode, we can have 0 or 3.  Using 1 instead of 3 makes room
        # for a subsequent single-insn compressed mode, so prefer
        # that.
        if next is 3:
            next = 1
            comment = '16-bit, could be 10-bit'
    elif cur is 2:
        # After a 16+16-bit insn, we can't switch directly to 32-bit
        # mode.  However, cur could have been encoded as 32-bit, since
        # any 16+16-bit insn can.  Indeed, we may have an arbitrary
        # long sequence of 16+16-bit insns before next, and if next
        # can only be encoded in 32-bit mode, we can "resolve" all
        # previous adjacent 16+16-bit insns to the corresponding
        # 32-bit insns in the encoding, and "adjust" the 16-bit or
        # 10-bit insn that enabled the potential 16+16-bit encoding to
        # switch to 32-bit mode then instead.
        if next is 0:
            prev = cur = 0
            comment = '32-bit, like tentative 16+16-bit insns above'
    elif cur is 3:
        # After a 10-bit insn, another insn that could be encoded as
        # 10-bit might as well be encoded as 16-bit, to make room for
        # a single-insn uncompressed insn afterwards.
        if next is 3:
            next = 1
            comment = '16-bit, could be 10-bit'
    else:
        raise "unknown mode for previous insn"

    count[next] += 1

    if comment is None:
        comment = comments[next]
    else:
        comment = '\t; ' + comment
    
    print(line + comment)

    prev = cur
    cur = next

transition_bytes = 2 * count[4]
compressed_bytes = 2 * (count[1] + count[3])
uncompressed_bytes = 4 * (count[0] + count[2])
total_bytes = transition_bytes + compressed_bytes + uncompressed_bytes
original_bytes = 2 * compressed_bytes + uncompressed_bytes

print()
print('Summary')
print('32-bit uncompressed instructions: %i' % count[0])
print('16-bit compressed instructions: %i' % count[1])
print('16+16-bit (tentative) compressed-mode instructions: %i' % count[2])
print('10-bit compressed instructions: %i' % count[3])
print('10-bit (tentative) mode-switching nops: %i' % count[4])
print('Compressed size estimate: %i' % total_bytes)
print('Original size: %i' % original_bytes)
print('Compressed/original ratio: %f' % (total_bytes / original_bytes))
