from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Callable, TextIO

from parser.tomato_parser import parse_source


class TomatoRuntimeError(Exception):
    """Raised when Tomato program execution fails."""


class _ReturnSignal(Exception):
    def __init__(self, value: Any) -> None:
        super().__init__("return")
        self.value = value


class Environment:
    def __init__(self, parent: Environment | None = None) -> None:
        self.parent = parent
        self.values: dict[str, Any] = {}

    def define(self, name: str, value: Any) -> None:
        self.values[name] = value

    def assign_or_define(self, name: str, value: Any) -> None:
        env = self._resolve(name)
        if env is None:
            self.values[name] = value
        else:
            env.values[name] = value

    def get(self, name: str) -> Any:
        env = self._resolve(name)
        if env is None:
            raise TomatoRuntimeError(f"Undefined variable: {name}")
        return env.values[name]

    def _resolve(self, name: str) -> Environment | None:
        if name in self.values:
            return self
        if self.parent is not None:
            return self.parent._resolve(name)
        return None


@dataclass
class TomatoFunction:
    name: str
    params: list[str]
    body: dict[str, Any]
    closure: Environment


class Interpreter:
    def __init__(
        self,
        output: TextIO | None = None,
        input_provider: Callable[[str], str] | None = None,
    ) -> None:
        self.globals = Environment()
        self.output = output or sys.stdout
        self.input_provider = input_provider or input
        self.cursed_assignments: dict[str, Any] = {}
        self._dir_stack: list[Path] = [Path.cwd()]
        self._imported_files: set[Path] = set()
        self._register_stdlib()

    def run_source(self, source: str, current_dir: Path | None = None) -> None:
        if current_dir is None:
            current_dir = self._dir_stack[-1]
        program = parse_source(source)
        self._dir_stack.append(current_dir)
        try:
            self.execute_program(program, self.globals)
        finally:
            self._dir_stack.pop()

    def run_file(self, file_path: str | Path) -> None:
        self._execute_file(Path(file_path), as_import=False)

    def execute_program(self, program: dict[str, Any], env: Environment) -> None:
        if program.get("type") != "Program":
            raise TomatoRuntimeError("Expected AST root node to be Program")
        for statement in program.get("body", []):
            self.execute_statement(statement, env)

    def execute_statement(self, statement: dict[str, Any], env: Environment) -> None:
        stmt_type = statement.get("type")

        if stmt_type == "AssignStatement":
            target = statement["target"]
            value = self.evaluate_expression(statement["value"], env)
            if target.get("type") == "Identifier":
                env.assign_or_define(target["name"], value)
            else:
                target_value = self.evaluate_expression(target, env)
                self.cursed_assignments[repr(target_value)] = value
            return

        if stmt_type == "VarDeclaration":
            env.define(statement["name"], None)
            return

        if stmt_type == "PrintStatement":
            values = [self.evaluate_expression(expr, env) for expr in statement["values"]]
            rendered = " ".join(self._display_value(value) for value in values)
            print(rendered, file=self.output)
            return

        if stmt_type == "InputStatement":
            prompt_value = self.evaluate_expression(statement["prompt"], env)
            prompt = self._to_string(prompt_value)
            received = self.input_provider(prompt)
            env.assign_or_define(statement["name"], received)
            return

        if stmt_type == "WhereStatement":
            condition = self.evaluate_expression(statement["condition"], env)
            if self._is_truthy(condition):
                block_env = Environment(parent=env)
                self.execute_block(statement["body"], block_env)
            return

        if stmt_type == "LoopStatement":
            count_value = self.evaluate_expression(statement["count"], env)
            count = max(0, int(self._to_number(count_value)))
            for _ in range(count):
                block_env = Environment(parent=env)
                self.execute_block(statement["body"], block_env)
            return

        if stmt_type == "FunctionDeclaration":
            fn = TomatoFunction(
                name=statement["name"],
                params=statement["params"],
                body=statement["body"],
                closure=env,
            )
            env.define(statement["name"], fn)
            return

        if stmt_type == "ReturnStatement":
            value_expr = statement.get("value")
            value = None if value_expr is None else self.evaluate_expression(value_expr, env)
            raise _ReturnSignal(value)

        if stmt_type == "CallStatement":
            self._eval_call(statement["call"], env)
            return

        if stmt_type == "ImportStatement":
            import_path = statement["path"]
            current_dir = self._dir_stack[-1]
            resolved = (current_dir / import_path).resolve()
            self._execute_file(resolved, as_import=True)
            return

        raise TomatoRuntimeError(f"Unsupported statement type: {stmt_type}")

    def execute_block(self, block: dict[str, Any], env: Environment) -> None:
        if block.get("type") != "BlockStatement":
            raise TomatoRuntimeError("Expected BlockStatement")
        for statement in block.get("body", []):
            self.execute_statement(statement, env)

    def evaluate_expression(self, expr: dict[str, Any], env: Environment) -> Any:
        expr_type = expr.get("type")

        if expr_type == "NumberLiteral":
            return expr["value"]
        if expr_type == "StringLiteral":
            return expr["value"]
        if expr_type == "ListLiteral":
            return [self.evaluate_expression(item, env) for item in expr["elements"]]
        if expr_type == "BooleanLiteral":
            return expr["value"]
        if expr_type == "NullLiteral":
            return None
        if expr_type == "Identifier":
            return env.get(expr["name"])
        if expr_type == "GroupingExpression":
            return self.evaluate_expression(expr["expression"], env)
        if expr_type == "UnaryExpression":
            operator = expr["operator"]
            operand = self.evaluate_expression(expr["operand"], env)
            if operator == "-":
                return -self._to_number(operand)
            raise TomatoRuntimeError(f"Unsupported unary operator: {operator}")
        if expr_type == "BinaryExpression":
            return self._eval_binary(expr, env)
        if expr_type == "CallExpression":
            return self._eval_call(expr, env)

        raise TomatoRuntimeError(f"Unsupported expression type: {expr_type}")

    def _eval_binary(self, expr: dict[str, Any], env: Environment) -> Any:
        left = self.evaluate_expression(expr["left"], env)
        right = self.evaluate_expression(expr["right"], env)
        operator = expr["operator"]

        if operator == "+":
            if isinstance(left, str) or isinstance(right, str):
                return self._to_string(left) + self._to_string(right)
            return self._to_number(left) + self._to_number(right)

        if operator == "-":
            return self._to_number(left) - self._to_number(right)

        if operator == "*":
            return self._to_number(left) * self._to_number(right)

        if operator == "/":
            divisor = self._to_number(right)
            if divisor == 0:
                raise TomatoRuntimeError("Division by zero")
            return self._to_number(left) / divisor

        if operator in {"<", "<=", ">", ">="}:
            left_num = self._to_number(left)
            right_num = self._to_number(right)
            if operator == "<":
                return left_num < right_num
            if operator == "<=":
                return left_num <= right_num
            if operator == ">":
                return left_num > right_num
            return left_num >= right_num

        if operator == "==":
            return left == right

        if operator == "!=":
            return left != right

        raise TomatoRuntimeError(f"Unsupported binary operator: {operator}")

    def _eval_call(self, call_expr: dict[str, Any], env: Environment) -> Any:
        callee_name = call_expr["callee"]
        callee = env.get(callee_name)
        args = [self.evaluate_expression(arg, env) for arg in call_expr.get("args", [])]

        if isinstance(callee, TomatoFunction):
            if len(args) != len(callee.params):
                raise TomatoRuntimeError(
                    f"Function {callee.name} expects {len(callee.params)} args, got {len(args)}"
                )
            call_env = Environment(parent=callee.closure)
            for param, arg in zip(callee.params, args, strict=True):
                call_env.define(param, arg)
            try:
                self.execute_block(callee.body, call_env)
            except _ReturnSignal as signal:
                return signal.value
            return None

        if callable(callee):
            try:
                return callee(*args)
            except TypeError as exc:
                raise TomatoRuntimeError(f"Invalid arguments for {callee_name}: {exc}") from exc

        raise TomatoRuntimeError(f"{callee_name} is not callable")

    def _register_stdlib(self) -> None:
        self.globals.define("list", lambda *args: list(args))
        self.globals.define("len", self._stdlib_len)
        self.globals.define("push", self._stdlib_push)
        self.globals.define("pop", self._stdlib_pop)
        self.globals.define("get", self._stdlib_get)
        self.globals.define("set", self._stdlib_set)
        self.globals.define("type", self._stdlib_type)
        self.globals.define("str", self._stdlib_str)
        self.globals.define("num", self._stdlib_num)

    def _stdlib_len(self, value: Any) -> int:
        if isinstance(value, (list, str)):
            return len(value)
        raise TomatoRuntimeError("len expects a list or string")

    def _stdlib_push(self, value: Any, item: Any) -> list[Any]:
        if not isinstance(value, list):
            raise TomatoRuntimeError("push expects first argument to be list")
        value.append(item)
        return value

    def _stdlib_pop(self, value: Any) -> Any:
        if not isinstance(value, list):
            raise TomatoRuntimeError("pop expects a list")
        if not value:
            raise TomatoRuntimeError("pop cannot operate on empty list")
        return value.pop()

    def _stdlib_get(self, value: Any, index: Any) -> Any:
        if not isinstance(value, list):
            raise TomatoRuntimeError("get expects first argument to be list")
        idx = int(self._to_number(index))
        try:
            return value[idx]
        except IndexError as exc:
            raise TomatoRuntimeError(f"list index out of range: {idx}") from exc

    def _stdlib_set(self, value: Any, index: Any, item: Any) -> list[Any]:
        if not isinstance(value, list):
            raise TomatoRuntimeError("set expects first argument to be list")
        idx = int(self._to_number(index))
        try:
            value[idx] = item
        except IndexError as exc:
            raise TomatoRuntimeError(f"list index out of range: {idx}") from exc
        return value

    def _stdlib_type(self, value: Any) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, (int, float)):
            return "number"
        if isinstance(value, str):
            return "string"
        if isinstance(value, list):
            return "list"
        if isinstance(value, TomatoFunction):
            return "function"
        if callable(value):
            return "builtin"
        return "unknown"

    def _stdlib_str(self, value: Any) -> str:
        return self._to_string(value)

    def _stdlib_num(self, value: Any) -> float:
        return self._to_number(value)

    def _execute_file(self, file_path: Path, as_import: bool) -> None:
        resolved = file_path.resolve()
        if as_import and resolved in self._imported_files:
            return

        if not resolved.exists():
            raise TomatoRuntimeError(f"Imported file not found: {resolved}")

        source = resolved.read_text(encoding="utf-8")
        program = parse_source(source)

        self._imported_files.add(resolved)
        self._dir_stack.append(resolved.parent)
        try:
            self.execute_program(program, self.globals)
        finally:
            self._dir_stack.pop()

    def _to_number(self, value: Any) -> float:
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        if isinstance(value, (int, float)):
            return float(value)
        if value is None:
            return 0.0
        if isinstance(value, str):
            return float(self._letters_to_number(value))
        raise TomatoRuntimeError(f"Cannot convert {type(value).__name__} to number")

    def _to_string(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return "null"
        if isinstance(value, int):
            return self._number_to_letters(value)
        if isinstance(value, float):
            if value.is_integer():
                return self._number_to_letters(int(value))
            return str(value)
        raise TomatoRuntimeError(f"Cannot convert {type(value).__name__} to string")

    def _display_value(self, value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return "null"
        return str(value)

    def _is_truthy(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value != ""
        return bool(value)

    def _number_to_letters(self, number: int) -> str:
        if number <= 0:
            return ""
        result: list[str] = []
        n = number
        while n > 0:
            n -= 1
            result.append(chr(ord("a") + (n % 26)))
            n //= 26
        return "".join(reversed(result))

    def _letters_to_number(self, text: str) -> int:
        stripped = text.strip().lower()
        if stripped == "":
            return 0
        total = 0
        for ch in stripped:
            if ch < "a" or ch > "z":
                raise TomatoRuntimeError(
                    f"Cannot convert string {text!r} to number: expected letters a-z"
                )
            total = (total * 26) + (ord(ch) - ord("a") + 1)
        return total


def interpret_source(
    source: str,
    output: TextIO | None = None,
    input_provider: Callable[[str], str] | None = None,
) -> Interpreter:
    interpreter = Interpreter(output=output, input_provider=input_provider)
    interpreter.run_source(source)
    return interpreter


def interpret_file(
    path: str | Path,
    output: TextIO | None = None,
    input_provider: Callable[[str], str] | None = None,
) -> Interpreter:
    interpreter = Interpreter(output=output, input_provider=input_provider)
    interpreter.run_file(path)
    return interpreter
