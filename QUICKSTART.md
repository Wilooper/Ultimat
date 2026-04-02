# ULMT Quick Start

## 5-Minute Tutorial

### Installation
```bash
git clone https://github.com/Wilooper/Ultimat.git
cd Ultimat
chmod +x ulmt
```

### Your First Program
Create `hello.ulmt`:
```ulmt
print "Hello, World!"
```

Run it:
```bash
./ulmt hello.ulmt
```

Output:
```
Hello, World!
```

### More Examples

**Math:**
```ulmt
print 10 + 5 * 2      # Arithmetic (evaluated at compile time)
print (3 + 4) * 2     # Parentheses respected
print "2 + 2 = "
print 2 + 2
```

**String Concatenation:**
```ulmt
print "Hello" + " " + "ULMT"
```

**Inline Assembly (if you know ARM64):**
```ulmt
print "About to syscall..."
asm {
    mov x8, #64
    mov x0, #1
    svc #0
}
print "Done"
```

### CLI Options

```bash
# Run and display output
./ulmt program.ulmt

# Show generated ARM64 assembly
./ulmt program.ulmt --emit-asm

# Compile only (don't run)
./ulmt program.ulmt --no-run
```

## What ULMT Does

1. **Compiles** your `.ulmt` file to ARM64 assembly
2. **Assembles** with GNU `as` to machine code
3. **Links** with GNU `ld` to create a binary
4. **Runs** the binary and displays output

All in one command! No separate steps needed.

## Philosophy

- **C-speed**: Compiles to native ARM64 machine code
- **Python-soul**: Simple, readable syntax
- **Assembly heart**: Direct 1:1 mapping to real instructions

## Next Steps

- Read `README.md` for full language reference
- Check `COMPILER.md` for technical internals
- Explore example programs: `hello.ulmt`, `math.ulmt`, `concat.ulmt`
- Try writing your own programs!

## Roadmap

| Version | Features |
|---------|----------|
| v0.3.0 | print, arithmetic, strings, inline asm ✓ |
| v0.4 | variables: `let x = 10` |
| v0.5 | if/else conditionals |
| v0.6 | while loops |
| v0.7 | function definitions |
| v0.8 | type system |

---

**Ready? Write your first ULMT program!**

```bash
echo 'print "My first ULMT program!"' > myapp.ulmt
./ulmt myapp.ulmt
```
