import ast
import re
try:
    import autopep8
    _AUTOPEP8_AVAILABLE = True
except Exception:
    autopep8 = None
    _AUTOPEP8_AVAILABLE = False
from typing import List, Tuple


def _format_report(items: List[dict]) -> str:
    if not items:
        return "✅ No issues found."

    lines = []
    counts = {"error": 0, "warning": 0, "info": 0}
    for it in items:
        sev = it.get("severity", "info")
        counts[sev] = counts.get(sev, 0) + 1
        ln = it.get("line", "?")
        msg = it.get("message", "")
        sug = it.get("suggestion", "")
        lines.append(f"{sev.upper()} (line {ln}): {msg}" + (f"\n    Suggestion: {sug}" if sug else ""))

    header = f"Found {counts['error']} errors, {counts['warning']} warnings, {counts['info']} info.\n"
    return header + "\n".join(lines)


def analyze_code(code: str, auto_fix: bool = False) -> Tuple[str, str, List[int], list]:
    """
    Analyze Python code using a lightweight, rule-based approach and autopep8 for formatting.

    Returns:
      - report_text: human-readable report
      - fixed_code: code after autopep8 formatting
      - highlights: list of line numbers to highlight in the editor
    """
    # Save a temp copy (useful for external tools)
    try:
        with open("temp_code.py", "w", encoding="utf-8") as f:
            f.write(code)
    except Exception:
        pass

    items = []
    highlight_lines = []
    applied_fixes = []
    # interprocedural helpers
    func_params = {}
    func_divisor_params = {}
    calls_with_zero = []

    # Quick heuristic: detect likely non-Python code (Java/C/C++) and avoid trying
    # Python-specific fixes which may mangle other languages. If it's probably not
    # Python, return a concise message and leave the code unchanged.
    def is_probably_python(s: str) -> bool:
        # obvious Java/CPP patterns
        java_patterns = [r"\bpublic\s+class\b", r"System\.out\.println", r"\bimport\s+java\.", r"#include\b", r"using\s+namespace"]
        for p in java_patterns:
            if re.search(p, s):
                return False
        # many semicolon line endings suggests C-family language
        semicolon_lines = sum(1 for ln in s.splitlines() if ln.strip().endswith(';'))
        if semicolon_lines > 3:
            return False
        # braces-heavy code
        if s.count('{') >= 1 and s.count('}') >= 1 and semicolon_lines > 0:
            return False
        return True

    if not is_probably_python(code):
        items.append({
            "line": 0,
            "severity": "error",
            "message": "Input does not appear to be Python code.",
            "suggestion": "This analyzer currently supports Python. Paste Python code or disable auto-fix for other languages.",
        })
        # Do not attempt autopep8 or automatic fixes on non-Python code
        fixed_code = code
        report_text = _format_report(items)
        return report_text, fixed_code, [], []

    # Syntax check
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        items.append({
            "line": e.lineno or 0,
            "severity": "error",
            "message": f"SyntaxError: {e.msg}",
            "suggestion": "Check syntax near the reported location (missing colon, parentheses, or indentation).",
        })
        highlight_lines.append(e.lineno or 0)
        if _AUTOPEP8_AVAILABLE:
            try:
                fixed_code = autopep8.fix_code(code)
            except Exception:
                fixed_code = code
        else:
            fixed_code = code
        # attempt conservative syntax fixes if requested
        if auto_fix:
            try:
                from fixer import attempt_syntax_fixes
                new_code, fixes = attempt_syntax_fixes(code)
                if fixes:
                    # record fixes and return
                    for f in fixes:
                        items.append({
                            "line": f.get('line', 0),
                            "severity": "info",
                            "message": f.get('message', 'Applied syntax fix'),
                            "suggestion": f.get('replacement', ''),
                        })
                        highlight_lines.append(f.get('line', 0))
                    # Use the new_code produced by the syntax fixer. If autopep8 is
                    # available, format it; otherwise return the raw new_code.
                    if _AUTOPEP8_AVAILABLE:
                        try:
                            fixed_code = autopep8.fix_code(new_code)
                        except Exception:
                            fixed_code = new_code
                    else:
                        fixed_code = new_code
                    return _format_report(items), fixed_code, highlight_lines, fixes
            except Exception:
                pass

        return _format_report(items), fixed_code, highlight_lines, []

    # Basic AST-based rules
    assigned_names = set()
    used_names = set()
    magic_number_lines = set()
    suspicious_calls = []
    hardcoded_credentials = []

    class Visitor(ast.NodeVisitor):
        def visit_Assign(self, node: ast.Assign):
            # record assigned names
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned_names.add(target.id)
            self.generic_visit(node)

        def visit_Name(self, node: ast.Name):
            if isinstance(node.ctx, ast.Load):
                used_names.add(node.id)

        def visit_Constant(self, node: ast.Constant):
            # magic number detection (simple heuristic)
            if isinstance(node.value, (int, float)) and node.value not in (0, 1, -1):
                # avoid flagging common constants like booleans represented as 0/1
                magic_number_lines.add(getattr(node, 'lineno', None))

        def visit_Call(self, node: ast.Call):
            # detect eval/exec and other suspicious functions
            func = node.func
            name = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr

            if name in ("eval", "exec", "execfile"):
                suspicious_calls.append((getattr(node, 'lineno', None), name))

            # detect string formatting that looks like SQL concatenation (very heuristic)
            for arg in node.args:
                if isinstance(arg, ast.BinOp):
                    suspicious_calls.append((getattr(node, 'lineno', None), 'possible_string_concat'))

            self.generic_visit(node)

        def visit_Compare(self, node: ast.Compare):
            self.generic_visit(node)

        def visit_FunctionDef(self, node: ast.FunctionDef):
            # simple naming check: discourage single-letter function names
            if len(node.name) == 1:
                items.append({
                    "line": node.lineno,
                    "severity": "warning",
                    "message": f"Function name '{node.name}' is too short.",
                    "suggestion": "Use descriptive function names (e.g., calculate_total).",
                })
            # record parameter list for later interprocedural checks
            func_params[node.name] = [a.arg for a in node.args.args]
            # detect if any parameter is used as divisor inside this function
            for child in ast.walk(node):
                if isinstance(child, ast.BinOp) and isinstance(child.op, ast.Div):
                    # right side used as divisor
                    if isinstance(child.right, ast.Name) and child.right.id in func_params[node.name]:
                        func_divisor_params.setdefault(node.name, set()).add(child.right.id)
            self.generic_visit(node)
            self.generic_visit(node)

    visitor = Visitor()
    visitor.visit(tree)

    # After visiting, look for calls to functions that may pass literal 0 into a divisor parameter
    # collect calls
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                fname = func.id
            else:
                continue
            calls.append((node.lineno, fname, node.args))

    # Analyze calls for possible zero divisor
    for ln, fname, args in calls:
        if fname in func_divisor_params and fname in func_params:
            params = func_params[fname]
            divisor_params = func_divisor_params[fname]
            # check positional arguments only (conservative)
            for idx, arg in enumerate(args):
                if idx < len(params) and params[idx] in divisor_params:
                    # if the argument is a literal zero
                    if isinstance(arg, ast.Constant) and (arg.value == 0):
                        pname = params[idx]
                        items.append({
                            "line": ln,
                            "severity": "error",
                            "message": f"Possible division by zero: function '{fname}' called with 0 for parameter '{pname}'.",
                            "suggestion": f"Guard the divisor in '{fname}' or avoid calling with zero.",
                        })
                        highlight_lines.append(ln)
                        # record for auto-fix
                        calls_with_zero.append((fname, pname))


    # Unused variables
    for name in sorted(assigned_names):
        if name not in used_names and not name.startswith("_"):
            # find first occurrence line (best-effort)
            pattern = re.compile(rf"\b{name}\b")
            for i, line in enumerate(code.splitlines(), start=1):
                if pattern.search(line):
                    items.append({
                        "line": i,
                        "severity": "warning",
                        "message": f"Variable '{name}' assigned but never used.",
                        "suggestion": "Remove unused variables or prefix with '_' if intentionally unused.",
                    })
                    highlight_lines.append(i)
                    break

    # Magic numbers
    for ln in sorted(n for n in magic_number_lines if n):
        items.append({
            "line": ln,
            "severity": "info",
            "message": "Possible magic number used.",
            "suggestion": "Consider extracting to a named constant explaining its meaning.",
        })
        highlight_lines.append(ln)

    # Suspicious calls
    for ln, name in suspicious_calls:
        if name == 'possible_string_concat':
            items.append({
                "line": ln,
                "severity": "warning",
                "message": "String concatenation detected — could be unsafe for SQL queries.",
                "suggestion": "Use parameterized queries or proper formatting libraries.",
            })
        else:
            items.append({
                "line": ln,
                "severity": "warning",
                "message": f"Use of dangerous function '{name}' detected.",
                "suggestion": "Avoid eval/exec; use safer alternatives.",
            })
        if ln:
            highlight_lines.append(ln)

    # Hard-coded credentials heuristic: look for password-like assignments
    for i, line in enumerate(code.splitlines(), start=1):
        if re.search(r"password\s*=\s*['\"].+['\"]", line, re.IGNORECASE) or re.search(r"api_key\s*=\s*['\"].+['\"]", line, re.IGNORECASE):
            items.append({
                "line": i,
                "severity": "warning",
                "message": "Possible hard-coded credential found.",
                "suggestion": "Move secrets to environment variables or a config file; do not commit them.",
            })
            highlight_lines.append(i)

    # Auto-format code with autopep8
    if _AUTOPEP8_AVAILABLE:
        try:
            fixed_code = autopep8.fix_code(code)
        except Exception as e:
            fixed_code = code
            items.append({
                "line": 0,
                "severity": "info",
                "message": f"Auto-formatting failed: {e}",
                "suggestion": "Install/upgrade autopep8.",
            })
    else:
        fixed_code = code
        items.append({
            "line": 0,
            "severity": "info",
            "message": "autopep8 not installed; skipping auto-formatting.",
            "suggestion": "pip install autopep8",
        })

    report_text = _format_report(items)
    # deduplicate highlight lines and sort
    highlight_lines = sorted(set(n for n in highlight_lines if isinstance(n, int) and n > 0))

    # Optionally apply safe fixes
    if auto_fix:
        try:
            # apply fixer-based rules first
            from fixer import apply_fixes
            fixed_code2, fixes = apply_fixes(fixed_code)
            # record applied fixes into items and highlights
            for f in fixes:
                items.append({
                    "line": f.get("line", 0),
                    "severity": "info",
                    "message": f.get("message", "Applied automatic fix."),
                    "suggestion": f.get("replacement", ""),
                })
                highlight_lines.append(f.get("line", 0))
            applied_fixes = fixes
            fixed_code = fixed_code2
            # Now apply conservative interprocedural divisor guards for calls found earlier
            if calls_with_zero:
                # operate on the current fixed_code text
                text = fixed_code
                for fname, pname in set(calls_with_zero):
                    # find the function definition and insert a guard if not present
                    pattern = re.compile(rf"(^\s*def\s+{re.escape(fname)}\s*\([^\)]*\)\s*:)", re.M)
                    m = pattern.search(text)
                    if not m:
                        continue
                    def_line = m.group(1)
                    # determine indentation for body (assume next line indentation)
                    start = m.end()
                    # insert guard after the def line
                    # construct guard snippet
                    guard = f"\n    if {pname} == 0:\n        return None\n"
                    # avoid duplicating if a simple check already exists
                    # naive check: see if "if <pname> == 0" appears in function body
                    func_body_region = text[start: start + 500]
                    if re.search(rf"if\s+{re.escape(pname)}\s*==\s*0", func_body_region):
                        continue
                    text = text[:start] + guard + text[start:]
                    applied_fixes.append({'line': 0, 'message': f"Inserted guard for divisor '{pname}' in function '{fname}'", 'old': '', 'replacement': guard})
                fixed_code = text
            report_text = _format_report(items)
            highlight_lines = sorted(set(n for n in highlight_lines if isinstance(n, int) and n > 0))
        except Exception:
            # if fixer fails, just continue with autopep8 output
            applied_fixes = []

    return report_text, fixed_code, highlight_lines, applied_fixes
