from __future__ import annotations

import json
from pathlib import Path
import sys

from parser.tomato_parser import TomatoParserError, parse_source


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m parser.cli <file.tomato>")
        return 1

    source_path = Path(sys.argv[1])
    if not source_path.exists():
        print(f"File not found: {source_path}")
        return 1

    source = source_path.read_text(encoding="utf-8")
    try:
        ast_tree = parse_source(source)
    except TomatoParserError as exc:
        print(f"Parse error: {exc}")
        return 2

    print(json.dumps(ast_tree, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
