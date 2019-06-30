RVC
===

The comment in the RVC section says that the Opcodes will be evaluated to see which are most useful to provide.

This takes a huge amount of time and, if not *exactly* RVC, would require a special decode engine, taking up extra gates as well as need time to develop.

Far better to just embed RVC into the opcode and prefix it. This is inline with the strategic principle behind SV: "No new opcodes, only prefixed augmentation"

Taking an entire major 32 bit opcode (or two) seems logical (RV128 space). I type funct3 to specify the C type page, Imm 12 bits for the operation.

Or, just "to hell with it" and just take the entire opcode and stuff C into it, no regard for R/I/U/S and instead do whatever we like.


+----------+------+---------------------+---------------------+-------+--------+
| 15 14 13 |  12  |   11 10 9     8   7 | 6    5    4   3   2 | 1   0 | format |
+----------+------+---------------------+---------------------+-------+--------+
|    funct4       |     rd/rs1          |      rs2            | op    | CR     |
+----------+------+---------------------+---------------------+-------+--------+
|funct3    | imm  |     rd/rs1          |     imm             | op    | CI     |
+----------+------+---------------------+---------------------+-------+--------+
|funct3    |          imm               |      rs2            | op    | CSS    |
+----------+----------------------------+---------+-----------+-------+--------+
|funct3    |              imm                     |  rd'      | op    | CIW    |
+----------+----------------+-----------+---------+-----------+-------+--------+
|funct3    |    imm         | rs1'      | imm     |  rd'      | op    | CL     |
+----------+----------------+-----------+---------+-----------+-------+--------+
|funct3    |    imm         | rs1'      | imm     |  rs2'     | op    | CS     |
+----------+----------------+-----------+---------+-----------+-------+--------+
|       funct6              | rd'/rs1'  | funct2  |  rs2'     | op    | CA     |
+----------+----------------+-----------+---------+-----------+-------+--------+
|funct3    |   offset       |  rs1'     |     offset          | op    | CB     |
+----------+----------------+-----------+---------------------+-------+--------+
|funct3    |                jump target                       | op    | CJ     |
+----------+--------------------------------------------------+-------+--------+

* top 14 bits of RVC to go into "MAJOR OPCODE 0-2" to represent
  RVC op[1:0] == 0b00, 0b01 and 0b02.  Therefore,
  18 bits remain in the 32-bit opcode space
* 32-bit opcode prefix takes 7 bits, therefore 11 bits remain to fit
  a SVPrefix.
* compared to P48, 11 bits are needed, and we have a match.

P48:

+---------------+--------+--------+----------+-----+--------+-------------+------+
| Encoding      | 17     | 16     | 15       | 14  | 13     | 12          | 11:7 |
+---------------+--------+--------+----------+-----+--------+-------------+------+
| P32C-LD-type  | rd[5]  | rs1[5] | vitp7[6] | vd  | vs1    | vitp7[5:0]         |
+---------------+--------+--------+----------+-----+--------+-------------+------+
| P32C-ST-type  |vitp7[6]| rs1[5] | rs2[5]   | vs2 | vs1    | vitp7[5:0]         |
+---------------+--------+--------+----------+-----+--------+-------------+------+
| P32C-R-type   | rd[5]  | rs1[5] | rs2[5]   | vs2 | vs1    | vitp6              |
+---------------+--------+--------+----------+-----+--------+--------------------+
| P32C-I-type   | rd[5]  | rs1[5] | vitp7[6] | vd  | vs1    | vitp7[5:0]         |
+---------------+--------+--------+----------+-----+--------+--------------------+
| P32C-U-type   | rd[5]  | *Rsvd* | *Rsvd*   | vd  | *Rsvd* | vitp6              |
+---------------+--------+--------+----------+-----+--------+-------------+------+
| P32C-FR-type  | rd[5]  | rs1[5] | rs2[5]   | vs2 | vs1    | *Rsvd*      | vtp5 |
+---------------+--------+--------+----------+-----+--------+-------------+------+
| P32C-FI-type  | rd[5]  | rs1[5] | vitp7[6] | vd  | vs1    | vitp7[5:0]         |
+---------------+--------+--------+----------+-----+--------+-------------+------+
| P32C-FR4-type | rd[5]  | rs1[5] | rs2[5]   | vs2 | rs3[5] | vs3 [#fr4]_ | vtp5 |
+---------------+--------+--------+----------+-----+--------+-------------+------+

P32C Prefix:

+---------------+--------+--------+----------+-----+--------+------------+
| Encoding      | 31     | 30     | 29       | 28  | 27     | 26:21      |
+---------------+--------+--------+----------+-----+--------+------------+
| P32C-CL-type  | rd[5]  | rs1[5] | vitp7[6] | vd  | vs1    | vitp7[5:0] |
+---------------+--------+--------+----------+-----+--------+------------+
| P32C-CS-type  |vitp7[6]| rs1[5] | rs2[5]   | vs2 | vs1    | vitp7[5:0] |
+---------------+--------+--------+----------+-----+--------+------------+
| P32C-CR-type  | rd[5]  | rs1[5] | *Rsvd*   | vd  | vs1    | vitp6      |
+---------------+--------+--------+----------+-----+--------+------------+
| P32C-CI1-type | rd[5]  | rs1[5] | vitp7[6] | vd  | vs1    | vitp7[5:0] |
+---------------+--------+--------+----------+-----+--------+------------+
| P32C-CI2-type | rd[5]  | *Rsvd* | *Rsvd*   | vd  | *Rsvd* | vitp6      |
+---------------+--------+--------+----------+-----+--------+------------+
| P32C-CMv-type | rd[5]  | rs1[5] | vitp7[6] | vd  | vs1    | vitp7[5:0] |
+---------------+--------+--------+----------+-----+--------+------------+

Mapping P32-* Quadrants 0-2 to CUSTOM OPCODEs 0-2:

+-------------+--------+-----------+----------+
| Encoding    | 31:21  | 20:7      | 6:0      |
+-------------+--------+-----------+----------+
| P32C RVC-Q0 | P32-*  | RVC[15:2] | OPCODE-0 |
+-------------+--------+-----------+----------+
| P32C RVC-Q1 | P32-*  | RVC[15:2] | OPCODE-1 |
+-------------+--------+-----------+----------+
| P32C RVC-Q2 | P32-*  | RVC[15:2] | OPCODE-2 |
+-------------+--------+-----------+----------+

Questions
=========

Confirmation needed as to whether subvector extraction can be covered
by twin predication (it probably can, it is one of the many purposes it
is for).

Answer:

Yes, it can, but VL needs to be changed for it to work, since predicates
work at the size of a whole subvector instead of an element of that
subvector. To avoid needing to constantly change VL, and since swizzles
are a very common operation, I think we should have a separate instruction
-- a subvector element swizzle instruction::

    velswizzle x32, x64, SRCSUBVL=3, DESTSUBVL=4, ELTYPE=u8, elements=[0, 0, 2, 1]

Answer:

    > ok, i like that idea - adding to TODO list
    > see MV.X_

.. _MV.X: http://libre-riscv.org/simple_v_extension/specification/mv.x/

Example pseudocode:

.. code:: C

    // processor state:
    uint64_t regs[128];
    int VL = 5;

    typedef uint8_t ELTYPE;
    const int SRCSUBVL = 3;
    const int DESTSUBVL = 4;
    const int elements[] = [0, 0, 2, 1];
    ELTYPE *rd = (ELTYPE *)&regs[32];
    ELTYPE *rs1 = (ELTYPE *)&regs[48];
    for(int i = 0; i < VL; i++)
    {
        rd[i * DESTSUBVL + 0] = rs1[i * SRCSUBVL + elements[0]];
        rd[i * DESTSUBVL + 1] = rs1[i * SRCSUBVL + elements[1]];
        rd[i * DESTSUBVL + 2] = rs1[i * SRCSUBVL + elements[2]];
        rd[i * DESTSUBVL + 3] = rs1[i * SRCSUBVL + elements[3]];
    }

To use the subvector element swizzle instruction to extract a subvector element,
all that needs to be done is to have DESTSUBVL be 1::

    // extract element index 2
    velswizzle rd, rs1, SRCSUBVL=4, DESTSUBVL=1, ELTYPE=u32, elements=[2]

Example pseudocode:

.. code:: C

    // processor state:
    uint64_t regs[128];
    int VL = 5;

    typedef uint32_t ELTYPE;
    const int SRCSUBVL = 4;
    const int DESTSUBVL = 1;
    const int elements[] = [2];
    ELTYPE *rd = (ELTYPE *)&regs[...];
    ELTYPE *rs1 = (ELTYPE *)&regs[...];
    for(int i = 0; i < VL; i++)
    {
        rd[i * DESTSUBVL + 0] = rs1[i * SRCSUBVL + elements[0]];
    }

----

What is SUBVL and how does it work

Answer:

SUBVL is the instruction field in P48 instructions that specifies
the sub-vector length. The sub-vector length is the number of scalars
that are grouped together and treated like an element by both VL and
predication. This is used to support operations where the elements are
short vectors (2-4 elements) in Vulkan and OpenGL. Those short vectors
are mostly used as mathematical vectors to handle directions, positions,
and colors, rather than as a pure optimization.

For example, when VL is 5::

    add x32, x48, x64, SUBVL=3, ELTYPE=u16, PRED=!x9

performs the following operation:

.. code:: C

    // processor state:
    uint64_t regs[128];
    int VL = 5;

    // instruction fields:
    typedef uint16_t ELTYPE;
    const int SUBVL = 3;
    ELTYPE *rd = (ELTYPE *)&regs[32];
    ELTYPE *rs1 = (ELTYPE *)&regs[48];
    ELTYPE *rs2 = (ELTYPE *)&regs[64];
    for(int i = 0; i < VL; i++)
    {
        if(~regs[9] & 0x1)
        {
            rd[i * SUBVL + 0] = rs1[i * SUBVL + 0] + rs2[i * SUBVL + 0];
            rd[i * SUBVL + 1] = rs1[i * SUBVL + 1] + rs2[i * SUBVL + 1];
            rd[i * SUBVL + 2] = rs1[i * SUBVL + 2] + rs2[i * SUBVL + 2];
        }
    }

----

SVorig goes to a lot of effort to make VL 1<= MAXVL and MAXVL 1..64
where both CSRs may be stored internally in only 6 bits.

Thus, CSRRWI can reach 1..32 for VL and MAXVL.

In addition, setting a hardware loop to zero turning instructions into
NOPs, um, just branch over them, to start the first loop at the end,
on the test for loop variable being zero, a la c "while do" instead of
"do while".

Or, does it not matter that VL only goes up to 31 on a CSRRWI, and that
it only goes to a max of 63 rather than 64?

Answer:

I think supporting SETVL where VL would be set to 0 should be done. that
way, the branch can be put after SETVL, allowing SETVL to execute
earlier giving more time for VL to propagate (preventing stalling)
to the instruction decoder.  I have no problem with having 0 stored to
VL via CSRW resulting in VL=64 (or whatever maximum value is supported
in hardware).

One related idea would to support VL > XLEN but to only allow unpredicated
instructions when VL > XLEN. This would allow later implementing register
pairs/triplets/etc. as predicates as an extension.

----

Is MV.X good enough a substitute for swizzle?

Answer:

no, since the swizzle instruction specifies in the opcode which elements are
used and where they go, so it can run much faster since the execution engine
doesn't need to pessimize. Additionally, swizzles almost always have constant
element selectors. MV.X is meant more as a last-resort instruction that is
better than load/store, but worse than everything else.

    > ok, then we'll need a way to do that.  given that it needs to apply
    > to, well... everything, basically, i'm tempted to recommend it be
    > done as a CSR and/or as (another) table in VBLOCK.
    > the reason is, it's just too much to expect to massively duplicate
    > literally every single opcode in existence, just to add swizzle
    > when there's no room in the opcode space to do so.
    > not sure what alternatives there might be.

----

Is vectorised srcbase ok as a gather scatter and ok substitute for
register stride? 5 dependency registers (reg stride being the 5th)
is quite scary

----

Why are integer conversion instructions needed, when the main SV spec
covers them by allowing elwidth to be set on both src and dest regs?

----

Why are the SETVL rules so complex? What is the reason, how are loops
carried out?

Partial Answer:

The idea is that the compiler knows maxVL at compile time since it allocated the
backing registers, so SETVL has the maxVL as an immediate value. There is no
maxVL CSR needed for just SVPrefix.

    > when looking at a loop assembly sequence
    > i think you'll find this approach will not work.
    > RVV loops on which SV loops are directly based needs understanding
    > of the use of MIN within the actual SETVL instruction.
    > Yes MVL is known at compile time
    > however unless MVL is communicates to the hardware, SETVL just
    > does not work: it has absolutely no way of knowing when to stop
    > processing.  The point being: it's not *MVL* that's the problem
    > if MVL is not a CSR, it's *VL* that becomes the problem.
    > The only other option which does work is to set a mandatory
    > hardcoded MVL baked into the actual hardware.
    > That results in loss of flexibility and defeats the purpose of SV. 

----

With SUBVL (sub vector len) being both a CSR and also part of the 48/64
bit opcode, how does that work?

Answer:

I think we should just ignore the SUBVL CSR and use the value from the
SUBVL field when executing 48/64-bit instructions. For just SVPrefix,
I would say that the only user-visible CSR needed is VL. This is ignoring
all the state for context-switching and exception handling.

    > the consequence of that would be that P48/64 would need
    > its own CSR State to track the subelement index.
    > or that any exceptions would need to occur on a group
    > basis, which is less than ideal,
    > and interrupts would have to be stalled.
    > interacting with SUBVL and requiring P48/64 to save the
    > STATE CSR if needed is a workable compromise that
    > does not result in huge CSR proliferation

----

What are the interaction rules when a 48/64 prefix opcode has a rd/rs
that already has a Vector Context for either predication or a register?

It would perhaps make sense (and for svlen as well) to make 48/64 isolated
and unaffected by VLIW context, with the exception of VL/MVL.

MVL and VL should be modifiable by 64 bit prefix as they are global
in nature.

Possible solution, svlen and VLtyp allowed to share STATE CSR however
programmer becomes responsible for push and pop of state during use of
a sequence of P48 and P64 ops.

----

Can bit 60 of P64 be put to use (in all but the FR4 case)?



experiment VLtyp
================

experiment 1:

+-----------+-------------+--------------+------------+----------------------+
| VLtyp[11] | VLtyp[10:6] | VLtyp[5:3]   | VLtyp[2:0] | comment              |
+-----------+-------------+--------------+------------+----------------------+
| 0         |  00000      | 000          |  000       | no change to VL/MVL  |
+-----------+-------------+--------------+------------+----------------------+
| 0         |  imm        | 000          |  rs'!=0    |                      |
+-----------+-------------+--------------+------------+----------------------+
| 0         |  imm        | rd'!=0       |  000       |                      |
+-----------+-------------+--------------+------------+----------------------+
| 0         |  imm        | rd'!=0       |  rs'!=0    |                      |
+-----------+-------------+--------------+------------+----------------------+
| 1         |  imm        | 000          |  000       |                      |
+-----------+-------------+--------------+------------+----------------------+
| 1         |  imm        | 000          |  rs'!=0    |                      |
+-----------+-------------+--------------+------------+----------------------+
| 1         |  imm        | rd'!=0       | 000        |                      |
+-----------+-------------+--------------+------------+----------------------+
| 1         |  imm        | rd'!=0       |  rs'!=0    |                      |
+-----------+-------------+--------------+------------+----------------------+


experiment 2:

+----+------+-----+-------+----------+-----------------------------------------------+
| 11 | 10:6 | 5   | 4:3   | 2:0      | comment                                       |
+----+------+-----+-------+----------+-----------------------------------------------+
| 0  |  000 | 000         |  000     | no change to VL/MVL                           |
+----+------+-------------+----------+-----------------------------------------------+
| 0  |  imm | 000         |  rs'!=0  | MVL = imm; vl = min(r[rs'], MVL)              |
+----+------+-------------+----------+-----------------------------------------------+
| 0  |  imm | rd'!=0      |  000     | MVL = imm; vl = MVL; r[rd'] = vl              |
+----+------+-------------+----------+-----------------------------------------------+
| 0  |  imm | rd'!=0      |  rs'!=0  | MVL = imm; vl = min(r[rs'], MVL); r[rd'] = vl |
+----+------+-----+-------+----------+-----------------------------------------------+
| 1  |  imm | 0   |  00      000     | MVL = imm; vl = MVL;                          |
+----+------+-----+------------------+-----------------------------------------------+
| 1  |  imm | 0   |  rd[4:0]         | MVL = imm; vl = MVL; r[rd] = vl               |
+----+------+-----+------------------+-----------------------------------------------+
| 1  |  imm | 1   |  00      000     | reserved                                      |
+----+------+-----+------------------+-----------------------------------------------+
| 1  |  imm | 1   |  rs1[4:0]        | MVL = imm; vl = min(r[rs], MVL)               |
+----+------+-----+------------------+-----------------------------------------------+

interestingly, "VLtyp[11] = 0" fits the sv.setvl pseudcode really well.
