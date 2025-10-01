"""Rule-based fixer utilities.

Implements safe, heuristic transforms to automatically correct common issues
and returns a list of applied fixes with locations and descriptions.
"""
import re
import ast
from typing import List, Dict, Tuple


def _apply_off_by_one(code: str) -> Tuple[str, List[Dict]]:
    """Fix patterns like range(len(x)+1) -> range(len(x)) and record fixes."""
    fixes: List[Dict] = []

    pattern = re.compile(r"range\s*\(\s*len\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)\s*\+\s*1\s*\)")

    def repl(match):
        var = match.group(1)
        orig = match.group(0)
        new = f"range(len({var}))"
        start = match.start()
        line = code.count('\n', 0, start) + 1
        fixes.append({
            "line": line,
            "message": "Off-by-one in range(len(...)+1) replaced with range(len(...)).",
            "original": orig,
            "replacement": new,
        })
        return new

    new_code, _ = pattern.subn(repl, code)
    return new_code, fixes


def _convert_index_loop_to_element_loop(code: str) -> Tuple[str, List[Dict]]:
    """Convert patterns like:
    for i in range(len(arr)):
        x += arr[i]
    into:
    for item in arr:
        x += item
    """
    fixes: List[Dict] = []

    simple_pattern = re.compile(
        r"(?m)^(?P<indent>[ \t]*)for\s+(?P<idx>[A-Za-z_][A-Za-z0-9_]*)\s+in\s+range\s*\(\s*len\s*\(\s*(?P<arr>[A-Za-z_][A-Za-z0-9_]*)\s*\)\s*\)\s*:\s*\n(?P<body>(?:^(?P=indent)[ \t]+.*\n?)+)",
    )

    def repl(m):
        indent = m.group('indent')
        idx = m.group('idx')
        arr = m.group('arr')
        body = m.group('body')

        # only apply if arr[idx] is used
        if not re.search(rf"\b{re.escape(arr)}\s*\[\s*{re.escape(idx)}\s*\]", body):
            return m.group(0)

        orig = m.group(0)
        start = m.start()
        line = code.count('\n', 0, start) + 1

        item_name = f"{arr}_item"
        new_body = re.sub(rf"\b{re.escape(arr)}\s*\[\s*{re.escape(idx)}\s*\]", item_name, body)
        new_header = f"{indent}for {item_name} in {arr}:\n"
        new = new_header + new_body

        fixes.append({
            "line": line,
            "message": "Converted index-based loop to element-based loop.",
            "original": orig,
            "replacement": new,
        })
        return new

    new_code, _ = simple_pattern.subn(repl, code)
    return new_code, fixes


def _replace_bare_except(code: str) -> Tuple[str, List[Dict]]:
    """Replace bare `except:` with `except Exception as e:`"""
    fixes: List[Dict] = []
    pattern = re.compile(r"(?m)^(?P<indent>[ \t]*)except\s*:\s*(?:\n|$)")

    def repl(m):
        indent = m.group('indent')
        orig = m.group(0)
        new = f"{indent}except Exception as e:\n"
        start = m.start()
        line = code.count('\n', 0, start) + 1
        fixes.append({
            "line": line,
            "message": "Replaced bare except with except Exception as e",
            "original": orig,
            "replacement": new,
        })
        return new

    new_code, _ = pattern.subn(repl, code)
    return new_code, fixes


def _convert_eq_none(code: str) -> Tuple[str, List[Dict]]:
    """Fix `== None` → `is None`, `!= None` → `is not None`."""
    fixes: List[Dict] = []
    pattern_eq = re.compile(r"\b([A-Za-z0-9_\.\)\]\}]+)\s*==\s*None\b")
    pattern_neq = re.compile(r"\b([A-Za-z0-9_\.\)\]\}]+)\s*!=\s*None\b")

    def repl_eq(m):
        orig = m.group(0)
        left = m.group(1)
        start = m.start()
        line = code.count('\n', 0, start) + 1
        new = f"{left} is None"
        fixes.append({
            "line": line,
            "message": "Replaced '== None' with 'is None'",
            "original": orig,
            "replacement": new,
        })
        return new

    def repl_neq(m):
        orig = m.group(0)
        left = m.group(1)
        start = m.start()
        line = code.count('\n', 0, start) + 1
        new = f"{left} is not None"
        fixes.append({
            "line": line,
            "message": "Replaced '!= None' with 'is not None'",
            "original": orig,
            "replacement": new,
        })
        return new

    code, _ = pattern_eq.subn(repl_eq, code)
    code, _ = pattern_neq.subn(repl_neq, code)
    return code, fixes


def attempt_syntax_fixes(code: str) -> Tuple[str, List[Dict]]:
    """Insert missing colons at simple block headers."""
    lines = code.splitlines()
    fixes: List[Dict] = []
    changed = False

    patterns = ("def ", "if ", "for ", "while ", "class ", "elif ", "else", "try", "except", "with ")

    for idx, line in enumerate(lines):
        stripped = line.rstrip()
        if not stripped or stripped.endswith(":"):
            continue
        for p in patterns:
            if stripped.lstrip().startswith(p):
                old = lines[idx]
                lines[idx] = lines[idx] + ':'
                fixes.append({
                    'line': idx + 1,
                    'message': 'Inserted missing colon at end of block header',
                    'original': old,
                    'replacement': lines[idx],
                })
                changed = True
                break

    if not changed:
        return code, []

    new_code = '\n'.join(lines) + ('\n' if code.endswith('\n') else '')
    try:
        ast.parse(new_code)
        return new_code, fixes
    except Exception:
        return code, []


def apply_fixes(code: str) -> Tuple[str, List[Dict]]:
    """Apply all fixes and return (new_code, fixes)."""
    all_fixes: List[Dict] = []
    new_code = code

    try:
        new_code, fixes = _apply_off_by_one(new_code)
        all_fixes.extend(fixes)
    except Exception:
        pass

    try:
        new_code, fixes = _convert_index_loop_to_element_loop(new_code)
        all_fixes.extend(fixes)
    except Exception:
        pass

    try:
        new_code, fixes = _replace_bare_except(new_code)
        all_fixes.extend(fixes)
    except Exception:
        pass

    try:
        new_code, fixes = _convert_eq_none(new_code)
        all_fixes.extend(fixes)
    except Exception:
        pass

    try:
        new_code, fixes = attempt_syntax_fixes(new_code)
        all_fixes.extend(fixes)
    except Exception:
        pass

    return new_code, all_fixes


__all__ = ["apply_fixes", "attempt_syntax_fixes"]
