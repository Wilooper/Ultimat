# ULMT Installation & Setup

## System Requirements

- **Assembler**: GNU `as` (binutils)
- **Linker**: GNU `ld` (binutils)
- **Scripting**: Python 3.6+
- **Target**: ARM64 (Android/Termux/Linux AArch64)

## Installation

### On Termux (Android)
```bash
pkg install binutils python
git clone https://github.com/Wilooper/Ultimat.git
cd Ultimat
chmod +x ulmt ulmt.py
```

### On Linux (AArch64)
```bash
# Debian/Ubuntu
sudo apt install binutils python3

# Or Fedora/RHEL
sudo dnf install binutils python3

git clone https://github.com/Wilooper/Ultimat.git
cd Ultimat
chmod +x ulmt ulmt.py
```

## Usage

### Option 1: Direct Execution (Recommended)
```bash
./ulmt hello.ulmt
```

### Option 2: With Python
```bash
python3 ulmt.py hello.ulmt
```

### Options
```bash
# Show generated ARM64 assembly
./ulmt hello.ulmt --emit-asm

# Compile without executing
./ulmt hello.ulmt --no-run
```

## Global Installation

To run `ulmt` from anywhere:

### Option 1: Add to PATH
```bash
export PATH="/path/to/Ultimat:$PATH"
ulmt hello.ulmt
```

### Option 2: Create symlink
```bash
sudo ln -s /path/to/Ultimat/ulmt /usr/local/bin/ulmt
ulmt hello.ulmt
```

### Option 3: Install script (Linux)
```bash
sudo install -m 755 ulmt /usr/local/bin/
sudo install -m 755 ulmt.py /usr/local/bin/
```

## Verify Installation

```bash
$ ./ulmt hello.ulmt
Hello, ULMT!

$ ./ulmt --version
# (not yet implemented, but shows setup works)
```

## Troubleshooting

### "as: not found"
You need to install `binutils`:
```bash
# Termux
pkg install binutils

# Linux
sudo apt install binutils  # Debian/Ubuntu
sudo dnf install binutils  # Fedora/RHEL
```

### "python3: not found"
Install Python 3:
```bash
# Termux
pkg install python

# Linux
sudo apt install python3  # Debian/Ubuntu
sudo dnf install python3  # Fedora/RHEL
```

### "Exec format error"
This means you're trying to run an x86-64 binary on ARM64 (or vice versa).
ULMT v0.3.0 only generates ARM64 code. To develop on x86-64:
1. Use WSL2 with Ubuntu ARM64 image
2. Use Docker with ARM64 image
3. Cross-compile (advanced - not yet supported)

## Next Steps

1. Read `README.md` for language syntax
2. Check `COMPILER.md` for technical details
3. Explore example programs:
   - `hello.ulmt` - Simple output
   - `math.ulmt` - Arithmetic
   - `concat.ulmt` - String operations
   - `showcase.ulmt` - Combined features
4. Write your own ULMT programs!

## Contributing

To contribute improvements:
```bash
git clone https://github.com/Wilooper/Ultimat.git
cd Ultimat
git checkout -b feature/my-feature
# Make changes...
git add -A
git commit -m "Add new feature"
git push origin feature/my-feature
```

---

**ULMT — one syscall at a time, all the way down.**
