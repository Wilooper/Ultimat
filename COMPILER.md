# ULMT Compiler - Implementation Guide

## Quick Start

```bash
# Run a ULMT program (compiles and executes)
python3 ulmt.py hello.ulmt
# OR use the wrapper
./ulmt hello.ulmt

# See generated ARM64 assembly
python3 ulmt.py hello.ulmt --emit-asm

# Compile without running
python3 ulmt.py hello.ulmt --no-run
```

## Architecture

The ULMT compiler consists of 5 major components:

### 1. Lexer (`Lexer` class)
- Tokenizes ULMT source code into a token stream
- Handles strings, integers, keywords, operators, comments
- Tracks line/column for error reporting
- **Key Methods:**
  - `tokenize()`: Returns list of `Token` objects
  - `read_string()`: Handles escape sequences
  - `read_number()`: Parses integers
  - `read_ident()`: Parses identifiers and keywords

### 2. Parser (`Parser` class)
- Builds Abstract Syntax Tree (AST) from tokens
- Implements recursive descent parsing
- Handles operator precedence correctly
- **Key Methods:**
  - `parse()`: Top-level entry point
  - `parse_statement()`: Parses print, asm, let, if statements
  - `parse_expression()`: Recursive expression parsing with precedence
  - `parse_primary()`: Terminal expressions (literals, variables)

### 3. Constant Folding (`ConstantFolder` class)
- Optimization pass: evaluates constant expressions at compile time
- Eliminates arithmetic computations from generated code
- **Example:** `print 10 + 5 * 2` → `print 20` (zero runtime cost)
- **Key Method:**
  - `fold()`: Recursively processes and optimizes AST

### 4. Code Generator (`CodeGen` class)
- Generates ARM64 assembly code from AST
- Manages string literals in `.data` section
- Handles syscalls for output and exit
- **Key Methods:**
  - `generate()`: Top-level code generation
  - `generate_print_string()`: Emits sys_write syscall
  - `generate_print_int()`: Converts int to string and prints
  - `evaluate_constant_expr()`: Evaluates constant expressions

### 5. Compiler Driver (`ULMTCompiler` class)
- Orchestrates entire pipeline: lex → parse → fold → codegen → assemble → link
- Manages temporary files
- Invokes GNU `as` (assembler) and `ld` (linker)
- **Key Methods:**
  - `compile()`: Main compilation entry point

## Supported Features (v0.3.0)

### Print Statements
```ulmt
print "Hello, World!"      # String literal
print 42                   # Integer literal
print 10 + 5 * 2          # Arithmetic (evaluated at compile time)
print "Hello" + " World"  # String concatenation
```

### Arithmetic Operators
- `+` (addition)
- `-` (subtraction)
- `*` (multiplication)
- `/` (integer division)
- `%` (modulo)

### Operator Precedence (highest to lowest)
1. Unary: `-x`, `+x`
2. Multiplicative: `*`, `/`, `%`
3. Additive: `+`, `-`
4. Comparison: `==`, `!=`, `<`, `<=`, `>`, `>=`

### Inline Assembly
```ulmt
asm {
    mov x8, #64
    mov x0, #1
    svc #0
}
```

### Comments
```ulmt
# This is a comment
```

## ARM64 Syscall Details

The generated code uses ARM64 Linux syscalls:

| Register | Purpose |
|----------|---------|
| `x8`     | Syscall number |
| `x0`     | First argument (file descriptor for write, exit code for exit) |
| `x1`     | Second argument (buffer address) |
| `x2`     | Third argument (byte count) |
| `svc #0` | Trigger syscall |

**Syscalls used:**
- `#64` - `sys_write` (output)
- `#93` - `sys_exit` (program termination)

## Generated Code Example

**Input (`hello.ulmt`):**
```ulmt
print "Hi"
```

**Generated Assembly:**
```asm
.arch armv8-a
.text
.global _start
_start:
    mov x8, #64           // sys_write
    mov x0, #1            // stdout
    ldr x1, =_s0          // string pointer
    ldr x2, =_s0_len      // string length
    svc #0
    
    mov x8, #93           // sys_exit
    mov x0, #0            // exit code 0
    svc #0

.data
_s0: .ascii "Hi\n"
_s0_len = . - _s0
```

## AST Node Types

```python
Program(statements: List[Statement])
  ├── PrintStmt(expr: Expression)
  ├── AsmStmt(code: str)
  ├── LetStmt(name: str, expr: Expression)
  └── IfStmt(condition: Expression, then_body: List[Statement], else_body: Optional[List[Statement]])

Expression types:
  ├── IntLiteral(value: int)
  ├── StringLiteral(value: str)
  ├── BinaryOp(left: Expression, op: str, right: Expression)
  ├── UnaryOp(op: str, operand: Expression)
  └── Variable(name: str)
```

## Extending the Compiler

### Adding a New Statement Type
1. Add AST node class (inherit from `Statement`)
2. Add parsing logic in `Parser.parse_statement()`
3. Add constant folding in `ConstantFolder.fold()`
4. Add code generation in `CodeGen.generate_statement()`

### Adding a New Operator
1. Add `TokenType` in `TokenType` enum
2. Add lexing logic in `Lexer.tokenize()`
3. Add parsing in appropriate `Parser.parse_*()` method
4. Add constant folding in `ConstantFolder.fold()`
5. Add code generation in `CodeGen`

### Adding Variable Support (v0.4)
```ulmt
let x = 10
print x
print x + 5
```
Requires:
- Symbol table for variable storage
- Register allocation for local variables
- Stack frame management (if needed)

### Adding Control Flow (v0.5+)
```ulmt
if x > 5 {
    print "greater"
} else {
    print "less"
}
```
Requires:
- Label generation for jumps
- Condition evaluation to ARM64 flags
- Conditional branch instructions

## Performance Notes

- **Constant folding**: Arithmetic on constants is done at compile time, not runtime
- **String deduplication**: Identical strings reuse the same label in `.data`
- **No heap allocations**: All generated binaries are statically linked
- **Native execution**: Compiled to ARM64 machine code, no VM overhead

## Error Handling

Errors are caught at each stage:
- **Lexer**: Unterminated strings, unexpected characters
- **Parser**: Syntax errors, unexpected tokens, mismatched braces
- **Compiler**: Missing source file, assembler/linker failures

All errors include line and column information for debugging.

## File Organization

```
Ultimat/
├── ulmt.py          # Main compiler (Python)
├── ulmt             # Wrapper script (Bash)
├── README.md        # User documentation
├── COMPILER.md      # This file (implementation guide)
├── hello.ulmt       # Example: hello world
├── math.ulmt        # Example: arithmetic
├── concat.ulmt      # Example: string concatenation
└── .git/            # Version control
```

## Next Steps (Roadmap)

- **v0.4**: Variables with `let x = 10`
- **v0.5**: If/else conditionals
- **v0.6**: While loops
- **v0.7**: Function definitions
- **v0.8**: Type system (int, str, bool)
- **Phase 2**: Self-hosting compiler (written in ULMT)
