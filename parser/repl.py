from __future__ import annotations

from pathlib import Path
import sys

from parser.interpreter import Interpreter, TomatoRuntimeError
from parser.tomato_parser import TomatoParserError


REPL_BANNER = "Tomato REPL 🍅 (type :help for commands, :quit to exit)"


def _is_buffer_complete(buffer: str) -> bool:
    # Minimal completeness check for multiline blocks and list literals.
    braces = 0
    parens = 0
    brackets = 0

    for ch in buffer:
        if ch == "{":
            braces += 1
        elif ch == "}":
            braces -= 1
        elif ch == "(":
            parens += 1
        elif ch == ")":
            parens -= 1
        elif ch == "[":
            brackets += 1
        elif ch == "]":
            brackets -= 1

    stripped = buffer.strip()
    if not stripped:
        return False

    # Closed delimiters and terminated statement/block.
    return (
        braces <= 0
        and parens <= 0
        and brackets <= 0
        and (stripped.endswith(";") or stripped.endswith("}"))
    )


def run_repl() -> int:
    interpreter = Interpreter()
    cwd = Path.cwd()

    print(REPL_BANNER)
    print("Examples: assign x = 5;  |  print x;  |  function add(a,b) { return a + b; }")

    buffer_lines: list[str] = []

    while True:
        prompt = "... " if buffer_lines else "tomato> "
        try:
            line = input(prompt)
        except EOFError:
            print()
            return 0

        stripped = line.strip()

        if not buffer_lines and stripped in {":q", ":quit", "exit"}:
            return 0

        if not buffer_lines and stripped == ":help":
            print("Commands:")
            print("  :help           Show this help")
            print("  :quit / :q      Exit REPL")
            print("  :reset          Reset interpreter state")
            print("  :cwd            Show current working directory")
            print("  :load <path>    Execute a .tomato file")
            continue

        if not buffer_lines and stripped == ":reset":
            interpreter = Interpreter()
            print("State reset.")
            continue

        if not buffer_lines and stripped == ":cwd":
            print(cwd)
            continue

        if not buffer_lines and stripped.startswith(":load "):
            target = stripped.removeprefix(":load ").strip()
            if not target:
                print("Usage: :load <path>")
                continue
            source_path = Path(target)
            if not source_path.is_absolute():
                source_path = (cwd / source_path).resolve()
            if not source_path.exists():
                print(f"File not found: {source_path}")
                continue
            try:
                interpreter.run_file(source_path)
            except (TomatoParserError, TomatoRuntimeError) as exc:
                print(f"Error: {exc}")
            continue

        if not stripped and not buffer_lines:
            continue

        buffer_lines.append(line)
        source = "\n".join(buffer_lines).strip()

        if not _is_buffer_complete(source):
            continue

        try:
            interpreter.run_source(source, current_dir=cwd)
        except (TomatoParserError, TomatoRuntimeError) as exc:
            print(f"Error: {exc}")
        finally:
            buffer_lines = []


def main() -> int:
    try:
        return run_repl()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
