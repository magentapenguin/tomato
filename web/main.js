const codeEl = document.getElementById("code");
const outputEl = document.getElementById("output");
const runBtn = document.getElementById("runBtn");
const clearBtn = document.getElementById("clearBtn");

let pyodide;

function appendOutput(text) {
  outputEl.textContent += text;
  outputEl.scrollTop = outputEl.scrollHeight;
}

function setBusy(isBusy) {
  runBtn.disabled = isBusy;
  runBtn.textContent = isBusy ? "Running..." : "Run";
}

clearBtn.addEventListener("click", () => {
  outputEl.textContent = "";
});

async function loadText(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load ${url}: ${response.status}`);
  }
  return response.text();
}

async function ensurePyodide() {
  if (pyodide) {
    return pyodide;
  }

  appendOutput("Loading Pyodide...\n");
  pyodide = await loadPyodide();

  pyodide.registerJsModule("tomato_bridge", {
    write_output: (text) => appendOutput(String(text)),
    read_input: (promptText) => {
      const text = String(promptText ?? "");
      appendOutput(text);
      const answer = window.prompt(text) ?? "";
      appendOutput(`${answer}\n`);
      return answer;
    },
  });

  const parserCode = await loadText("../parser/tomato_parser.py");
  const interpreterCode = await loadText("../parser/interpreter.py");

  pyodide.FS.mkdirTree("/home/pyodide/parser");
  pyodide.FS.writeFile("/home/pyodide/parser/__init__.py", "");
  pyodide.FS.writeFile("/home/pyodide/parser/tomato_parser.py", parserCode);
  pyodide.FS.writeFile("/home/pyodide/parser/interpreter.py", interpreterCode);

  await pyodide.runPythonAsync(`
import sys
sys.path.insert(0, '/home/pyodide')
`);

  appendOutput("Pyodide ready.\n");
  return pyodide;
}

runBtn.addEventListener("click", async () => {
  setBusy(true);
  try {
    const py = await ensurePyodide();
    const code = codeEl.value;
    const escaped = JSON.stringify(code);

    await py.runPythonAsync(`
import io
import tomato_bridge
from parser.interpreter import Interpreter, TomatoRuntimeError
from parser.tomato_parser import TomatoParserError

class _BridgeWriter(io.TextIOBase):
    def write(self, s):
        tomato_bridge.write_output(str(s))
        return len(s)

def _ask(prompt):
  return tomato_bridge.read_input(prompt)

source = ${escaped}
out = _BridgeWriter()
interpreter = Interpreter(output=out, input_provider=_ask)
try:
    interpreter.run_source(source)
except TomatoParserError as exc:
    tomato_bridge.write_output(f"Parse error: {exc}\\n")
except TomatoRuntimeError as exc:
    tomato_bridge.write_output(f"Runtime error: {exc}\\n")
`);
  } catch (error) {
    appendOutput(`\nError: ${error.message}\n`);
  } finally {
    setBusy(false);
  }
});
