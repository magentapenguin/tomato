from __future__ import annotations

from pathlib import Path
import sys

from parser.interpreter import TomatoRuntimeError, interpret_file
from parser.tomato_parser import TomatoParserError


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m parser.run <file.tomato>")
        return 1

    source_path = Path(sys.argv[1])
    if not source_path.exists():
        print(f"File not found: {source_path}")
        return 1

    try:
        interpret_file(source_path)
    except TomatoParserError as exc:
        print(f"Parse error: {exc}")
        return 2
    except TomatoRuntimeError as exc:
        print(f"Runtime error: {exc}")
        return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
