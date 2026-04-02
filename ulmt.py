#!/usr/bin/env python3
"""
ULMT Compiler v0.3.0
C-speed. Python-soul. Assembly heart.
Targets ARM64 (Android/Termux/Linux AArch64)
"""

import sys
import os
import subprocess
import re
import tempfile
from dataclasses import dataclass
from typing import List, Optional, Union
from enum import Enum

# ============================================================================
# LEXER
# ============================================================================

class TokenType(Enum):
    # Literals
    STRING = "STRING"
    INTEGER = "INTEGER"
    
    # Keywords
    PRINT = "PRINT"
    ASM = "ASM"
    LET = "LET"
    IF = "IF"
    ELSE = "ELSE"
    
    # Operators
    PLUS = "PLUS"
    MINUS = "MINUS"
    MUL = "MUL"
    DIV = "DIV"
    MOD = "MOD"
    EQ = "EQ"      # ==
    NEQ = "NEQ"     # !=
    LT = "LT"       # <
    LTE = "LTE"     # <=
    GT = "GT"       # >
    GTE = "GTE"     # >=
    
    # Delimiters
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    ASSIGN = "ASSIGN"
    NEWLINE = "NEWLINE"
    
    # Special
    IDENT = "IDENT"
    EOF = "EOF"

@dataclass
class Token:
    type: TokenType
    value: Union[str, int, None]
    line: int
    col: int

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []
        
    def error(self, msg: str):
        raise SyntaxError(f"Lexer error at line {self.line}, col {self.col}: {msg}")
    
    def peek(self, offset: int = 0) -> Optional[str]:
        p = self.pos + offset
        return self.source[p] if p < len(self.source) else None
    
    def advance(self) -> Optional[str]:
        if self.pos >= len(self.source):
            return None
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch
    
    def skip_whitespace(self):
        while self.peek() and self.peek() in ' \t\r':
            self.advance()
    
    def skip_comment(self):
        if self.peek() == '#':
            while self.peek() and self.peek() != '\n':
                self.advance()
    
    def read_string(self, quote: str) -> str:
        result = []
        self.advance()  # skip opening quote
        while True:
            ch = self.peek()
            if ch is None:
                self.error(f"Unterminated string")
            if ch == quote:
                self.advance()
                break
            if ch == '\\':
                self.advance()
                next_ch = self.advance()
                if next_ch == 'n':
                    result.append('\n')
                elif next_ch == 't':
                    result.append('\t')
                elif next_ch == 'r':
                    result.append('\r')
                elif next_ch == '\\':
                    result.append('\\')
                elif next_ch == quote:
                    result.append(quote)
                else:
                    result.append(next_ch)
            else:
                result.append(self.advance())
        return ''.join(result)
    
    def read_number(self) -> int:
        result = []
        while self.peek() and self.peek().isdigit():
            result.append(self.advance())
        return int(''.join(result))
    
    def read_ident(self) -> str:
        result = []
        while self.peek() and (self.peek().isalnum() or self.peek() in '_'):
            result.append(self.advance())
        return ''.join(result)
    
    def tokenize(self) -> List[Token]:
        keywords = {
            'print': TokenType.PRINT,
            'asm': TokenType.ASM,
            'let': TokenType.LET,
            'if': TokenType.IF,
            'else': TokenType.ELSE,
        }
        
        while self.pos < len(self.source):
            self.skip_whitespace()
            self.skip_comment()
            self.skip_whitespace()
            
            if self.pos >= len(self.source):
                break
            
            line, col = self.line, self.col
            ch = self.peek()
            
            if ch == '\n':
                self.advance()
                self.tokens.append(Token(TokenType.NEWLINE, None, line, col))
            elif ch == '"':
                string_val = self.read_string('"')
                self.tokens.append(Token(TokenType.STRING, string_val, line, col))
            elif ch == "'":
                string_val = self.read_string("'")
                self.tokens.append(Token(TokenType.STRING, string_val, line, col))
            elif ch.isdigit():
                num = self.read_number()
                self.tokens.append(Token(TokenType.INTEGER, num, line, col))
            elif ch.isalpha() or ch == '_':
                ident = self.read_ident()
                token_type = keywords.get(ident, TokenType.IDENT)
                self.tokens.append(Token(token_type, ident, line, col))
            elif ch == '+':
                self.advance()
                self.tokens.append(Token(TokenType.PLUS, '+', line, col))
            elif ch == '-':
                self.advance()
                self.tokens.append(Token(TokenType.MINUS, '-', line, col))
            elif ch == '*':
                self.advance()
                self.tokens.append(Token(TokenType.MUL, '*', line, col))
            elif ch == '/':
                self.advance()
                self.tokens.append(Token(TokenType.DIV, '/', line, col))
            elif ch == '%':
                self.advance()
                self.tokens.append(Token(TokenType.MOD, '%', line, col))
            elif ch == '(':
                self.advance()
                self.tokens.append(Token(TokenType.LPAREN, '(', line, col))
            elif ch == ')':
                self.advance()
                self.tokens.append(Token(TokenType.RPAREN, ')', line, col))
            elif ch == '{':
                self.advance()
                self.tokens.append(Token(TokenType.LBRACE, '{', line, col))
            elif ch == '}':
                self.advance()
                self.tokens.append(Token(TokenType.RBRACE, '}', line, col))
            elif ch == '=':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.EQ, '==', line, col))
                else:
                    self.tokens.append(Token(TokenType.ASSIGN, '=', line, col))
            elif ch == '!':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.NEQ, '!=', line, col))
                else:
                    self.error(f"Unexpected character: !")
            elif ch == '<':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.LTE, '<=', line, col))
                else:
                    self.tokens.append(Token(TokenType.LT, '<', line, col))
            elif ch == '>':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.GTE, '>=', line, col))
                else:
                    self.tokens.append(Token(TokenType.GT, '>', line, col))
            else:
                self.error(f"Unexpected character: {ch}")
        
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.col))
        return self.tokens


# ============================================================================
# AST NODES
# ============================================================================

@dataclass
class ASTNode:
    line: int
    col: int

@dataclass
class Program(ASTNode):
    statements: List['Statement']

@dataclass
class Statement(ASTNode):
    pass

@dataclass
class PrintStmt(Statement):
    expr: 'Expression'

@dataclass
class AsmStmt(Statement):
    code: str

@dataclass
class LetStmt(Statement):
    name: str
    expr: 'Expression'

@dataclass
class IfStmt(Statement):
    condition: 'Expression'
    then_body: List[Statement]
    else_body: Optional[List[Statement]]

@dataclass
class Expression(ASTNode):
    pass

@dataclass
class IntLiteral(Expression):
    value: int

@dataclass
class StringLiteral(Expression):
    value: str

@dataclass
class BinaryOp(Expression):
    left: Expression
    op: str
    right: Expression

@dataclass
class UnaryOp(Expression):
    op: str
    operand: Expression

@dataclass
class Variable(Expression):
    name: str


# ============================================================================
# PARSER
# ============================================================================

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
    
    def error(self, msg: str):
        token = self.current_token()
        raise SyntaxError(f"Parse error at line {token.line}, col {token.col}: {msg}")
    
    def current_token(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else self.tokens[-1]
    
    def peek(self, offset: int = 0) -> Token:
        p = self.pos + offset
        return self.tokens[p] if p < len(self.tokens) else self.tokens[-1]
    
    def advance(self) -> Token:
        token = self.current_token()
        if token.type != TokenType.EOF:
            self.pos += 1
        return token
    
    def expect(self, token_type: TokenType) -> Token:
        token = self.current_token()
        if token.type != token_type:
            self.error(f"Expected {token_type.value}, got {token.type.value}")
        return self.advance()
    
    def skip_newlines(self):
        while self.current_token().type == TokenType.NEWLINE:
            self.advance()
    
    def parse(self) -> Program:
        self.skip_newlines()
        statements = []
        
        while self.current_token().type != TokenType.EOF:
            self.skip_newlines()
            if self.current_token().type == TokenType.EOF:
                break
            statements.append(self.parse_statement())
            self.skip_newlines()
        
        return Program(line=1, col=1, statements=statements)
    
    def parse_statement(self) -> Statement:
        token = self.current_token()
        
        if token.type == TokenType.PRINT:
            return self.parse_print_stmt()
        elif token.type == TokenType.ASM:
            return self.parse_asm_stmt()
        elif token.type == TokenType.LET:
            return self.parse_let_stmt()
        elif token.type == TokenType.IF:
            return self.parse_if_stmt()
        else:
            self.error(f"Unexpected statement: {token.type.value}")
    
    def parse_print_stmt(self) -> PrintStmt:
        line, col = self.current_token().line, self.current_token().col
        self.expect(TokenType.PRINT)
        expr = self.parse_expression()
        return PrintStmt(line=line, col=col, expr=expr)
    
    def parse_asm_stmt(self) -> AsmStmt:
        line, col = self.current_token().line, self.current_token().col
        self.expect(TokenType.ASM)
        self.expect(TokenType.LBRACE)
        
        # Collect everything until closing brace as raw assembly
        asm_lines = []
        while self.current_token().type != TokenType.RBRACE:
            if self.current_token().type == TokenType.EOF:
                self.error("Unterminated asm block")
            # Read raw tokens as assembly
            token = self.current_token()
            if token.type == TokenType.NEWLINE:
                asm_lines.append('\n')
            else:
                asm_lines.append(str(token.value) if token.value else token.type.value)
            self.advance()
        
        self.expect(TokenType.RBRACE)
        code = ''.join(asm_lines).strip()
        return AsmStmt(line=line, col=col, code=code)
    
    def parse_let_stmt(self) -> LetStmt:
        line, col = self.current_token().line, self.current_token().col
        self.expect(TokenType.LET)
        name_token = self.expect(TokenType.IDENT)
        self.expect(TokenType.ASSIGN)
        expr = self.parse_expression()
        return LetStmt(line=line, col=col, name=name_token.value, expr=expr)
    
    def parse_if_stmt(self) -> IfStmt:
        line, col = self.current_token().line, self.current_token().col
        self.expect(TokenType.IF)
        condition = self.parse_expression()
        self.expect(TokenType.LBRACE)
        self.skip_newlines()
        
        then_body = []
        while self.current_token().type != TokenType.RBRACE:
            then_body.append(self.parse_statement())
            self.skip_newlines()
        
        self.expect(TokenType.RBRACE)
        self.skip_newlines()
        
        else_body = None
        if self.current_token().type == TokenType.ELSE:
            self.advance()
            self.expect(TokenType.LBRACE)
            self.skip_newlines()
            else_body = []
            while self.current_token().type != TokenType.RBRACE:
                else_body.append(self.parse_statement())
                self.skip_newlines()
            self.expect(TokenType.RBRACE)
        
        return IfStmt(line=line, col=col, condition=condition, then_body=then_body, else_body=else_body)
    
    def parse_expression(self) -> Expression:
        return self.parse_comparison()
    
    def parse_comparison(self) -> Expression:
        left = self.parse_additive()
        
        while self.current_token().type in [TokenType.EQ, TokenType.NEQ, TokenType.LT, TokenType.LTE, TokenType.GT, TokenType.GTE]:
            token = self.advance()
            right = self.parse_additive()
            left = BinaryOp(line=token.line, col=token.col, left=left, op=token.value, right=right)
        
        return left
    
    def parse_additive(self) -> Expression:
        left = self.parse_multiplicative()
        
        while self.current_token().type in [TokenType.PLUS, TokenType.MINUS]:
            token = self.advance()
            right = self.parse_multiplicative()
            left = BinaryOp(line=token.line, col=token.col, left=left, op=token.value, right=right)
        
        return left
    
    def parse_multiplicative(self) -> Expression:
        left = self.parse_unary()
        
        while self.current_token().type in [TokenType.MUL, TokenType.DIV, TokenType.MOD]:
            token = self.advance()
            right = self.parse_unary()
            left = BinaryOp(line=token.line, col=token.col, left=left, op=token.value, right=right)
        
        return left
    
    def parse_unary(self) -> Expression:
        if self.current_token().type in [TokenType.MINUS, TokenType.PLUS]:
            token = self.advance()
            operand = self.parse_unary()
            return UnaryOp(line=token.line, col=token.col, op=token.value, operand=operand)
        
        return self.parse_primary()
    
    def parse_primary(self) -> Expression:
        token = self.current_token()
        
        if token.type == TokenType.INTEGER:
            self.advance()
            return IntLiteral(line=token.line, col=token.col, value=token.value)
        elif token.type == TokenType.STRING:
            self.advance()
            return StringLiteral(line=token.line, col=token.col, value=token.value)
        elif token.type == TokenType.IDENT:
            self.advance()
            return Variable(line=token.line, col=token.col, name=token.value)
        elif token.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr
        else:
            self.error(f"Unexpected token in expression: {token.type.value}")


# ============================================================================
# CONSTANT FOLDING
# ============================================================================

class ConstantFolder:
    def fold(self, node: ASTNode) -> ASTNode:
        if isinstance(node, Program):
            return Program(
                line=node.line,
                col=node.col,
                statements=[self.fold(stmt) for stmt in node.statements]
            )
        elif isinstance(node, PrintStmt):
            return PrintStmt(
                line=node.line,
                col=node.col,
                expr=self.fold(node.expr)
            )
        elif isinstance(node, BinaryOp):
            left = self.fold(node.left)
            right = self.fold(node.right)
            
            # Fold if both sides are constants
            if isinstance(left, IntLiteral) and isinstance(right, IntLiteral):
                if node.op == '+':
                    return IntLiteral(line=node.line, col=node.col, value=left.value + right.value)
                elif node.op == '-':
                    return IntLiteral(line=node.line, col=node.col, value=left.value - right.value)
                elif node.op == '*':
                    return IntLiteral(line=node.line, col=node.col, value=left.value * right.value)
                elif node.op == '/':
                    return IntLiteral(line=node.line, col=node.col, value=left.value // right.value)
                elif node.op == '%':
                    return IntLiteral(line=node.line, col=node.col, value=left.value % right.value)
                elif node.op == '==':
                    return IntLiteral(line=node.line, col=node.col, value=1 if left.value == right.value else 0)
                elif node.op == '!=':
                    return IntLiteral(line=node.line, col=node.col, value=1 if left.value != right.value else 0)
                elif node.op == '<':
                    return IntLiteral(line=node.line, col=node.col, value=1 if left.value < right.value else 0)
                elif node.op == '<=':
                    return IntLiteral(line=node.line, col=node.col, value=1 if left.value <= right.value else 0)
                elif node.op == '>':
                    return IntLiteral(line=node.line, col=node.col, value=1 if left.value > right.value else 0)
                elif node.op == '>=':
                    return IntLiteral(line=node.line, col=node.col, value=1 if left.value >= right.value else 0)
            
            # String concatenation
            if node.op == '+' and isinstance(left, StringLiteral) and isinstance(right, StringLiteral):
                return StringLiteral(line=node.line, col=node.col, value=left.value + right.value)
            
            return BinaryOp(line=node.line, col=node.col, left=left, op=node.op, right=right)
        elif isinstance(node, UnaryOp):
            operand = self.fold(node.operand)
            if node.op == '-' and isinstance(operand, IntLiteral):
                return IntLiteral(line=node.line, col=node.col, value=-operand.value)
            return UnaryOp(line=node.line, col=node.col, op=node.op, operand=operand)
        elif isinstance(node, LetStmt):
            return LetStmt(
                line=node.line,
                col=node.col,
                name=node.name,
                expr=self.fold(node.expr)
            )
        elif isinstance(node, IfStmt):
            return IfStmt(
                line=node.line,
                col=node.col,
                condition=self.fold(node.condition),
                then_body=[self.fold(stmt) for stmt in node.then_body],
                else_body=[self.fold(stmt) for stmt in node.else_body] if node.else_body else None
            )
        elif isinstance(node, AsmStmt):
            return node
        else:
            return node


# ============================================================================
# CODE GENERATOR (ARM64)
# ============================================================================

class CodeGen:
    def __init__(self):
        self.code: List[str] = []
        self.data: List[str] = []
        self.string_counter = 0
        self.string_map = {}  # value -> (label, length)
        self.temp_counter = 0
    
    def generate(self, ast: Program) -> str:
        # Header
        self.code.append(".arch armv8-a")
        self.code.append(".text")
        self.code.append(".global _start")
        self.code.append("_start:")
        
        # Generate statements
        for stmt in ast.statements:
            self.generate_statement(stmt)
        
        # Exit syscall
        self.code.append("    mov x8, #93    // sys_exit")
        self.code.append("    mov x0, #0     // exit code 0")
        self.code.append("    svc #0")
        
        # Data section
        if self.data:
            self.code.append("")
            self.code.append(".data")
            self.code.extend(self.data)
        
        return '\n'.join(self.code)
    
    def generate_statement(self, stmt: Statement):
        if isinstance(stmt, PrintStmt):
            self.generate_print(stmt.expr)
        elif isinstance(stmt, AsmStmt):
            self.generate_asm(stmt.code)
        elif isinstance(stmt, LetStmt):
            pass  # TODO: variable support
        elif isinstance(stmt, IfStmt):
            pass  # TODO: if/else support
    
    def generate_print(self, expr: Expression):
        if isinstance(expr, StringLiteral):
            self.generate_print_string(expr.value)
        elif isinstance(expr, IntLiteral):
            self.generate_print_int(expr.value)
        elif isinstance(expr, BinaryOp):
            # Evaluate and print
            self.generate_print_int(self.evaluate_constant_expr(expr))
        else:
            # For now, assume it evaluates to something printable
            pass
    
    def generate_print_string(self, s: str):
        s_with_newline = s + '\n'
        
        if s_with_newline in self.string_map:
            label, length = self.string_map[s_with_newline]
        else:
            label = f"_s{self.string_counter}"
            self.string_counter += 1
            length = len(s_with_newline)
            self.string_map[s_with_newline] = (label, length)
            # Add to data section
            escaped = s_with_newline.replace('\\', '\\\\').replace('"', '\\"')
            self.data.append(f'{label}: .ascii "{escaped}"')
            self.data.append(f'{label}_len = . - {label}')
        
        self.code.append(f"    // print string")
        self.code.append(f"    mov x8, #64           // sys_write")
        self.code.append(f"    mov x0, #1            // stdout")
        self.code.append(f"    ldr x1, ={label}      // string pointer")
        self.code.append(f"    ldr x2, ={label}_len  // string length")
        self.code.append(f"    svc #0")
    
    def generate_print_int(self, value: int):
        # Convert integer to string at compile time
        s = str(value) + '\n'
        self.generate_print_string(s)
    
    def generate_asm(self, code: str):
        for line in code.split('\n'):
            line = line.strip()
            if line:
                self.code.append(f"    {line}")
    
    def evaluate_constant_expr(self, expr: Expression) -> int:
        """Evaluate a constant expression to an integer."""
        if isinstance(expr, IntLiteral):
            return expr.value
        elif isinstance(expr, BinaryOp):
            left = self.evaluate_constant_expr(expr.left)
            right = self.evaluate_constant_expr(expr.right)
            if expr.op == '+':
                return left + right
            elif expr.op == '-':
                return left - right
            elif expr.op == '*':
                return left * right
            elif expr.op == '/':
                return left // right
            elif expr.op == '%':
                return left % right
        elif isinstance(expr, UnaryOp):
            operand = self.evaluate_constant_expr(expr.operand)
            if expr.op == '-':
                return -operand
            elif expr.op == '+':
                return operand
        raise ValueError(f"Cannot evaluate constant expression: {expr}")


# ============================================================================
# MAIN COMPILER
# ============================================================================

class ULMTCompiler:
    def __init__(self, source_file: str):
        self.source_file = source_file
        self.base_name = os.path.splitext(os.path.basename(source_file))[0]
    
    def compile(self, emit_asm: bool = False, no_run: bool = False) -> Optional[str]:
        """Compile ULMT file to ARM64 binary."""
        
        # Read source
        with open(self.source_file, 'r') as f:
            source = f.read()
        
        # Lexical analysis
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        # Parsing
        parser = Parser(tokens)
        ast = parser.parse()
        
        # Optimization: constant folding
        folder = ConstantFolder()
        ast = folder.fold(ast)
        
        # Code generation
        codegen = CodeGen()
        asm_code = codegen.generate(ast)
        
        if emit_asm:
            print(asm_code)
            return None
        
        # Write assembly to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.s', delete=False) as f:
            asm_file = f.name
            f.write(asm_code)
        
        try:
            # Assemble
            obj_file = f"{self.base_name}.o"
            result = subprocess.run(['as', '-o', obj_file, asm_file], 
                                   capture_output=True, text=True)
            if result.returncode != 0:
                print("Assembler error:")
                print(result.stderr)
                return None
            
            # Link
            bin_file = self.base_name
            result = subprocess.run(['ld', '-o', bin_file, obj_file],
                                   capture_output=True, text=True)
            if result.returncode != 0:
                print("Linker error:")
                print(result.stderr)
                return None
            
            # Make executable
            os.chmod(bin_file, 0o755)
            
            if not no_run:
                # Run the binary
                result = subprocess.run([f'./{bin_file}'], capture_output=True, text=True)
                print(result.stdout, end='')
                if result.stderr:
                    print(result.stderr, file=sys.stderr, end='')
                return result.stdout
            
            return bin_file
        
        finally:
            # Cleanup
            if os.path.exists(asm_file):
                os.remove(asm_file)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 ulmt.py <file.ulmt> [--emit-asm] [--no-run]")
        sys.exit(1)
    
    source_file = sys.argv[1]
    emit_asm = '--emit-asm' in sys.argv
    no_run = '--no-run' in sys.argv
    
    if not os.path.exists(source_file):
        print(f"Error: File not found: {source_file}")
        sys.exit(1)
    
    compiler = ULMTCompiler(source_file)
    try:
        compiler.compile(emit_asm=emit_asm, no_run=no_run)
    except Exception as e:
        print(f"Compilation error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
