const codeEl = document.getElementById("code");
const outputEl = document.getElementById("output");
const runBtn = document.getElementById("runBtn");
const clearBtn = document.getElementById("clearBtn");
const highlightToggleEl = document.getElementById("highlightToggle");
const editorStackEl = document.getElementById("editorStack");
const highlightInputEl = document.getElementById("highlightInput");
const highlightCodeEl = document.getElementById("highlightCode");

let pyodide;
let highlightEnabled = false;

function setupTomatoHighlighter() {
  if (!window.hljs) {
    return;
  }

  window.hljs.registerLanguage("tomato", () => ({
    name: "Tomato",
    keywords: {
      keyword:
        "assign unset var print input into where do loop function return call import export list true false null",
    },
    contains: [
      window.hljs.C_LINE_COMMENT_MODE,
      window.hljs.QUOTE_STRING_MODE,
      {
        className: "number",
        begin: /\b-?\d+(?:\.\d+)?\b/,
      },
    ],
  }));
}

function updateHighlightPreview() {
  if (!highlightEnabled) {
    editorStackEl.classList.remove("highlight-input-enabled");
    return;
  }

  editorStackEl.classList.add("highlight-input-enabled");

  if (!window.hljs) {
    highlightCodeEl.textContent = codeEl.value;
    return;
  }

  const source = codeEl.value.endsWith("\n") ? `${codeEl.value} ` : codeEl.value;
  const highlighted = window.hljs.highlight(source, { language: "tomato" }).value;
  highlightCodeEl.innerHTML = highlighted;
}

function syncEditorScroll() {
  highlightInputEl.scrollTop = codeEl.scrollTop;
  highlightInputEl.scrollLeft = codeEl.scrollLeft;
}

setupTomatoHighlighter();

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

codeEl.addEventListener("input", () => {
  // set hash
  const code = codeEl.value;
  if (code) {
    const encoded = btoa(unescape(encodeURIComponent(code)));
    window.location.hash = encoded;
  } else {
    history.replaceState(null, null, " ");
  }

  updateHighlightPreview();
  syncEditorScroll();
});

codeEl.addEventListener("scroll", () => {
  syncEditorScroll();
});

highlightToggleEl.addEventListener("change", () => {
  highlightEnabled = highlightToggleEl.checked;
  updateHighlightPreview();
  syncEditorScroll();
});

// Load code from hash on page load
window.addEventListener("load", () => {
  const hash = window.location.hash.slice(1);
  if (hash) {
    try {
      const decoded = decodeURIComponent(escape(atob(hash)));
      codeEl.value = decoded;
    } catch (error) {
      console.error("Failed to decode code from URL hash:", error);
    }
  }

  updateHighlightPreview();
  syncEditorScroll();
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
