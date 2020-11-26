#!/bin/bash
mapfile -t lines <<'EOF'
addi r3, r4, 5
paddi r3, r5, 0xDEADBEEF
x.placeholder
addi r3, r4, 5
paddi r3, r5, 0x89ABCDEF
x.placeholder
h.add r3, r4
addi r3, r6, 7
hs.add r3, r31
c.add r3, r30
cst.add r3, r29
paddi r3, r31, 0x12345678
c.add r3, r5
c.add r3, r3
cs.add r3, r6
addi r3, r3, 0x23
addi r3, r10, 0xA
hs.add r3, r5
cst.add r3, r4
hs.add r3, r6
cst.add r3, r28
h.add r3, r29
cst.add r3, r30
x.placeholder
cst.add r3, r31
addi r3, r15, 0xF
cs.add r3, r4
addi r3, r10, 0xF
addi r3, r11, 0xF
EOF

declare -a small_regs
small_regs[3]=0
small_regs[4]=1
small_regs[5]=2
small_regs[6]=3
small_regs[28]=4
small_regs[29]=5
small_regs[30]=6
small_regs[31]=7
colors=("800" "880" "080" "088" "008" "808")
pc=0x1000
initial_pc=$((pc))
bytes=()
function out_byte_text() {
    local s
    printf -v s '| %4s | %6s | %-30s |' "$1" "$2" "$3"
    bytes+=("$s")
}
function out_byte() {
    local a b
    printf -v a '0x%02X' $(($1))
    printf -v b '0x%04X' $((pc))
    local l="$line"
    if ((${#colors[@]} != 0)); then
        local color="${colors[(pc - initial_pc) / 2 % ${#colors[@]}]}"
        a="<div class=\"color-$color\">$a</div>"
        b="<div class=\"color-$color\">$b</div>"
        l="<div class=\"color-$color\">$l</div>"
    fi
    out_byte_text "$a" "$b" "$l"
}
function out_16() {
    out_byte $(($1 >> 8))
    out_byte $(($1 & 0xFF))
}
function out_32() {
    out_16 $(($1 >> 16))
    out_16 $(($1 & 0xFFFF))
}
for line in "${lines[@]}"; do
    if [[ "$line" =~ ^([a-z0-9.]+)(' '+'r'?([0-9]+)','' '*'r'?([0-9]+)(','' '*([0-9xA-Fa-f]+))?)?$ ]]; then
        opcode="${BASH_REMATCH[1]}"
        arg1="${BASH_REMATCH[3]}"
        arg2="${BASH_REMATCH[4]}"
        arg3="${BASH_REMATCH[6]}"
    else
        echo "invalid line: $line"
        exit 1
    fi
    arg1s="${small_regs[arg1]}"
    arg2s="${small_regs[arg2]}"
    case "$opcode" in
    addi)
        out_32 $((14 << 31 - 5 | arg1 << 31 - 10 | arg2 << 31 - 15 | arg3 & 0xFFFF))
        ((pc += 4))
        ;;
    paddi)
        out_32 $((1 << 31 - 5 | 2 << 31 - 7 | (arg3 >> 16) & 0x3FFFF))
        out_32 $((14 << 31 - 5 | arg1 << 31 - 10 | arg2 << 31 - 15 | arg3 & 0xFFFF))
        ((pc += 8))
        ;;
    x.placeholder)
        out_32 $((0 << 31 - 5 | 1 << 31 - 30))
        out_16 0
        ((pc += 6))
        ;;
    h.add)
        out_16 $((5 << 15 - 5 | arg1s << 15 - 11 | arg2s << 15 - 14))
        ((pc += 2))
        ;;
    hs.add)
        out_16 $((5 << 15 - 5 | arg1s << 15 - 11 | arg2s << 15 - 14 | 1))
        ((pc += 2))
        ;;
    c.add)
        out_16 $((1 << 15 - 5 | arg1s << 15 - 11 | arg2s << 15 - 14))
        ((pc += 2))
        ;;
    cs.add)
        out_16 $((1 << 15 - 5 | arg1s << 15 - 11 | arg2s << 15 - 14 | 1))
        ((pc += 2))
        ;;
    cst.add)
        out_16 $((1 << 15 | 1 << 15 - 5 | arg1s << 15 - 11 | arg2s << 15 - 14 | 1))
        ((pc += 2))
        ;;
    *)
        echo "invalid opcode: $opcode"
        echo "line: $line"
        exit 1
        ;;
    esac
done
while ((${#bytes[@]} % 4 != 0)); do
    out_byte_text "" "" ""
done
function write() {
    local i
    local endian="$1"
    local endian_bits=$(($2))
    echo "## $endian Machine Code"
    echo
    echo "| Address | Byte | PC     | Instruction                    |"
    echo "|---------|------|--------|--------------------------------|"
    for((i=0;i<${#bytes[@]};i++)); do
        printf "| 0x%04X  %s\n" $((i + initial_pc)) "${bytes[i ^ endian_bits]}"
    done
}
write "Big-Endian" 0
echo
write "Little-Endian" 3
