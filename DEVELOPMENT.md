# ULMT Development Guide

This guide helps developers extend the ULMT compiler.

## Architecture Overview

The compiler follows a classic pipeline:

```
Source Code → Lexer → Parser → Optimizer → CodeGen → Assembler → Linker → Binary
```

Each stage is independent and can be modified without affecting others.

## File Organization

```python
ulmt.py
├── TokenType (enum)        # All token types
├── Token (dataclass)       # Single token with location
├── Lexer                   # Tokenization
│   └── tokenize()
├── ASTNode (base)          # Base class for AST
├── Statement/Expression    # AST node types
├── Parser                  # Builds AST
│   └── parse()
├── ConstantFolder          # Optimization pass
│   └── fold()
├── CodeGen                 # ARM64 generation
│   └── generate()
├── ULMTCompiler            # Main driver
│   └── compile()
└── main()                  # CLI entry point
```

## Adding a New Feature

### Example: Adding `while` loops (v0.6)

#### 1. Add AST Node

```python
@dataclass
class WhileStmt(Statement):
    condition: Expression
    body: List[Statement]
```

#### 2. Add Token Type

```python
class TokenType(Enum):
    WHILE = "WHILE"
```

#### 3. Update Lexer

In `Lexer.tokenize()`, add to keywords:
```python
keywords = {
    'while': TokenType.WHILE,
    # ... other keywords
}
```

#### 4. Update Parser

Add parsing method:
```python
def parse_while_stmt(self) -> WhileStmt:
    line, col = self.current_token().line, self.current_token().col
    self.expect(TokenType.WHILE)
    condition = self.parse_expression()
    self.expect(TokenType.LBRACE)
    self.skip_newlines()
    body = []
    while self.current_token().type != TokenType.RBRACE:
        body.append(self.parse_statement())
        self.skip_newlines()
    self.expect(TokenType.RBRACE)
    return WhileStmt(line=line, col=col, condition=condition, body=body)
```

Add to `parse_statement()`:
```python
elif token.type == TokenType.WHILE:
    return self.parse_while_stmt()
```

#### 5. Update Constant Folder

```python
elif isinstance(node, WhileStmt):
    return WhileStmt(
        line=node.line,
        col=node.col,
        condition=self.fold(node.condition),
        body=[self.fold(stmt) for stmt in node.body]
    )
```

#### 6. Update Code Generator

Add to `CodeGen`:
```python
def generate_while(self, stmt: WhileStmt):
    loop_label = f"_loop_{self.temp_counter}"
    exit_label = f"_exit_{self.temp_counter}"
    self.temp_counter += 1
    
    self.code.append(f"{loop_label}:")
    # Generate condition check
    # Jump to exit_label if condition false
    # Generate loop body
    # Jump back to loop_label
    self.code.append(f"{exit_label}:")
```

Add to `generate_statement()`:
```python
elif isinstance(stmt, WhileStmt):
    self.generate_while(stmt)
```

#### 7. Test

Create `while_loop.ulmt`:
```ulmt
let i = 0
while i < 5 {
    print i
}
```

Run: `./ulmt while_loop.ulmt`

---

## Key Concepts

### Register Allocation

For v0.4+ (variables), you need to assign registers to variables:
```python
# x0-x7: Scratch (caller-saved)
# x8-x15: Scratch (caller-saved)
# x16-x17: Temporary
# x18-x28: Callee-saved
# x29: Frame pointer
# x30: Link register
# x31: Stack pointer (sp)
```

For simple local variables, use x0-x7 and push/pop as needed.

### Stack Frame

For functions (v0.7), you'll need:
```asm
_function:
    stp x29, x30, [sp, #-16]!   // Save frame pointer and return address
    mov x29, sp                  // Set up frame pointer
    
    // Function body
    
    ldp x29, x30, [sp], #16      // Restore and return
    ret
```

### Label Generation

Keep a counter for unique labels:
```python
self.temp_counter = 0

def new_label(self, prefix: str) -> str:
    label = f"_{prefix}_{self.temp_counter}"
    self.temp_counter += 1
    return label
```

### String Deduplication

Current implementation deduplicates strings:
```python
if s_with_newline in self.string_map:
    label, length = self.string_map[s_with_newline]
else:
    # Create new label
```

This saves space in generated binaries.

---

## Testing Strategy

### Unit Tests

For each feature, create a `.ulmt` file:

```ulmt
# variables.ulmt
let x = 10
let y = x + 5
print y  # Should print 15
```

### Integration Tests

Test interactions between features:
```ulmt
let i = 0
while i < 3 {
    if i > 0 {
        print i
    }
}
```

### Performance Tests

Track compilation time and binary size:
```bash
time ./ulmt large_program.ulmt --no-run
ls -lh large_program
```

---

## Common Pitfalls

1. **Forgetting to fold AST** - Constants won't be optimized
2. **Not tracking label locations** - Jumps will go wrong
3. **Incorrect ARM64 calling conventions** - Crashes or hangs
4. **Memory management** - Stack overflow on deep recursion
5. **Not testing edge cases** - `0`, negative numbers, empty strings

---

## Debug Tips

### Emit Assembly

Use `--emit-asm` to see generated code:
```bash
./ulmt program.ulmt --emit-asm
```

### Disassemble Binary

```bash
objdump -d program
# or on Android/Termux
arm64-linux-gnu-objdump -d program
```

### Run with Strace

```bash
strace ./program
# Shows all syscalls made
```

### Add Debug Output

```python
print(f"DEBUG: Folding {node}", file=sys.stderr)
```

---

## Version Increment Strategy

- **Patch (0.3.1)**: Bug fixes, minor improvements
- **Minor (0.4.0)**: New language feature
- **Major (1.0.0)**: API breaking changes or self-hosting

Current: v0.3.0 → Next: v0.4.0 (variables)

---

## Performance Optimization Ideas

1. **Inline constants** - Don't use labels for short strings
2. **Dead code elimination** - Remove unreachable code
3. **Register coalescing** - Reuse registers more efficiently
4. **Instruction scheduling** - Order instructions for pipeline
5. **Loop unrolling** - For fixed-count loops

---

## Self-Hosting Roadmap (Phase 2)

To bootstrap the compiler in ULMT itself:

1. **Stage 1** (now): Python compiler → ARM64 binary
2. **Stage 2**: Rewrite compiler in ULMT
3. **Stage 3**: Compile with itself (ulmt.ulmt → ulmt)
4. **Stage 4**: Drop Python, just use assembly toolchain

This is a major milestone proving ULMT is production-ready.

---

**Happy coding! One syscall at a time.**
