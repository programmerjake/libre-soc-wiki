[[!tag oldstandards]]

MV.X and MV.swizzle
===================

swizzle needs a MV (there are 2 of them: swizzle and swizzle2).
see below for a potential way to use the funct7 to do a swizzle in rs2.

+---------------+-------------+-------+----------+----------+--------+----------+--------+--------+
| Encoding      | 31:27       | 26:25 | 24:20    | 19:15    | 14:12  | 11:7     | 6:2    | 1:0    |
+---------------+-------------+-------+----------+----------+--------+----------+--------+--------+
| RV32-I-type   + imm[11:0]                      + rs1[4:0] + funct3 | rd[4:0]  + opcode + 0b11   |
+---------------+-------------+-------+----------+----------+--------+----------+--------+--------+
| RV32-I-type   + fn4[3:0]    + swizzle[7:0]     + rs1[4:0] + 0b000  | rd[4:0]  + OP-V   + 0b11   |
+---------------+-------------+-------+----------+----------+--------+----------+--------+--------+

* funct3 = MV: 0b000 for FP, 0b001 for INT
* OP-V = 0b1010111
* fn4 = 4 bit function.
* fn4 = 0b0000 - MV-SWIZZLE
* fn4 = 0bNN01 - MV-X, NN=elwidth (default/8/16/32)
* fn4 = 0bNN11 - MV-X.SUBVL NN=elwidth (default/8/16/32)

swizzle (only active on SV or P48/P64 when SUBVL!=0):

+-----+-----+-----+-----+
| 7:6 | 5:4 | 3:2 | 1:0 |
+-----+-----+-----+-----+
|   w |   z |   y |   x |
+-----+-----+-----+-----+

MV.X has two modes: SUBVL mode applies the element offsets only within a SUBVL inner loop. This can be used for transposition.

::

  for i in range(VL):
     for j in range(SUBVL):
        regs[rd] = regs[rd+regs[rs+j]]

Normal mode will apply the element offsets incrementally:

::

  for i in range(VL):
     for j in range(SUBVL):
        regs[rd] = regs[rd+regs[rs+k]]
          k++


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

MV.X with 3 operands
====================

regs[rd] = regs[rs1 + regs[rs2]]

Similar to LD/ST with the same twin predication rules

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

<http://web.archive.org/web/20100111104515/http://www.randombit.net:80/bitbashing/programming/integer_matrix_transpose_in_sse2.html>


::

   __m128i T0 = _mm_unpacklo_epi32(I0, I1);
   __m128i T1 = _mm_unpacklo_epi32(I2, I3);
   __m128i T2 = _mm_unpackhi_epi32(I0, I1);
   __m128i T3 = _mm_unpackhi_epi32(I2, I3);

   /* Assigning transposed values back into I[0-3] */
   I0 = _mm_unpacklo_epi64(T0, T1);
   I1 = _mm_unpackhi_epi64(T0, T1);
   I2 = _mm_unpacklo_epi64(T2, T3);
   I3 = _mm_unpackhi_epi64(T2, T3);

Transforms for DCT 
==================

<https://opencores.org/websvn/filedetails?repname=mpeg2fpga&path=%2Fmpeg2fpga%2Ftrunk%2Frtl%2Fmpeg2%2Fidct.v>

Table to evaluate
=================

swizzle2 takes 2 arguments, interleaving the two vectors depending on a 3rd (the swizzle selector)

+-----------+-------+-------+-------+-------+-------+------+
|           | 31:27 | 26:25 | 24:20 | 19:15 | 14:12 | 11:7 |
+===========+=======+=======+=======+=======+=======+======+
| swizzle2  | rs3   | 00    | rs2   | rs1   | 000   | rd   |
+-----------+-------+-------+-------+-------+-------+------+
| fswizzle2 | rs3   | 01    | rs2   | rs1   | 000   | rd   |
+-----------+-------+-------+-------+-------+-------+------+
| swizzle   | 0     | 10    | rs2   | rs1   | 000   | rd   |
+-----------+-------+-------+-------+-------+-------+------+
| fswizzle  | 0     | 11    | rs2   | rs1   | 000   | rd   |
+-----------+-------+-------+-------+-------+-------+------+
| swizzlei  | imm                   | rs1   | 001   | rd   |
+-----------+                       +-------+-------+------+
| fswizzlei |                       | rs1   | 010   | rd   |
+-----------+-------+-------+-------+-------+-------+------+

More:

swizzlei would still need the 12-bit format due to not having enough immediate bits. we can get away with only 3 i-type funct3s used for [f]swizzlei by having one funct3 for destsubvl 1 through 3 for int and fp versions and a separate one for destsubvl = 4 that's shared between int/fp:

+--------+-----------+----+-----------+----------+-------+-------+------+
| int/fp | DESTSUBVL | 31 | 30:29     | 28:20    | 19:15 | 14:12 | 11:7 |
+========+===========+====+===========+==========+=======+=======+======+
| int    | 1 to 3    | 0  | DESTSUBVL | selector | rs    | 000   | rd   |
+--------+-----------+----+-----------+----------+-------+-------+------+
| fp     | 1 to 3    | 1  | DESTSUBVL | selector | rs    | 000   | rd   |
+--------+-----------+----+-----------+----------+-------+-------+------+
| int    | 4         | selector[11:0]            | rs    | 001   | rd   |
+--------+-----------+---------------------------+-------+-------+------+
| fp     | 4         | selector[11:0]            | rs    | 010   | rd   |
+--------+-----------+---------------------------+-------+-------+------+

the rest could be encoded as follows:

+-----------+-------+-----------+-------+-------+-------+------+
|           | 31:27 | 26:25     | 24:20 | 19:15 | 14:12 | 11:7 |
+===========+=======+===========+=======+=======+=======+======+
| swizzle2  | rs3   | DESTSUBVL | rs2   | rs1   | 100   | rd   |
+-----------+-------+-----------+-------+-------+-------+------+
| swizzle   | rs1   | DESTSUBVL | rs2   | rs1   | 100   | rd   |
+-----------+-------+-----------+-------+-------+-------+------+
| fswizzle2 | rs3   | DESTSUBVL | rs2   | rs1   | 101   | rd   |
+-----------+-------+-----------+-------+-------+-------+------+
| fswizzle  | rs1   | DESTSUBVL | rs2   | rs1   | 101   | rd   |
+-----------+-------+-----------+-------+-------+-------+------+

note how for [f]swizzle, rs3 == rs1

so it uses 5 funct3 values overall, which is appropriate, since swizzle is probably right after muladd in usage in graphics shaders.

Alternative immed encoding

+--------+-----------+----------+-------+-------+------+
| int/fp | 31:28     | 27:20    | 19:15 | 14:12 | 11:7 |
+========+===========+==========+=======+=======+======+
| int    | DESTMASK  | selector | rs    | 000   | rd   |
+--------+-----------+----------+-------+-------+------+
| fp     | DESTMASK  | selector | rs    | 001   | rd   |
+--------+-----------+----------+-------+-------+------+ 
| int    | DESTMASK  | constsel | rs    | 010   | rd   |
+--------+-----------+----------+-------+-------+------+
| fp     | DESTMASK  | constsel | rs    | 011   | rd   |
+--------+-----------+----------+-------+-------+------+

Allows setting of arbitrary dest (xz, yw) without needing register-versions. Saves on instruction count.
Needs 4 funct3 to express.

Matrix 4x4 Vector mul
=====================

::

    pfscale,3 F2, F1, F10
    pfscaleadd,2 F2, F1, F11, F2
    pfscaleadd,1 F2, F1, F12, F2
    pfscaleadd,0 F2, F1, F13, F2

pfscale is a 4 vec mv.shuffle followed by a fmul. pfscaleadd is a 4 vec mv.shuffle followed by a fmac.

In effect what this is doing is:

::

    fmul f2, f1.xxxx, f10
    fmac f2, f1.yyyy, f11, f2
    fmac f2, f1.zzzz, f12, f2
    fmac f2, f1.wwww, f13, f2

Where all of f2, f1, and f10-13 are vec4, and f1.x-w are copied (fixed index) where the other vec4 indices progress.

Pseudocode
==========

Swizzle:

::

    pub trait SwizzleConstants: Copy + 'static {
        const CONSTANTS: &'static [Self; 4];
    }

    impl SwizzleConstants for u8 {
        const CONSTANTS: &'static [Self; 4] = &[0, 1, 0xFF, 0x7F];
    }

    impl SwizzleConstants for u16 {
        const CONSTANTS: &'static [Self; 4] = &[0, 1, 0xFFFF, 0x7FFF];
    }

    impl SwizzleConstants for f32 {
        const CONSTANTS: &'static [Self; 4] = &[0.0, 1.0, -1.0, 0.5];
    }

    // impl for other types too...

    pub fn swizzle<Elm, Selector>(
        rd: &mut [Elm],
        rs1: &[Elm],
        rs2: &[Selector],
        vl: usize,
        destsubvl: usize,
        srcsubvl: usize)
    where
        Elm: SwizzleConstants,
        // Selector is a copyable type that can be converted into u64
        Selector: Copy + Into<u64>,
    {
        const FIELD_SIZE: usize = 3;
        const FIELD_MASK: u64 = 0b111;
        for vindex in 0..vl {
            let selector = rs2[vindex].into();
            // selector's type is u64
            if selector >> (FIELD_SIZE * destsubvl) != 0 {
                // handle illegal instruction trap
            }
            for i in 0..destsubvl {
                let mut sel_field = selector >> (FIELD_SIZE * i);
                sel_field &= FIELD_MASK;
                let src = if (sel_field & 0b100) == 0 {
                    &rs1[(vindex * srcsubvl)..]
                } else {
                    SwizzleConstants::CONSTANTS
                };
                sel_field &= 0b11;
                if sel_field as usize >= srcsubvl {
                    // handle illegal instruction trap
                }
                let value = src[sel_field as usize];
                rd[vindex * destsubvl + i] = value;
            }
        }
    }

Swizzle2:

::

    fn swizzle2<Elm, Selector>(
        rd: &mut [Elm],
        rs1: &[Elm],
        rs2: &[Selector],
        rs3: &[Elm],
        vl: usize,
        destsubvl: usize,
        srcsubvl: usize)
    where
        // Elm is a copyable type
        Elm: Copy,
        // Selector is a copyable type that can be converted into u64
        Selector: Copy + Into<u64>,
    {
        const FIELD_SIZE: usize = 3;
        const FIELD_MASK: u64 = 0b111;
        for vindex in 0..vl {
            let selector = rs2[vindex].into();
            // selector's type is u64
            if selector >> (FIELD_SIZE * destsubvl) != 0 {
                // handle illegal instruction trap
            }
            for i in 0..destsubvl {
                let mut sel_field = selector >> (FIELD_SIZE * i);
                sel_field &= FIELD_MASK;
                let src = if (sel_field & 0b100) != 0 {
                    rs1
                } else {
                    rs3
                };
                sel_field &= 0b11;
                if sel_field as usize >= srcsubvl {
                    // handle illegal instruction trap
                }
                let value = src[vindex * srcsubvl + (sel_field as usize)];
                rd[vindex * destsubvl + i] = value;
            }
        }
    }

