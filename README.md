# ULMT Language — v0.3.0

```
 C-speed. Python-soul. Assembly heart.
 Target: ARM64 (Android / Termux / Linux AArch64)
```

ULMT is a thin, powerful wrapper over assembly.
Every language construct maps directly to real machine instructions.
No GC. No VM. No runtime. Pure native binary.

---

## Why ARM64?

You're on Android/Termux. Android uses ARM64 chips.
NASM only supports x86 — that's the `Exec format error` from v0.2.
v0.3.0 switches to GNU `as` targeting ARM64, which runs natively on your device.

---

## Install

```bash
pkg install binutils python
```

`binutils` gives you `as` (assembler) and `ld` (linker). That's all you need.

---

## Usage

```bash
python3 ulmt.py hello.ulmt             # compile + run
python3 ulmt.py hello.ulmt --emit-asm  # show generated ARM64 assembly
python3 ulmt.py hello.ulmt --no-run    # compile to binary, don't execute
```

---

## Syntax (v0.3.0)

### Print
```
print "Hello, World!"
print 42
print 10 + 5 * 2          # arithmetic (evaluated at compile time)
print (3 + 4) * (2 + 1)   # parens respected
print "Hello" + " World"  # string concat
```

### Inline Assembly
```
asm {
    mov x8, #64
    mov x0, #1
    ldr x1, =my_label
    mov x2, #my_label_len
    svc #0
}
```
Raw ARM64 instructions injected directly into the output `.s` file.
This is what makes ULMT a true assembly wrapper.

### Comments
```
# This is a comment
```

---

## What `print "Hi"` compiles to

```asm
    // print 'Hi'  (line 3)
    mov x8, #64          // sys_write
    mov x0, #1           // stdout
    ldr x1, =_s0         // pointer to "Hi\n" in .data
    mov x2, #_s0_len     // byte count
    svc #0               // kernel call
```

5 instructions. Exactly what you'd write by hand in assembly.

---

## ARM64 Syscall ABI

| Register | Role        |
|----------|-------------|
| `x8`     | Syscall number |
| `x0`     | Arg 1 (fd / exit code) |
| `x1`     | Arg 2 (buffer address) |
| `x2`     | Arg 3 (byte count) |
| `svc #0` | Trigger syscall |

| Syscall      | Number |
|--------------|--------|
| `sys_write`  | 64     |
| `sys_exit`   | 93     |

---

## Compiler Pipeline

```
hello.ulmt
    |
    v  Lexer  ->  Token stream
    |
    v  Parser  ->  AST
    |
    v  Constant Folder  (all arithmetic at compile time, zero runtime cost)
    |
    v  CodeGen  ->  hello.s  (ARM64 GNU as)
    |
    v  as (GNU assembler)  ->  hello.o
    |
    v  ld (GNU linker)  ->  hello  (native ARM64 binary)
```

---

## Roadmap

### Phase 1 — Language features
| Version | Status | Feature |
|---------|--------|---------|
| v0.1 | done | print string/int, x86-64 backend |
| v0.2 | done | arithmetic, operator precedence |
| v0.3 | done | ARM64 target, inline asm blocks |
| v0.4 | next | variables: `let x = 10` |
| v0.5 |      | if / else |
| v0.6 |      | loops |
| v0.7 |      | functions |
| v0.8 |      | type system: int, str, bool |

### Phase 2 — Compiler written in assembly

```
Stage 1 (now):   Python compiler  ->  ARM64 binary
Stage 2:         Write ULMT compiler in ULMT itself
Stage 3:         Compile the compiler with itself (self-hosting)
Stage 4:         Drop Python entirely — pure ASM toolchain
```

When the compiler is ARM64 assembly:
- Compiles in microseconds (no Python startup overhead)
- Proves ULMT is production-capable
- Zero dependencies: just one `ulmt` binary

---

*ULMT — one syscall at a time, all the way down.*
