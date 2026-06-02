from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Any


class TomatoParserError(Exception):
    """Raised when Tomato source cannot be tokenized or parsed."""


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    line: int
    column: int


KEYWORDS = {
    "assign",
    "print",
    "input",
    "into",
    "where",
    "do",
    "loop",
    "function",
    "return",
    "call",
    "import",
    "export",
    "var",
    "list",
    "true",
    "false",
    "null",
}

TOKEN_PATTERN = re.compile(
    r"""
    (?P<COMMENT>//[^\n]*)
    |(?P<NUMBER>\d+(?:\.\d+)?)
    |(?P<STRING>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')
    |(?P<IDENT>(?:[A-Za-z_]|[\U0001F300-\U0001FAFF])(?:[A-Za-z0-9_]|[\U0001F300-\U0001FAFF\u200D\uFE0F])*)
    |(?P<SYMBOL>==|!=|<=|>=|[+\-*/<>=(),;{}\[\]])
    |(?P<NEWLINE>\n)
    |(?P<SKIP>[ \t\r]+)
    |(?P<MISMATCH>.)
    """,
    re.VERBOSE,
)


class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        line = 1
        line_start = 0

        for match in TOKEN_PATTERN.finditer(self.source):
            kind = match.lastgroup
            value = match.group()
            column = match.start() - line_start + 1

            if kind in {"SKIP", "COMMENT"}:
                continue
            if kind == "NEWLINE":
                line += 1
                line_start = match.end()
                continue
            if kind == "MISMATCH":
                raise TomatoParserError(
                    f"Unexpected character {value!r} at line {line}, column {column}"
                )

            token_kind = kind
            if kind == "IDENT" and value in KEYWORDS:
                token_kind = "KEYWORD"

            tokens.append(Token(token_kind, value, line, column))

        tokens.append(Token("EOF", "", line, 1))
        return tokens


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    @property
    def current(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        token = self.current
        if token.kind != "EOF":
            self.pos += 1
        return token

    def parse_program(self) -> dict[str, Any]:
        statements: list[dict[str, Any]] = []
        while self.current.kind != "EOF":
            statements.append(self.parse_statement())
        return {"type": "Program", "body": statements}

    def parse_statement(self) -> dict[str, Any]:
        if self._match_keyword("assign"):
            return self._parse_assign()
        if self._match_keyword("var"):
            return self._parse_var()
        if self._match_keyword("print"):
            return self._parse_print()
        if self._match_keyword("input"):
            return self._parse_input()
        if self._match_keyword("where"):
            return self._parse_where()
        if self._match_keyword("loop"):
            return self._parse_loop()
        if self._match_keyword("function"):
            return self._parse_function_decl(exported=False)
        if self._match_keyword("return"):
            return self._parse_return()
        if self._match_keyword("call"):
            return self._parse_call_stmt()
        if self._match_keyword("import"):
            return self._parse_import()
        if self._match_keyword("export"):
            return self._parse_export()

        token = self.current
        raise TomatoParserError(
            f"Unexpected token {token.value!r} at line {token.line}, column {token.column}"
        )

    def _parse_assign(self) -> dict[str, Any]:
        target = self.parse_expression(stop_at={"="})
        self._expect_value("=")
        value = self.parse_expression(stop_at={";"})
        self._expect_value(";")
        return {"type": "AssignStatement", "target": target, "value": value}

    def _parse_var(self) -> dict[str, Any]:
        name = self._expect_kind("IDENT").value
        self._expect_value(";")
        return {"type": "VarDeclaration", "name": name}

    def _parse_print(self) -> dict[str, Any]:
        values: list[dict[str, Any]] = []
        while not self._check_value(";"):
            values.append(self.parse_expression(stop_at={",", ";"}))
            self._match_value(",")
            if self._check_value(";"):
                break
        if not values:
            raise TomatoParserError("print requires at least one expression")
        self._expect_value(";")
        return {"type": "PrintStatement", "values": values}

    def _parse_input(self) -> dict[str, Any]:
        prompt = self.parse_expression(stop_at={"into"})
        self._expect_keyword("into")
        name = self._expect_kind("IDENT").value
        self._expect_value(";")
        return {"type": "InputStatement", "prompt": prompt, "name": name}

    def _parse_where(self) -> dict[str, Any]:
        condition = self.parse_expression(stop_at={"do"})
        self._expect_keyword("do")
        body = self._parse_block()
        return {"type": "WhereStatement", "condition": condition, "body": body}

    def _parse_loop(self) -> dict[str, Any]:
        count_expr = self.parse_expression(stop_at={"do"})
        self._expect_keyword("do")
        body = self._parse_block()
        return {"type": "LoopStatement", "count": count_expr, "body": body}

    def _parse_function_decl(self, exported: bool) -> dict[str, Any]:
        name = self._expect_kind("IDENT").value
        self._expect_value("(")
        params: list[str] = []
        if not self._check_value(")"):
            while True:
                params.append(self._expect_kind("IDENT").value)
                if self._match_value(","):
                    continue
                break
        self._expect_value(")")
        body = self._parse_block()
        return {
            "type": "FunctionDeclaration",
            "name": name,
            "params": params,
            "body": body,
            "exported": exported,
        }

    def _parse_return(self) -> dict[str, Any]:
        value = None
        if not self._check_value(";"):
            value = self.parse_expression(stop_at={";"})
        self._expect_value(";")
        return {"type": "ReturnStatement", "value": value}

    def _parse_call_stmt(self) -> dict[str, Any]:
        call_expr = self._parse_call_expression()
        self._expect_value(";")
        return {"type": "CallStatement", "call": call_expr}

    def _parse_import(self) -> dict[str, Any]:
        path_token = self._expect_kind("STRING")
        self._expect_value(";")
        return {"type": "ImportStatement", "path": _decode_string(path_token.value)}

    def _parse_export(self) -> dict[str, Any]:
        self._expect_keyword("function")
        return self._parse_function_decl(exported=True)

    def _parse_block(self) -> dict[str, Any]:
        self._expect_value("{")
        statements: list[dict[str, Any]] = []
        while not self._check_value("}"):
            if self.current.kind == "EOF":
                raise TomatoParserError("Unterminated block")
            statements.append(self.parse_statement())
        self._expect_value("}")
        return {"type": "BlockStatement", "body": statements}

    def parse_expression(self, stop_at: set[str] | None = None) -> dict[str, Any]:
        return self._parse_equality(stop_at)

    def _parse_equality(self, stop_at: set[str] | None) -> dict[str, Any]:
        expr = self._parse_comparison(stop_at)
        while self._check_binary({"==", "!="}, stop_at):
            operator = self.advance().value
            right = self._parse_comparison(stop_at)
            expr = {"type": "BinaryExpression", "operator": operator, "left": expr, "right": right}
        return expr

    def _parse_comparison(self, stop_at: set[str] | None) -> dict[str, Any]:
        expr = self._parse_term(stop_at)
        while self._check_binary({"<", ">", "<=", ">="}, stop_at):
            operator = self.advance().value
            right = self._parse_term(stop_at)
            expr = {"type": "BinaryExpression", "operator": operator, "left": expr, "right": right}
        return expr

    def _parse_term(self, stop_at: set[str] | None) -> dict[str, Any]:
        expr = self._parse_factor(stop_at)
        while self._check_binary({"+", "-"}, stop_at):
            operator = self.advance().value
            right = self._parse_factor(stop_at)
            expr = {"type": "BinaryExpression", "operator": operator, "left": expr, "right": right}
        return expr

    def _parse_factor(self, stop_at: set[str] | None) -> dict[str, Any]:
        expr = self._parse_unary(stop_at)
        while self._check_binary({"*", "/"}, stop_at):
            operator = self.advance().value
            right = self._parse_unary(stop_at)
            expr = {"type": "BinaryExpression", "operator": operator, "left": expr, "right": right}
        return expr

    def _parse_unary(self, stop_at: set[str] | None) -> dict[str, Any]:
        if self._check_value("-") and not self._is_stopped(stop_at):
            operator = self.advance().value
            right = self._parse_unary(stop_at)
            return {"type": "UnaryExpression", "operator": operator, "operand": right}
        return self._parse_primary(stop_at)

    def _parse_primary(self, stop_at: set[str] | None) -> dict[str, Any]:
        if self._is_stopped(stop_at):
            token = self.current
            raise TomatoParserError(
                f"Expected expression before {token.value!r} at line {token.line}, column {token.column}"
            )

        if self._match_kind("NUMBER"):
            token = self.tokens[self.pos - 1]
            value = float(token.value) if "." in token.value else int(token.value)
            return {"type": "NumberLiteral", "value": value}

        if self._match_kind("STRING"):
            token = self.tokens[self.pos - 1]
            return {"type": "StringLiteral", "value": _decode_string(token.value)}

        if self._match_keyword("list"):
            self._expect_value("(")
            elements: list[dict[str, Any]] = []
            if not self._check_value(")"):
                while True:
                    elements.append(self.parse_expression(stop_at={",", ")"}))
                    if self._match_value(","):
                        continue
                    break
            self._expect_value(")")
            return {"type": "ListLiteral", "elements": elements}

        if self._match_keyword("true"):
            return {"type": "BooleanLiteral", "value": True}
        if self._match_keyword("false"):
            return {"type": "BooleanLiteral", "value": False}
        if self._match_keyword("null"):
            return {"type": "NullLiteral", "value": None}

        if self._match_kind("IDENT"):
            ident = self.tokens[self.pos - 1]
            if self._check_value("("):
                self.pos -= 1
                return self._parse_call_expression()
            return {"type": "Identifier", "name": ident.value}

        if self._match_value("["):
            elements: list[dict[str, Any]] = []
            if not self._check_value("]"):
                while True:
                    elements.append(self.parse_expression(stop_at={",", "]"}))
                    if self._match_value(","):
                        continue
                    break
            self._expect_value("]")
            return {"type": "ListLiteral", "elements": elements}

        if self._match_value("("):
            expr = self.parse_expression(stop_at={")"})
            self._expect_value(")")
            return {"type": "GroupingExpression", "expression": expr}

        token = self.current
        raise TomatoParserError(
            f"Unexpected token {token.value!r} in expression at line {token.line}, column {token.column}"
        )

    def _parse_call_expression(self) -> dict[str, Any]:
        callee = self._expect_kind("IDENT").value
        self._expect_value("(")
        args: list[dict[str, Any]] = []
        if not self._check_value(")"):
            while True:
                args.append(self.parse_expression(stop_at={",", ")"}))
                if self._match_value(","):
                    continue
                break
        self._expect_value(")")
        return {"type": "CallExpression", "callee": callee, "args": args}

    def _is_stopped(self, stop_at: set[str] | None) -> bool:
        return stop_at is not None and self.current.value in stop_at

    def _check_binary(self, operators: set[str], stop_at: set[str] | None) -> bool:
        if self._is_stopped(stop_at):
            return False
        return self.current.kind == "SYMBOL" and self.current.value in operators

    def _check_value(self, value: str) -> bool:
        return self.current.value == value

    def _match_value(self, value: str) -> bool:
        if self._check_value(value):
            self.advance()
            return True
        return False

    def _expect_value(self, value: str) -> Token:
        if not self._match_value(value):
            token = self.current
            raise TomatoParserError(
                f"Expected {value!r}, got {token.value!r} at line {token.line}, column {token.column}"
            )
        return self.tokens[self.pos - 1]

    def _match_kind(self, kind: str) -> bool:
        if self.current.kind == kind:
            self.advance()
            return True
        return False

    def _expect_kind(self, kind: str) -> Token:
        if not self._match_kind(kind):
            token = self.current
            raise TomatoParserError(
                f"Expected token kind {kind}, got {token.kind} ({token.value!r}) at line {token.line}, column {token.column}"
            )
        return self.tokens[self.pos - 1]

    def _match_keyword(self, keyword: str) -> bool:
        if self.current.kind == "KEYWORD" and self.current.value == keyword:
            self.advance()
            return True
        return False

    def _expect_keyword(self, keyword: str) -> Token:
        if not self._match_keyword(keyword):
            token = self.current
            raise TomatoParserError(
                f"Expected keyword {keyword!r}, got {token.value!r} at line {token.line}, column {token.column}"
            )
        return self.tokens[self.pos - 1]


def _decode_string(value: str) -> str:
    return ast.literal_eval(value)


def parse_source(source: str) -> dict[str, Any]:
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse_program()
