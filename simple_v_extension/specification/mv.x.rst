MV.X and MV.swizzle
===================

swizzle needs a MV.  see below for a potential way to use the funct7 to do a swizzle in rs2.

+---------------+-------------+-------+----------+----------+--------+----------+--------+--------+
| Encoding      | 31:27       | 26:25 | 24:20    | 19:15    | 14:12  | 11:7     | 6:2    | 1:0    |
+---------------+-------------+-------+----------+----------+--------+----------+--------+--------+
| RV32-I-type   + imm[11:0]                      + rs1[4:0] + funct3 | rd[4:0]  + opcode + 0b11   |
+---------------+-------------+-------+----------+----------+--------+----------+--------+--------+
| RV32-I-type   + fn4[11:8] swizzle[7:0]         + rs1[4:0] + 0b000  | rd[4:0]  + OP-V   + 0b11   |
+---------------+-------------+-------+----------+----------+--------+----------+--------+--------+

* funct3 = MV
* OP-V = 0b1010111
* fn4 = 4 bit function.
* fn4 = 0b0000 - INT MV-SWIZZLE ?
* fn4 = 0b0001 - FP MV-SWIZZLE ?

swizzle (only active on SV or P48/P64 when SUBVL!=0):

+-----+-----+-----+-----+
| 7:6 | 5:4 | 3:2 | 1:0 |
+-----+-----+-----+-----+
|   w |   z |   y |   x |
+-----+-----+-----+-----+

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
* funct7 = 0b0000000 - INT MV.X
* funct7 = 0b0000001 - FP MV.X
* funct7 = 0b0000010 - INT MV.swizzle to say that rs2 is a swizzle argument?
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
