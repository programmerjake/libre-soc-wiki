[[!tag oldstandards]]

SimpleV Prefix (SVprefix) Proposal v0.3
=======================================

* Copyright (c) Jacob Lifshay, 2019
* Copyright (c) Luke Kenneth Casson Leighton, 2019

This proposal is designed to be able to operate without SVorig, but not to
require the absence of SVorig. See Specification_.

Principle: SVprefix embeds (unmodified) RVC and 32-bit scalar opcodes
into 32, 48 and 64 bit RV formats, to provide Vectorisation context
on a per-instruction basis.

.. _Specification: http://libre-riscv.org/simple_v_extension/specification/
.. _Appendix: http://libre-riscv.org/simple_v_extension/appendix/

.. contents::

Conventions
===========

Conventions used in this document:

* Bits are numbered starting from 0 at the LSB, so bit 3 is 1 in the integer 8.
* Bit ranges are inclusive on both ends, so 5:3 means bits 5, 4, and 3.
* Operations work on variable-length vectors of sub-vectors up to *VL*
  in length, where each sub-vector has a length *svlen*, and *svlen*
  elements of type *etype*.
* The actual total number of elements is therefore *svlen* times *VL*.
* When the vectors are stored in registers, all elements are packed so
  that there is no padding in-between elements of the same vector.
* The register file itself is thus best viewed as a byte-level SRAM that
  is typecast to an array of *etypes*
* The number of bytes in a sub-vector, *svsz*, is the product of *svlen*
  and the element size in bytes.

Options
=======

The following partial / full implementation options are possible:

* SVPrefix augments the main Specification_
* SVPrefix operates independently, without the main spec VL (and MVL)
  CSRs (in any priv level)
* SVPrefix operates independently, without the main spec SUBVL CSRs
  (in any priv level)
* SVPrefix has no support for VL (or MVL) overrides in the 64 bit
  instruction format (VLtyp=0 as the only legal permitted value)
* SVPrefix has no support for svlen overrides in either the 48 or 64
  bit instruction format either (svlen=0 as the only legal permitted value).

All permutations of the above options are permitted, and the UNIX
platform must raise illegal instruction exceptions on implementations
that do not support each option.  For example, an implementation that
has no support for VLtyp that sees an opcode with a nonzero VLtyp must
raise an illegal instruction exception.

Note that SVPrefix (VLtyp and svlen) has its own STATE CSR, SVPSTATE. This allows Prefixed operations to be re-entrant on traps, and to not affect VBLOCK use of VL or SUBVL.

If the main Specification_ CSRs and features are to be supported (VBLOCK), then when VLtyp or svlen are "default" they utilise the main Specification_ VBLOCK VL and/or SUBVL, and, correspondingly, the main VBLOCK STATE CSR will be updated and used to track hardware loops.

If however VLtyp is set to nondefault, then the SVPSTATE src and destoffs fields are used instead to create the hardware loops, and likewise if svlen is set to nondefault, SVPSTATE's svoffs field is used.

Half-Precision Floating Point (FP16)
====================================

If the F extension is supported, SVprefix adds support for FP16 in the
base FP instructions by using 10 (H) in the floating-point format field
*fmt* and using 001 (H) in the floating-point load/store *width* field.

Compressed Instructions
=======================

Compressed instructions are under evaluation by taking the same
prefix as used in P48, embedding that and standard RVC opcodes (minus
their RVC prefix) into a 32-bit space.  This by taking the three remaining
Major "custom" opcodes (0-2), one for each of the three RVC Quadrants.
see [[discussion]].

48-bit Prefixed Instructions
============================

All 48-bit prefixed instructions contain a 32-bit "base" instruction as
the last 4 bytes. Since all 32-bit instructions have bits 1:0 set to
11, those bits are reused for additional encoding space in the 48-bit
instructions.

64-bit Prefixed Instructions
============================

The 48 bit format is further extended with the full 128-bit range on all
source and destination registers, and the option to set both SVSTATE.VL and SVSTATE.MVL
is provided.

48-bit Instruction Encodings
============================

In the following table, *Rsvd* (reserved) entries must be zero.  RV32 equivalent
encodings included for side-by-side comparison (and listed below,
separately).

First, bits 17:0:

+---------------+--------+--------+----------+-----+--------+-------------+------+--------+--------+
| Encoding      | 17     | 16     | 15       | 14  | 13     | 12          | 11:7 | 6      | 5:0    |
+---------------+--------+--------+----------+-----+--------+-------------+------+--------+--------+
| P48-LD-type   | rd[5]  | rs1[5] | vitp7[6] | vd  | vs1    | vitp7[5:0]         | *Rsvd* | 011111 |
+---------------+--------+--------+----------+-----+--------+-------------+------+--------+--------+
| P48-ST-type   |vitp7[6]| rs1[5] | rs2[5]   | vs2 | vs1    | vitp7[5:0]         | *Rsvd* | 011111 |
+---------------+--------+--------+----------+-----+--------+-------------+------+--------+--------+
| P48-R-type    | rd[5]  | rs1[5] | rs2[5]   | vs2 | vs1    | vitp6              | *Rsvd* | 011111 |
+---------------+--------+--------+----------+-----+--------+--------------------+--------+--------+
| P48-I-type    | rd[5]  | rs1[5] | vitp7[6] | vd  | vs1    | vitp7[5:0]         | *Rsvd* | 011111 |
+---------------+--------+--------+----------+-----+--------+--------------------+--------+--------+
| P48-U-type    | rd[5]  | *Rsvd* | *Rsvd*   | vd  | *Rsvd* | vitp6              | *Rsvd* | 011111 |
+---------------+--------+--------+----------+-----+--------+-------------+------+--------+--------+
| P48-FR-type   | rd[5]  | rs1[5] | rs2[5]   | vs2 | vs1    | *Rsvd*      | vtp5 | *Rsvd* | 011111 |
+---------------+--------+--------+----------+-----+--------+-------------+------+--------+--------+
| P48-FI-type   | rd[5]  | rs1[5] | vitp7[6] | vd  | vs1    | vitp7[5:0]         | *Rsvd* | 011111 |
+---------------+--------+--------+----------+-----+--------+-------------+------+--------+--------+
| P48-FR4-type  | rd[5]  | rs1[5] | rs2[5]   | vs2 | rs3[5] | vs3 [#fr4]_ | vtp5 | *Rsvd* | 011111 |
+---------------+--------+--------+----------+-----+--------+-------------+------+--------+--------+

.. [#fr4] Only vs2 and vs3 are included in the P48-FR4-type encoding
          because there is not enough space for vs1 as well, and because
          it is more useful to have a scalar argument for each of the
          multiplication and addition portions of fmadd than to have
          two scalars on the multiplication portion.

Table showing correspondance between P48-*-type and RV32-*-type.
These are bits 47:18 (RV32 shifted up by 16 bits):

+---------------+---------------+
| Encoding      | RV32 Encoding |
+---------------+---------------+
| 47:32         | 31:2          |
+---------------+---------------+
| P48-LD-type   | RV32-I-type   |
+---------------+---------------+
| P48-ST-type   | RV32-S-Type   |
+---------------+---------------+
| P48-R-type    | RV32-R-Type   |
+---------------+---------------+
| P48-I-type    | RV32-I-Type   |
+---------------+---------------+
| P48-U-type    | RV32-U-Type   |
+---------------+---------------+
| P48-FR-type   | RV32-FR-Type  |
+---------------+---------------+
| P48-FI-type   | RV32-I-Type   |
+---------------+---------------+
| P48-FR4-type  | RV32-FR4-type |
+---------------+---------------+

Table showing Standard RV32 encodings:

+---------------+-------------+-------+----------+----------+--------+----------+--------+--------+
| Encoding      | 31:27       | 26:25 | 24:20    | 19:15    | 14:12  | 11:7     | 6:2    | 1:0    |
+---------------+-------------+-------+----------+----------+--------+----------+--------+--------+
| RV32-R-type   +    funct7           + rs2[4:0] + rs1[4:0] + funct3 | rd[4:0]  + opcode + 0b11   |
+---------------+-------------+-------+----------+----------+--------+----------+--------+--------+
| RV32-S-type   + imm[11:5]           + rs2[4:0] + rs1[4:0] + funct3 | imm[4:0] + opcode + 0b11   |
+---------------+-------------+-------+----------+----------+--------+----------+--------+--------+
| RV32-I-type   + imm[11:0]                      + rs1[4:0] + funct3 | rd[4:0]  + opcode + 0b11   |
+---------------+-------------+-------+----------+----------+--------+----------+--------+--------+
| RV32-U-type   + imm[31:12]                                         | rd[4:0]  + opcode + 0b11   |
+---------------+-------------+-------+----------+----------+--------+----------+--------+--------+
| RV32-FR4-type + rs3[4:0]    + fmt   + rs2[4:0] + rs1[4:0] + funct3 | rd[4:0]  + opcode + 0b11   |
+---------------+-------------+-------+----------+----------+--------+----------+--------+--------+
| RV32-FR-type  + funct5      + fmt   + rs2[4:0] + rs1[4:0] + rm     | rd[4:0]  + opcode + 0b11   |
+---------------+-------------+-------+----------+----------+--------+----------+--------+--------+

64-bit Instruction Encodings
============================

Where in the 48 bit format the prefix is "0b0011111" in bits 0 to 6,
this is now set to "0b0111111".

+---------------+---------------+--------------+-----------+
| 63:48         | 47:18         | 17:7         | 6:0       |
+---------------+---------------+--------------+-----------+
| 64 bit prefix | RV32[31:3]    | P48[17:7]    | 0b0111111 |
+---------------+---------------+--------------+-----------+

* The 64 bit prefix format is below
* Bits 18 to 47 contain bits 3 to 31 of a standard RV32 format
* Bits 7 to 17 contain bits 7 through 17 of the P48 format
* Bits 0 to 6 contain the standard RV 64-bit prefix 0b0111111

64 bit prefix format:

+--------------+-------+--------+--------+--------+--------+
| Encoding     | 63    | 62     | 61     | 60     | 59:48  |
+--------------+-------+--------+--------+--------+--------+
| P64-LD-type  | rd[6] | rs1[6] |        | *Rsvd* | VLtyp  |
+--------------+-------+--------+--------+--------+--------+
| P64-ST-type  |       | rs1[6] | rs2[6] | *Rsvd* | VLtyp  |
+--------------+-------+--------+--------+--------+--------+
| P64-R-type   | rd[6] | rs1[6] | rs2[6] | vd     | VLtyp  |
+--------------+-------+--------+--------+--------+--------+
| P64-I-type   | rd[6] | rs1[6] |        | *Rsvd* | VLtyp  |
+--------------+-------+--------+--------+--------+--------+
| P64-U-type   | rd[6] |        |        | *Rsvd* | VLtyp  |
+--------------+-------+--------+--------+--------+--------+
| P64-FR-type  |       | rs1[6] | rs2[6] | vd     | VLtyp  |
+--------------+-------+--------+--------+--------+--------+
| P64-FI-type  | rd[6] | rs1[6] | rs2[6] | vd     | VLtyp  |
+--------------+-------+--------+--------+--------+--------+
| P64-FR4-type | rd[6] | rs1[6] | rs2[6] | rs3[6] | VLtyp  |
+--------------+-------+--------+--------+--------+--------+

The extra bit for src and dest registers provides the full range of
up to 128 registers, when combined with the extra bit from the 48 bit
prefix as well.  VLtyp encodes how (whether) to set SVPSTATE.VL and SVPSTATE.MAXVL.

VLtyp field encoding
====================

NOTE: VL and MVL below are local to SVPrefix and, if non-default,
will update the src and dest element offsets in SVPSTATE, not the main
Specification_ STATE. If default (all zeros) then STATE VL and MVL apply
to this instruction, and STATE.srcoffs (etc) will be used.

+-----------+-------------+--------------+----------+----------------------+
| VLtyp[11] | VLtyp[10:6] | VLtyp[5:1]   | VLtyp[0] | comment              |
+-----------+-------------+--------------+----------+----------------------+
| 0         |  00000      | 00000        |  0       | no change to VL/MVL  |
+-----------+-------------+--------------+----------+----------------------+
| 0         |  VLdest     | VLEN         |  vlt     | VL imm/reg mode (vlt)|
+-----------+-------------+--------------+----------+----------------------+
| 1         |  VLdest     | MVL+VL-immed | 0        | MVL+VL immed mode    |
+-----------+-------------+--------------+----------+----------------------+
| 1         |  VLdest     |  MVL-immed   | 1        | MVL immed mode       |
+-----------+-------------+--------------+----------+----------------------+

Note: when VLtyp is all zeros, the main Specification_ VL and MVL apply
to this instruction. If called outside of a VBLOCK or if sv.setvl has
not set VL, the operation is "scalar".

Just as in the VBLOCK format, when bit 11 of VLtyp is zero:

* if vlt is zero, bits 1 to 5 specify the VLEN as a 5 bit immediate
  (offset by 1: 0b00000 represents VL=1, 0b00001 represents VL=2 etc.)
* if vlt is 1, bits 1 to 5 specify the scalar (RV standard) register
  from which VL is set.  x0 is not permitted
* VL goes into the scalar register VLdest (if VLdest is not x0)

When bit 11 of VLtype is 1:

* if VLtyp[0] is zero, both SVPSTATE.MAXVL and SVPSTATE.VL are set to (imm+1).  The same
  value goes into the scalar register VLdest (if VLdest is not x0)
* if VLtyp[0] is 1, SVPSTATE.MAXVL is set to (imm+1).
  SVPSTATE.VL will be truncated to within the new range (if VL was greater
  than the new MAXVL).  The new VL goes into the scalar register VLdest
  (if VLdest is not x0).

This gives the option to set up SVPSTATE.VL in a "loop mode" (VLtype[11]=0) or
in a "one-off" mode (VLtype[11]=1) which sets both MVL and VL to the
same immediate value.  This may be most useful for one-off Vectorised
operations such as LOAD-MULTI / STORE-MULTI, for saving and restoration
of large batches of registers in context-switches or function calls.

Note that VLtyp's VL and MVL are not the same as the main Specification_
VL or MVL, and that loops will alter srcoffs and destoffs in SVPSTATE in VLtype nondefault mode, but the srcoffs and destoffs in STATE, if VLtype=0.

Furthermore, the execution order and exception handling must be exactly
the same as in the main spec (Program Order must be preserved)

Pseudocode for SVPSTATE.VL:

.. parsed-literal::

    # pseudocode

    regs = [0u64; 128];
    vl = 0;

    // instruction fields:
    rd = get_rd_field();
    vlmax = get_immed_field();

    // handle illegal instruction decoding
    if vlmax > XLEN {
        trap()
    }

    // calculate VL
    if rs1 == 0 { // rs1 is x0
        vl = vlmax
    } else {
        vl = min(regs[rs1], vlmax)
    }

    // write rd
    if rd != 0 {
        // rd is not x0
        regs[rd] = vl
    }

vs#/vd Fields' Encoding
=======================

+--------+----------+----------------------------------------------------------+
| vs#/vd | Mnemonic | Meaning                                                  |
+========+==========+==========================================================+
| 0      | S        | the rs#/rd field specifies a scalar (single sub-vector); |
|        |          | the rs#/rd field is zero-extended to get the actual      |
|        |          | 7-bit register number                                    |
+--------+----------+----------------------------------------------------------+
| 1      | V        | the rs#/rd field specifies a vector; the rs#/rd field is |
|        |          | decoded using the `Vector Register Number Encoding`_ to  |
|        |          | get the actual 7-bit register number                     |
+--------+----------+----------------------------------------------------------+

If a vs#/vd field is not present, it is as if it was present with a value that
is the bitwise-or of all present vs#/vd fields.

* scalar register numbers do NOT increment when allocated in the
  hardware for-loop.  the same scalar register number is handed
  to every ALU.

* vector register numbers *DO* increase when allocated in the
  hardware for-loop.  sequentially-increasing register data
  is handed to sequential ALUs.

Vector Register Number Encoding
===============================

For the 48 bit format, when vs#/vd is 1, the actual 7-bit register number
is derived from the corresponding 6-bit rs#/rd field:

+---------------------------------+
| Actual 7-bit register number    |
+===========+=============+=======+
| Bit 6     | Bits 5:1    | Bit 0 |
+-----------+-------------+-------+
| rs#/rd[0] | rs#/rd[5:1] | 0     |
+-----------+-------------+-------+

For the 64 bit format, the 7 bit register is constructed from the 7 bit
fields: bits 0 to 4 from the 32 bit RV Standard format, bit 5 from the 48
bit prefix and bit 6 from the 64 bit prefix.  Thus in the 64 bit format
the full range of up to 128 registers is directly available. This for
both when either scalar or vector mode is set.

Load/Store Kind (lsk) Field Encoding
====================================

+--------+-----+--------------------------------------------------------------------------------+
| vd/vs2 | vs1 | Meaning                                                                        |
+========+=====+================================================================================+
| 0      | 0   | srcbase is scalar, LD/ST is pure scalar.                                       |
+--------+-----+--------------------------------------------------------------------------------+
| 1      | 0   | srcbase is scalar, LD/ST is unit strided                                       |
+--------+-----+--------------------------------------------------------------------------------+
| 0      | 1   | srcbase is a vector (gather/scatter aka array of srcbases). VSPLAT and VSELECT |
+--------+-----+--------------------------------------------------------------------------------+
| 1      | 1   | srcbase is a vector, LD/ST is a full vector LD/ST.                             |
+--------+-----+--------------------------------------------------------------------------------+

Notes:

* A register strided LD/ST would require *5* registers. srcbase, vd/vs2,
  predicate 1, predicate 2 and the stride register.
* Complex strides may all be done with a general purpose vector of srcbases.
* Twin predication may be used even when vd/vs1 is a scalar, to give
  VSPLAT and VSELECT, because the hardware loop ends on the first occurrence
  of a 1 in the predicate when a predicate is applied to a scalar.
* Full vectorised gather/scatter is enabled when both registers are
  marked as vectorised, however unlike e.g Intel AVX512, twin predication
  can be applied.

Open question: RVV overloads the width field of LOAD-FP/STORE-FP
using the bit 2 to indicate additional interpretation of the 11 bit
immediate. Should this be considered?


Sub-Vector Length (svlen) Field Encoding
========================================

NOTE: svlen is not the same as the main spec SUBVL.  When nondefault (not zero) SVPSTATE context is used for Sub vector loops. However is svlen is zero, STATE and SUBVL is used instead.

Bitwidth, from VL's perspective, is a multiple of the elwidth times svlen.
So within each loop of VL there are svlen sub-elements of elwidth in size,
just like in a SIMD architecture. When svlen is set to 0b00 (indicating
svlen=1) no such SIMD-like behaviour exists and the subvectoring is
disabled.

Predicate bits do not apply to the individual sub-vector elements, they
apply to the entire subvector group. This saves instructions on setup
of the predicate.

+----------------+-------+
| svlen Encoding | Value |
+================+=======+
| 00             | SUBVL |
+----------------+-------+
| 01             | 2     |
+----------------+-------+
| 10             | 3     |
+----------------+-------+
| 11             | 4     |
+----------------+-------+

In independent standalone implementations that do not implement the
main specification, the value of SUBVL in the above table (svtyp=0b00)
is set to 1, such that svlen is also 1.

Behaviour of operations that set svlen are identical to those of the
main spec. See section on VLtyp, above.

Predication (pred) Field Encoding
=================================

+------+------------+--------------------+----------------------------------------+
| pred | Mnemonic   | Predicate Register | Meaning                                |
+======+============+====================+========================================+
| 000  | *None*     | *None*             | The instruction is unpredicated        |
+------+------------+--------------------+----------------------------------------+
| 001  | *Reserved* | *Reserved*         |                                        |
+------+------------+--------------------+----------------------------------------+
| 010  | !x9        | x9 (s1)            | execute vector op[0..i] on x9[i] == 0  |
+------+------------+                    +----------------------------------------+
| 011  | x9         |                    | execute vector op[0..i] on x9[i] == 1  |
+------+------------+--------------------+----------------------------------------+
| 100  | !x10       | x10 (a0)           | execute vector op[0..i] on x10[i] == 0 |
+------+------------+                    +----------------------------------------+
| 101  | x10        |                    | execute vector op[0..i] on x10[i] == 1 |
+------+------------+--------------------+----------------------------------------+
| 110  | !x11       | x11 (a1)           | execute vector op[0..i] on x11[i] == 0 |
+------+------------+                    +----------------------------------------+
| 111  | x11        |                    | execute vector op[0..i] on x11[i] == 1 |
+------+------------+--------------------+----------------------------------------+

Twin-predication (tpred) Field Encoding
=======================================

Twin-predication (ability to associate two predicate registers with an
instruction) applies to MV, FCLASS, LD and ST.  The same format also
applies to integer-branch-compare operations although it is **not** to be
considered "twin" predication.  In the case of integer-branch-compare
operations, the second register (if enabled) stores the results of the
element comparisons.  See Appendix_ for details.

+-------+------------+--------------------+----------------------------------------------+
| tpred | Mnemonic   | Predicate Register | Meaning                                      |
+=======+============+====================+==============================================+
| 000   | *None*     | *None*             | The instruction is unpredicated              |
+-------+------------+--------------------+----------------------------------------------+
| 001   | x9,off     | src=x9, dest=none  | src[0..i] uses x9[i], dest unpredicated      |
+-------+------------+                    +----------------------------------------------+
| 010   | off,x10    | src=none, dest=x10 | dest[0..i] uses x10[i], src unpredicated     |
+-------+------------+                    +----------------------------------------------+
| 011   | x9,10      | src=x9, dest=x10   | src[0..i] uses x9[i], dest[0..i] uses x10[i] |
+-------+------------+--------------------+----------------------------------------------+
| 100   | *None*     | *RESERVED*         | Instruction is unpredicated (TBD)            |
+-------+------------+--------------------+----------------------------------------------+
| 101   | !x9,off    | src=!x9, dest=none |                                              |
+-------+------------+                    +----------------------------------------------+
| 110   | off,!x10   | src=none, dest=!x10|                                              |
+-------+------------+                    +----------------------------------------------+
| 111   | !x9,!x10   | src=!x9, dest=!x10 |                                              |
+-------+------------+--------------------+----------------------------------------------+

Integer Element Type (itype) Field Encoding
===========================================

+------------+-------+--------------+--------------+-----------------+-------------------+
| Signedness | itype | Element Type | Mnemonic in  | Mnemonic in FP  | Meaning (INT may  |
| [#sgn_def]_|       |              | Integer      | Instructions    | be un/signed, FP  |
| [#sgn_def]_|       |              | Instructions | (such as fmv.x) | just re-sized     |
+============+=======+==============+==============+=================+===================+
| Unsigned   | 01    | u8           | BU           | BU              | Unsigned 8-bit    |
|            +-------+--------------+--------------+-----------------+-------------------+
|            | 10    | u16          | HU           | HU              | Unsigned 16-bit   |
|            +-------+--------------+--------------+-----------------+-------------------+
|            | 11    | u32          | WU           | WU              | Unsigned 32-bit   |
|            +-------+--------------+--------------+-----------------+-------------------+
|            | 00    | uXLEN        | WU/DU/QU     | WU/LU/TU        | Unsigned XLEN-bit |
+------------+-------+--------------+--------------+-----------------+-------------------+
| Signed     | 01    | i8           | BS           | BS              | Signed 8-bit      |
|            +-------+--------------+--------------+-----------------+-------------------+
|            | 10    | i16          | HS           | HS              | Signed 16-bit     |
|            +-------+--------------+--------------+-----------------+-------------------+
|            | 11    | i32          | W            | W               | Signed 32-bit     |
|            +-------+--------------+--------------+-----------------+-------------------+
|            | 00    | iXLEN        | W/D/Q        | W/L/T           | Signed XLEN-bit   |
+------------+-------+--------------+--------------+-----------------+-------------------+

.. [#sgn_def] Signedness is defined in `Signedness Decision Procedure`_

Note: vector mode is effectively a type-cast of the register file
as if it was a sequential array being typecast to typedef itype[]
(c syntax).  The starting point of the "typecast" is the vector
register rs#/rd.

Example: if itype=0b10 (u16), and rd is set to "vector", and
VL is set to 4, the 64-bit register at rd is subdivided into
*FOUR* 16-bit destination elements.  It is *NOT* four
separate 64-bit destination registers (rd+0, rd+1, rd+2, rd+3)
that are sign-extended from the source width size out to 64-bit,
because that is itype=0b00 (uXLEN).

Note also: changing elwidth creates packed elements that, depending on
VL, may create vectors that do not fit perfectly onto XLEN sized registry
file bit-boundaries. This does NOT result in the destruction of the MSBs
of the last register written to at the end of a VL loop. More details
on how to handle this are described in the main Specification_.

Signedness Decision Procedure
=============================

1. If the opcode field is either OP or OP-IMM, then
    1. Signedness is Unsigned.
2. If the opcode field is either OP-32 or OP-IMM-32, then
    1. Signedness is Signed.
3. If Signedness is encoded in a field of the base instruction, [#sign_enc]_ then
    1. Signedness uses the encoded value.
4. Otherwise,
    1. Signedness is Unsigned.

.. [#sign_enc] Like in fcvt.d.l[u], but unlike in fmv.x.w,
               since there is no fmv.x.wu

Vector Type and Predication 5-bit (vtp5) Field Encoding
=========================================================

In the following table, X denotes a wildcard that is 0 or 1 and can be
a different value for every occurrence.

+-------+-----------+-----------+
| vtp5  | pred      | svlen     |
+=======+===========+===========+
| 1XXXX | vtp5[4:2] | vtp5[1:0] |
+-------+           |           |
| 01XXX |           |           |
+-------+           |           |
| 000XX |           |           |
+-------+-----------+-----------+
| 001XX | *Reserved*            |
+-------+-----------------------+

Vector Integer Type and Predication 6-bit (vitp6) Field Encoding
=================================================================

In the following table, X denotes a wildcard that is 0 or 1 and can be a
different value for every occurrence.

+--------+------------+---------+------------+------------+
| vitp6  | itype      | pred[2] | pred[0:1]  | svlen      |
+========+============+=========+============+============+
| XX1XXX | vitp6[5:4] | 0       | vitp6[3:2] | vitp6[1:0] |
+--------+            |         |            |            |
| XX00XX |            |         |            |            |
+--------+------------+---------+------------+------------+
| XX01XX | *Reserved*                                     |
+--------+------------------------------------------------+

vitp7 field: only tpred

+---------+------------+----------+-------------+------------+
| vitp7   | itype      | tpred[2] | tpred[0:1]  | svlen      |
+=========+============+==========+=============+============+
| XXXXXXX | vitp7[5:4] | vitp7[6] | vitp7[3:2]  | vitp7[1:0] |
+---------+------------+----------+-------------+------------+

48-bit Instruction Encoding Decision Procedure
==============================================

In the following decision procedure, *Reserved* means that there is not
yet a defined 48-bit instruction encoding for the base instruction.

1. If the base instruction is a load instruction, then
    a. If the base instruction is an I-type instruction, then
        1. The encoding is P48-LD-type.
    b. Otherwise
        1. The encoding is *Reserved*.
2. If the base instruction is a store instruction, then
    a. If the base instruction is an S-type instruction, then
        1. The encoding is P48-ST-type.
    b. Otherwise
        1. The encoding is *Reserved*.
3. If the base instruction is a SYSTEM instruction, then
    a. The encoding is *Reserved*.
4. If the base instruction is an integer instruction, then
    a. If the base instruction is an R-type instruction, then
        1. The encoding is P48-R-type.
    b. If the base instruction is an I-type instruction, then
        1. The encoding is P48-I-type.
    c. If the base instruction is an S-type instruction, then
        1. The encoding is *Reserved*.
    d. If the base instruction is an B-type instruction, then
        1. The encoding is *Reserved*.
    e. If the base instruction is an U-type instruction, then
        1. The encoding is P48-U-type.
    f. If the base instruction is an J-type instruction, then
        1. The encoding is *Reserved*.
    g. Otherwise
        1. The encoding is *Reserved*.
5. If the base instruction is a floating-point instruction, then
    a. If the base instruction is an R-type instruction, then
        1. The encoding is P48-FR-type.
    b. If the base instruction is an I-type instruction, then
        1. The encoding is P48-FI-type.
    c. If the base instruction is an S-type instruction, then
        1. The encoding is *Reserved*.
    d. If the base instruction is an B-type instruction, then
        1. The encoding is *Reserved*.
    e. If the base instruction is an U-type instruction, then
        1. The encoding is *Reserved*.
    f. If the base instruction is an J-type instruction, then
        1. The encoding is *Reserved*.
    g. If the base instruction is an R4-type instruction, then
        1. The encoding is P48-FR4-type.
    h. Otherwise
        1. The encoding is *Reserved*.
6. Otherwise
    a. The encoding is *Reserved*.

CSR Registers
=============

CSRs are the same as in the main Specification_, if associated
functionality is implemented. They have the exact same meaning as in
the main specification.

* VL
* MVL
* SVPSTATE
* SUBVL

Associated SET and GET on the CSRs is exactly as in the main spec as well
(including CSRRWI and CSRRW differences).

Note that if both VLtyp and svlen are not implemented, SVPSTATE is not required. Also if VL and SUBVL are not implemented, STATE from the main Specification_ is not required either.

However if partial functionality is implemented, the unimplemented bits
in STATE and SVPSTATE must be zero, and, in the UNIX Platform, an illegal exception
**MUST** be raised if unsupported bits are written to.

SVPSTATE fields are exactly the same layout as STATE:

+----------+----------+----------+----------+----------+---------+---------+
| (31..28) | (27..26) | (25..24) | (23..18) | (17..12) | (11..6) | (5...0) |
+----------+----------+----------+----------+----------+---------+---------+
| rsvd     | dsvoffs  | subvl    | destoffs | srcoffs  | vl      | maxvl   |
+----------+----------+----------+----------+----------+---------+---------+

However note that where STATE stores the scalar register number to be used as VL, SVPSTATE.VL actually contains the actual VL value, in an identical fashion to RVV.

Additional Instructions
=======================

* Add instructions to convert between integer types.
* Add instructions to `swizzle`_ elements in sub-vectors. Note that
  the sub-vector lengths of the source and destination won't necessarily
  match.
* Add instructions to transpose (2-4)x(2-4) element matrices.
* Add instructions to insert or extract a sub-vector from a vector, with
  the index allowed to be both immediate and from a register (*immediate
  can be covered by twin-predication, register might be, by virtue of
  predicates being registers*)
* Add a register gather instruction (aka MV.X: regfile[rd] =
  regfile[regfile[rs1]])

subelement swizzle example:

    velswizzle x32, x64, SRCSUBVL=3, DESTSUBVL=4, ELTYPE=u8, elements=[0, 0, 2, 1]

.. _swizzle: https://www.khronos.org/opengl/wiki/Data_Type_(GLSL)#Swizzling

questions
=========

Moved to the discussion page (link at top of this page)

TODO
====

Work out a way to do sub-element swizzling.

