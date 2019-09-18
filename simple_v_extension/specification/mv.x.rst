MV.X and MV.swizzle
===================

swizzle needs a MV.  see below for a potential way to use the funct7 to do a swizzle in rs2.

+---------------+-------------+-------+----------+----------+--------+----------+--------+--------+
| Encoding      | 31:27       | 26:25 | 24:20    | 19:15    | 14:12  | 11:7     | 6:2    | 1:0    |
+---------------+-------------+-------+----------+----------+--------+----------+--------+--------+
| RV32-I-type   + imm[11:0]                      + rs1[4:0] + funct3 | rd[4:0]  + opcode + 0b11   |
+---------------+-------------+-------+----------+----------+--------+----------+--------+--------+
| RV32-I-type   + fn4[3:0]    + swizzle[7:0]     + rs1[4:0] + 0b000  | rd[4:0]  + OP-V   + 0b11   |
+---------------+-------------+-------+----------+----------+--------+----------+--------+--------+

* funct3 = MV
* OP-V = 0b1010111
* fn4 = 4 bit function.
* fn4 = 0b0000 - INT MV-SWIZZLE ?
* fn4 = 0b0001 - FP MV-SWIZZLE ?
* fn4 = 0bNN10 - INT MV-X, NN=elwidth (default/8/16/32)
* fn4 = 0bNN11 - FP MV-X NN=elwidth (default/8/16/32)

swizzle (only active on SV or P48/P64 when SUBVL!=0):

+-----+-----+-----+-----+
| 7:6 | 5:4 | 3:2 | 1:0 |
+-----+-----+-----+-----+
|   w |   z |   y |   x |
+-----+-----+-----+-----+

Pseudocode for element width part of MV.X:

::

  def mv_x(rd, rs1, funct4):
      elwidth = (funct4>>2) & 0x3
      bitwidth = {0:XLEN, 1:8, 2:16, 3:32}[elwidth] # get bits per el
      bytewidth = bitwidth / 8 # get bytes per el
      for i in range(VL):
          addr = (unsigned char *)&regs[rs1]
          offset = addr + bytewidth # get offset within regfile as SRAM
          # TODO, actually, needs to respect rd and rs1 element width,
          # here, as well.  this pseudocode just illustrates that the
          # MV.X operation contains a way to compact the indices into
          # less space.
          regs[rd] = (unsigned char*)(regs)[offset]

The idea here is to allow 8-bit indices to be stored inside XLEN-sized
registers, such that rather than doing this:

.. parsed-literal::
    ldimm x8, 1
    ldimm x9, 3
    ldimm x10, 2
    ldimm x11, 0
    {SVP.VL=4} MV.X x3, x8, elwidth=default

The alternative is this:

.. parsed-literal::
    ldimm x8, 0x00020301
    {SVP.VL=4} MV.X x3, x8, elwidth=8

Thus compacting four indices into the one register.  x3 and x8's element
width are *independent* of the MV.X elwidth, thus allowing both source
and element element widths of the *elements* to be moved to be over-ridden,
whilst *at the same time* allowing the *indices* to be compacted, as well.

----

potential MV.X?  register-version of MV-swizzle?

+-------------+-------+-------+----------+----------+--------+----------+--------+--------+
| Encoding    | 31:27 | 26:25 | 24:20    | 19:15    | 14:12  | 11:7     | 6:2    | 1:0    |
+-------------+-------+-------+----------+----------+--------+----------+--------+--------+
| RV32-R-type + funct7        + rs2[4:0] + rs1[4:0] + funct3 | rd[4:0]  + opcode + 0b11   |
+-------------+-------+-------+----------+----------+--------+----------+--------+--------+
| RV32-R-type + 0b0000000     + rs2[4:0] + rs1[4:0] + 0b001  | rd[4:0]  + OP-V   + 0b11   |
+-------------+-------+-------+----------+----------+--------+----------+--------+--------+

* funct3 = MV.X
* OP-V = 0b1010111
* funct7 = 0b000NN00 - INT MV.X, elwidth=NN (default/8/16/32)
* funct7 = 0b000NN10 - FP MV.X, elwidth=NN (default/8/16/32)
* funct7 = 0b0000001 - INT MV.swizzle to say that rs2 is a swizzle argument?
* funct7 = 0b0000011 - FP MV.swizzle to say that rs2 is a swizzle argument?

question: do we need a swizzle MV.X as well?

macro-op fusion
===============

there is the potential for macro-op fusion of mv-swizzle with the following instruction and/or preceding instruction.
<http://lists.libre-riscv.org/pipermail/libre-riscv-dev/2019-August/002486.html>

VBLOCK context?
===============

additional idea: a VBLOCK context that says that if a given register is used, it indicates that the
register is to be "swizzled", and the VBLOCK swizzle context contains the swizzling to be carried out.

mm_shuffle_ps?
==============

__m128 _mm_shuffle_ps(__m128 lo,__m128 hi,
       _MM_SHUFFLE(hi3,hi2,lo1,lo0))
Interleave inputs into low 2 floats and high 2 floats of output. Basically
   out[0]=lo[lo0];
   out[1]=lo[lo1];
   out[2]=hi[hi2];
   out[3]=hi[hi3];

For example, _mm_shuffle_ps(a,a,_MM_SHUFFLE(i,i,i,i)) copies the float
a[i] into all 4 output floats.

Transpose
=========

assuming a vector of 4x4 matrixes is stored as 4 separate vectors with subvl=4 in struct-of-array-of-struct form (the form I've been planning on using):
using standard (4+4) -> 4 swizzle instructions with 2 input vectors with subvl=4 and 1 output vector with subvl, a vectorized matrix transpose operation can be done in 2 steps with 4 instructions per step to give 8 instructions in total:

input:
| m00 m10 m20 m30 |
| m01 m11 m21 m31 |
| m02 m12 m22 m32 |
| m03 m13 m23 m33 |

transpose 4 corner 2x2 matrices

intermediate:
| m00 m01 m20 m21 |
| m10 m11 m30 m31 |
| m02 m03 m22 m23 |
| m12 m13 m32 m33 |

finish transpose

output:
| m00 m01 m02 m03 |
| m10 m11 m12 m13 |
| m20 m21 m22 m23 |
| m30 m31 m32 m33 |
