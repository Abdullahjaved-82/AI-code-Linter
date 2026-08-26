# AI Code Linter

![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)
![PyQt5](https://img.shields.io/badge/UI-PyQt5-41B883.svg)
![Status](https://img.shields.io/badge/Status-Portfolio%20Project-orange.svg)

**AI Code Linter is a desktop Python code quality tool that analyzes source code, highlights issues, and applies conservative quick fixes through a PyQt5 interface.**

---

## Overview

AI Code Linter is a lightweight desktop application designed to help developers spot bugs, code smells, and risky patterns in Python code before they ship. It combines rule-based static analysis with a simple GUI, making it useful for students, solo developers, and teams that want a fast local code-review helper without relying on a cloud service.

The project focuses on practical code-quality checks such as syntax errors, unused variables, magic numbers, suspicious calls like `eval()` / `exec()`, and hard-coded credentials. It also includes conservative auto-fix logic for common patterns, such as off-by-one loops, `== None` comparisons, bare `except:` blocks, and missing colons in simple block headers.

The repository is structured as a portfolio-ready desktop software project: it has a working UI, analysis engine, fixer utilities, sample test harnesses, and a placeholder for future CodeBERT integration. That makes it a solid example of combining UI engineering, static analysis, and machine learning architecture planning in one codebase.

---

## Key Features

- **PyQt5 desktop interface** with:
  - source editor
  - corrected-code preview panel
  - analysis report pane
  - suggestions list
  - status bar and progress indicator
- **AST-based Python analysis** for:
  - syntax errors
  - unused variables
  - magic numbers
  - dangerous function usage (`eval`, `exec`, `execfile`)
  - suspicious string concatenation patterns
  - hard-coded credential heuristics
- **Optional auto-formatting** via `autopep8`
- **Conservative quick-fix engine** in `fixer.py` for:
  - `range(len(x) + 1)` off-by-one corrections
  - simple index-based loop rewrites
  - bare `except:` replacement
  - `== None` / `!= None` normalization
  - missing colon repair for basic block headers
- **Non-Python input detection** to avoid mangling Java/C/C++-style code
- **Division-by-zero heuristic** that can flag likely runtime errors and insert a basic guard when auto-fix is enabled
- **File open/save support** for loading source files and exporting corrected code
- **Basic syntax highlighting** for Python keywords, strings, and comments
- **CodeBERT stub** prepared for future transformer-based analysis

---

## Tech Stack

| Category | Technologies |
|---|---|
| Language | Python |
| Desktop UI | PyQt5 |
| Static analysis | `ast`, `re` |
| Auto-formatting | `autopep8` |
| ML / NLP integration | `transformers`, `torch` |
| Code generation / rewriting | `astor` |
| Export / reporting | `reportlab` |

**Detected project type:** Python desktop application with rule-based analysis and optional ML integration.

---

## Architecture / How It Works

The project is intentionally small and modular:

- `main.py` is the application entry point.
- `ui/main_ui.py` builds the desktop interface and wires button actions to the analyzer.
- `linter.py` performs the main code analysis and produces:
  - human-readable reports
  - a fixed-code preview
  - line numbers to highlight
  - a list of applied fixes
- `fixer.py` contains conservative text-based transformations used when `auto_fix=True`.
- `models/codebert_stub.py` is a lazy-loading placeholder for CodeBERT inference.
- Test scripts like `test_linter.py` and `run_fixer_tests.py` act as manual regression checks.

### Data flow

1. The user pastes or opens Python code in the editor.
2. `CodeLinterUI` calls `analyze_code()` from `linter.py`.
3. `linter.py` parses the code with `ast.parse()` and runs heuristic checks.
4. If `auto_fix=True`, the analyzer also calls `fixer.apply_fixes()` and may apply extra guard logic for obvious zero-divisor cases.
5. The UI displays:
   - the report text
   - the corrected preview
   - highlighted lines
   - fix suggestions in the sidebar

### Design decisions

- The analyzer is **rule-based first**, which keeps the app fast, deterministic, and easy to reason about.
- Fixes are **conservative** on purpose, reducing the risk of changing code incorrectly.
- The CodeBERT integration is stubbed rather than forced into the runtime, which keeps the current app lightweight while leaving room for future ML upgrades.

---

## Installation

### Prerequisites
- Python 3.9 or newer
- Windows, macOS, or Linux
- A virtual environment is strongly recommended

### 1) Clone the repository

```bash
git clone https://github.com/Abdullahjaved-82/AI-code-Linter.git
cd AI-code-Linter
```

### 2) Create and activate a virtual environment

**Windows PowerShell**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

If you want the UI to open and run with the fewest missing pieces, install the main desktop dependency explicitly if needed:

```bash
pip install PyQt5
```

### 4) Optional ML/runtime dependencies

The repository includes `transformers` and `torch` for future CodeBERT support. If you plan to use the model stub, make sure those packages are installed correctly in your environment.

### 5) Run the application

```bash
python main.py
```

---

## Usage

### Launch the desktop app

```bash
python main.py
```

### Typical workflow

1. Paste Python code into the editor.
2. Click **Analyze** to generate a report and preview formatted output.
3. Click **Quick Fix** to apply conservative automated fixes.
4. Review the corrected code in the preview panel.
5. Use **Save** to export the cleaned-up file.

### Example: analyzer output

The analyzer returns a tuple like:

```python
report_text, fixed_code, highlight_lines, applied_fixes
```

### Example: direct analyzer usage

```python
from linter import analyze_code

code = """
def broken_divide(a, b)
    return a / b
"""

report, fixed, highlights, applied = analyze_code(code, auto_fix=True)
print(report)
print(fixed)
print(highlights)
print(applied)
```

### Example: fixer utilities

```python
from fixer import apply_fixes

code = """
for i in range(len(arr) + 1):
    print(arr[i])
"""

new_code, fixes = apply_fixes(code)
print(new_code)
print(fixes)
```

### Example: CodeBERT stub

```python
from models.codebert_stub import predict

result = predict("def add(a, b): return a + b")
print(result)
```

> Note: `codebert_stub.py` is currently a placeholder loader. It will return an error field or placeholder score unless the model is available and a classifier head is implemented.

---

## API Reference

There is no HTTP API in this repository.
The project is a **desktop application** with Python functions that serve as the internal API.

### `linter.analyze_code(code: str, auto_fix: bool = False)`

Analyzes Python code and returns:

```python
(report_text: str, fixed_code: str, highlight_lines: list[int], applied_fixes: list[dict])
```

#### Example result shape

```python
{
  "report_text": "Found 1 errors, 2 warnings, 3 info...",
  "fixed_code": "...",
  "highlight_lines": [3, 8, 12],
  "applied_fixes": [
    {
      "line": 8,
      "message": "Replaced bare except with except Exception as e",
      "original": "except:\n",
      "replacement": "except Exception as e:\n"
    }
  ]
}
```

### `fixer.apply_fixes(code: str)`

Applies deterministic quick-fix rules and returns:

```python
(new_code: str, fixes: list[dict])
```

### `fixer.attempt_syntax_fixes(code: str)`

Attempts small syntax repairs such as inserting missing colons:

```python
(new_code: str, fixes: list[dict])
```

### `models.codebert_stub.predict(code: str)`

Returns a placeholder model response:

```python
{
  "label": "unknown",
  "score": 0.0,
  "error": "..."
}
```

---

## Folder Structure

```text
AI-code-Linter/
├── main.py                  # Application entry point
├── linter.py                # AST-based analyzer and reporting logic
├── fixer.py                 # Safe heuristic quick-fix utilities
├── ui/
│   └── main_ui.py           # PyQt5 GUI, actions, highlighting, save/open flow
├── models/
│   └── codebert_stub.py     # Lazy-loading CodeBERT placeholder
├── test_linter.py           # End-to-end analyzer test harness
├── run_fixer_tests.py       # Rule-focused fixer test runner
├── demo_logic_exception_test.py   # Sample code for analyzer demo
├── demo_wrong_code_test.py        # Sample code for analyzer demo
├── requirements.txt         # Python dependencies
├── README.md                # Project documentation
└── PROJECT_SUMMARY.txt      # Concise project summary
```

### What each part does

- **`main.py`** — starts the PyQt5 application.
- **`ui/main_ui.py`** — handles the desktop experience and user actions.
- **`linter.py`** — performs AST analysis and generates reports.
- **`fixer.py`** — contains safe code-repair transformations.
- **`models/codebert_stub.py`** — future ML integration point.
- **demo/test scripts** — provide sample inputs and manual verification flows.

---

## Challenges & Learnings

One of the main engineering challenges in this project is balancing automation with safety. The fixer logic in `fixer.py` is intentionally conservative so that automated changes do not introduce new bugs while still resolving common patterns like off-by-one loops and bare exception handling.

Another important learning is how to combine static analysis, formatting, and GUI state management into a single workflow. The UI in `ui/main_ui.py` has to handle analysis results, fix previews, line highlighting, saving files, and status updates without making the application feel complex to the user.

A third takeaway is designing for future ML integration without blocking the current product. The `models/codebert_stub.py` module shows how a transformer-based workflow can be introduced later while keeping the current release lightweight and functional.

---

## Future Improvements

- Add a real trained classifier head for the CodeBERT pipeline
- Improve fix selection so users can accept or reject individual suggestions
- Add unit tests and CI via GitHub Actions
- Make the analyzer thread-safe for long-running model inference
- Expand support for more Python anti-patterns and runtime risks
- Improve the division-by-zero guard insertion logic
- Add export options for HTML, PDF, or JSON reports
- Package the app with PyInstaller for easier distribution

---
