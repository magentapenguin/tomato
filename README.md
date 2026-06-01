# 🍅 Tomato

Tomato is a cursed programming language.
It lets you:

- Assign to anything (even if doesn't make sense) (`assign 5 = 10;`)
- Cursed type conversions [(More info)](#types)
<!-- TODO: Add more features -->

## Syntax

Tomato has a simple syntax:

- Statements end with a semicolon (`;`)
- Variables are declared with the `assign` keyword (e.g. `assign x = 5;`)
- You can assign to anything (e.g. `assign 5 = 10;`)
- You can use basic arithmetic operators (`+`, `-`, `*`, `/`) and parentheses for grouping (e.g. `assign x = (5 + 3) * 2;`)
- You can use the `print` keyword to output values (e.g. `print x;`) or (e.g. `print "52" "*" "2";`)
- You can use the `where` keyword like an `if` statement (e.g. `where x > 10 do { print "x is greater than 10"; }`)
- You can use the `loop` keyword for loops (e.g. `loop 5 do { print "Hello, world!"; }`)
- You can use the `function` keyword to define functions (e.g. `function add(a, b) { return a + b; }`)
- You can use the `return` keyword to return values from functions (e.g. `function add(a, b) { return a + b; }`)
- You can use the `call` keyword to call functions (e.g. `call add(5, 3);`)
- You can use the `import` keyword to import other Tomato files (e.g. `import "utils.tomato";`)
- You can use the `export` keyword to export functions from a Tomato file (e.g. `export function add(a, b) { return a + b; }`)
- You can use the `var` keyword to declare variables without assigning a value (e.g. `var x;`)
- You can use the `input` keyword to get user input (e.g. `input "Enter your name: " into name;`)
- You can use the `list` keyword to create lists (e.g. `assign myList = list(1, 2, 3);`) or use list literals (e.g. `assign myList = [1, 2, 3];`)

## Types

Tomato has 4 types:

- `number`: A number (e.g. `5`, `3.14`, `-2`)
- `string`: A string (e.g. `"Hello, world!"`, `'Tomato'`)
- `boolean`: A boolean value (`true` or `false`)
- `null`: A null value (`null`)

### Cursed Type Conversions

Tomato has some cursed type conversions:

- `number` to `string`: Converts the number to the letter of the alphabet corresponding to its value (e.g. `1` becomes `a`, `2` becomes `b`, ..., `26` becomes `z`, and `27` becomes `aa`, etc.)
- `string` to `number`: Converts the string to the sum of the values of its characters (e.g. `a` becomes `1`, `b` becomes `2`, ..., `z` becomes `26`, and `aa` becomes `27`, etc.)

## Python Parser

This repository now includes a Python parser under `parser/`.

### Parser files

- `parser/tomato_parser.py`: Lexer + recursive-descent parser that outputs an AST (dictionary form).
- `parser/cli.py`: Command-line entrypoint for parsing `.tomato` files.
- `parser/examples/sample.tomato`: Example source file.
- `parser/tests/test_parser.py`: Unit tests.

### Run the parser

From the project root:

- `python -m parser.cli parser/examples/sample.tomato`

This prints the parsed AST as formatted JSON.

### Run tests

From the project root:

- `python -m unittest discover -s parser/tests -p "test_*.py"`

## Python Interpreter

Tomato now also has an interpreter runtime under `parser/interpreter.py`.

### Runtime behavior

- Executes statements in order (`assign`, `var`, `print`, `input`, `where`, `loop`, `function`, `return`, `call`, `import`).
- Supports function declarations and calls with lexical scope.
- Supports list literals (`[1, 2, 3]`) and `list(...)` expressions.
- Supports cursed assignment to non-identifiers by storing those writes internally.
- Supports cursed conversions:
  - number to string: base-26 letters (`1 -> a`, `27 -> aa`)
  - string to number: inverse base-26 (`aa -> 27`)

### Standard library

Tomato includes built-ins available as callable functions:

- `list(a, b, c, ...)`: create a list
- `len(value)`: length of a list or string
- `push(listValue, item)`: append item and return the list
- `pop(listValue)`: pop and return last item
- `get(listValue, index)`: get an item by index
- `set(listValue, index, item)`: set an item and return the list
- `type(value)`: returns `null`, `boolean`, `number`, `string`, `list`, `function`, or `builtin`
- `str(value)`: convert value to string using Tomato conversions
- `num(value)`: convert value to number using Tomato conversions

### Run a Tomato program

From the project root:

- `python -m parser.run parser/examples/sample.tomato`

## VS Code Syntax Extension

A local VS Code extension is included in `vscode-extension/` to provide Tomato syntax support.

### Files

- `vscode-extension/package.json`: Extension manifest and language registration.
- `vscode-extension/language-configuration.json`: Brackets, comments, auto-closing pairs.
- `vscode-extension/syntaxes/tomato.tmLanguage.json`: TextMate grammar for highlighting.

### Use in VS Code

1. Open this repo in VS Code.
1. Run **Run Tomato Extension (from repo root)** from `.vscode/launch.json`.
1. If you opened only the `vscode-extension` folder as your workspace, run **Run Tomato Extension** from `vscode-extension/.vscode/launch.json`.
1. In the Extension Development Host window, open any `.tomato` file.
