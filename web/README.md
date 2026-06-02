# Tomato Web Playground (Pyodide)

This folder contains a browser playground that runs Tomato using Pyodide.

## Files

- `index.html`: UI shell
- `styles.css`: styling
- `main.js`: Pyodide bootstrap + execution bridge

## Optional syntax highlighting

The editor includes an optional **syntax highlighting in-editor** toggle.

- Keep it off for plain editing.
- Turn it on to render highlighted Tomato code directly in the input area.

This uses Highlight.js from CDN and falls back to plain text rendering if unavailable.

## Run locally

From the repository root, run:

- `python -m http.server 8000`

Open:

- <http://localhost:8000/web/>

## How it works

- Loads Pyodide from CDN
- Fetches local Python modules:
  - `parser/tomato_parser.py`
  - `parser/interpreter.py`
- Writes them into Pyodide FS under `/home/pyodide/parser`
- Executes user Tomato code via `Interpreter.run_source`
