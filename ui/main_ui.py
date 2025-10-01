from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel,
    QFileDialog, QSplitter, QListWidget, QProgressBar, QToolBar, QAction, QStatusBar
)
from PyQt5.QtGui import (
    QTextCursor, QTextCharFormat, QColor, QFont, QIcon, QSyntaxHighlighter, QTextCharFormat
)
from PyQt5.QtCore import Qt, QRegExp
import re


class PythonHighlighter(QSyntaxHighlighter):
    """Basic Python syntax highlighter for QTextEdit."""
    def __init__(self, parent):
        super().__init__(parent.document())
        self._highlighting_rules = []
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor('#569CD6'))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            'def', 'class', 'if', 'elif', 'else', 'try', 'except', 'finally', 'for', 'while', 'return', 'import', 'from', 'as', 'with', 'lambda', 'pass', 'yield', 'raise'
        ]
        for kw in keywords:
            pattern = QRegExp(r"\b" + kw + r"\b")
            self._highlighting_rules.append((pattern, keyword_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor('#CE9178'))
        self._highlighting_rules.append((QRegExp(r"\".*\""), string_format))
        self._highlighting_rules.append((QRegExp(r"\'.*\'"), string_format))

        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor('#6A9955'))
        self._highlighting_rules.append((QRegExp(r"#.*"), comment_format))

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._highlighting_rules:
            i = pattern.indexIn(text)
            while i >= 0:
                length = pattern.matchedLength()
                self.setFormat(i, length, fmt)
                i = pattern.indexIn(text, i + length)


class CodeLinterUI(QWidget):
    def __init__(self, analyze_callback):
        super().__init__()
        self.setWindowTitle("AI Code Linter — Semester Project")
        self.resize(1000, 700)

        # Main layout
        main_layout = QVBoxLayout()

        # Toolbar
        toolbar = QToolBar()
        open_action = QAction("Open", self)
        save_action = QAction("Save", self)
        analyze_action = QAction("Analyze", self)
        clear_action = QAction("Clear", self)
        quickfix_action = QAction("Quick Fix", self)
        theme_action = QAction("Toggle Theme", self)
        model_action = QAction("Use Model", self)
        model_action.setCheckable(True)

        toolbar.addAction(open_action)
        toolbar.addAction(save_action)
        toolbar.addAction(analyze_action)
        toolbar.addAction(quickfix_action)
        toolbar.addAction(clear_action)
        toolbar.addAction(model_action)
        toolbar.addSeparator()
        toolbar.addAction(theme_action)

        open_action.triggered.connect(self.open_file)
        save_action.triggered.connect(self.save_corrected_code)
        analyze_action.triggered.connect(self.run_analysis)
        quickfix_action.triggered.connect(self.run_quick_fix)
        clear_action.triggered.connect(self.clear_all)
        theme_action.triggered.connect(self.toggle_theme)
        model_action.triggered.connect(self.toggle_model)

        main_layout.addWidget(toolbar)

        # Splitter: editor | results
        splitter = QSplitter(Qt.Horizontal)

        # Left: Editor + corrected code (stacked)
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)

        label = QLabel("Enter or paste your code:")
        left_layout.addWidget(label)

        self.code_input = QTextEdit()
        self.code_input.setFont(QFont('Consolas', 11))
        left_layout.addWidget(self.code_input)

        corrected_label = QLabel("Corrected / Fixed Code (editable):")
        left_layout.addWidget(corrected_label)
        self.fixed_output = QTextEdit()
        self.fixed_output.setFont(QFont('Consolas', 11))
        left_layout.addWidget(self.fixed_output)

        splitter.addWidget(left_widget)

        # Right: results and suggestions
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)

        results_label = QLabel("Analysis Report:")
        right_layout.addWidget(results_label)

        self.result_output = QTextEdit()
        self.result_output.setReadOnly(True)
        self.result_output.setFont(QFont('Segoe UI', 10))
        right_layout.addWidget(self.result_output)

        suggestions_label = QLabel("Suggestions / Quick Tips:")
        right_layout.addWidget(suggestions_label)
        self.suggestions = QListWidget()
        right_layout.addWidget(self.suggestions)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

        # Status bar
        self.status = QStatusBar()
        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.status.addPermanentWidget(self.progress)
        main_layout.addWidget(self.status)

        self.setLayout(main_layout)

        # Highlighter
        self.highlighter = PythonHighlighter(self.code_input)

        # state
        self.dark = False
        self.analyze_callback = analyze_callback
        self.use_model = False
        self.last_applied_fixes = []

    def run_analysis(self):
        code = self.code_input.toPlainText()
        if not code.strip():
            self.result_output.setText("⚠️ Please enter some code first.")
            self.fixed_output.setPlainText("")
            return

        self.status.showMessage("Analyzing...")
        self.progress.setValue(10)

        try:
            # analyzer may return 3- or 4-tuple depending on auto_fix
            result = self.analyze_callback(code)
        except Exception as e:
            self.result_output.setText(f"Error during analysis: {e}")
            self.progress.setValue(0)
            self.status.showMessage("Ready")
            return

        # handle outputs
        if isinstance(result, tuple) and len(result) == 3:
            report_text, fixed_code, highlights = result
        elif isinstance(result, tuple) and len(result) == 2:
            report_text, fixed_code = result
            highlights = []
        else:
            report_text = str(result)
            fixed_code = ""
            highlights = []

        self.result_output.setPlainText(report_text)
        self.fixed_output.setPlainText(fixed_code)
        self.suggestions.clear()
        # add first few suggestion lines as items
        for line in report_text.splitlines()[:10]:
            self.suggestions.addItem(line)

        self.highlight_lines(highlights)
        self.progress.setValue(100)
        self.status.showMessage("Analysis complete.")

    def run_quick_fix(self):
        code = self.code_input.toPlainText()
        if not code.strip():
            self.result_output.setText("⚠️ Please enter some code first.")
            return

        self.status.showMessage("Applying quick fixes...")
        self.progress.setValue(5)
        try:
            # analyze_code now supports auto_fix flag and returns fixes
            result = self.analyze_callback(code, True)
        except TypeError:
            # backward compatibility: if analyze_callback doesn't accept auto_fix
            result = self.analyze_callback(code)

        # result expected: report, fixed_code, highlights, applied_fixes
        if isinstance(result, tuple) and len(result) == 4:
            report_text, fixed_code, highlights, applied_fixes = result
        elif isinstance(result, tuple) and len(result) == 3:
            report_text, fixed_code, highlights = result
            applied_fixes = []
        else:
            report_text = str(result)
            fixed_code = ""
            highlights = []
            applied_fixes = []

        self.result_output.setPlainText(report_text)
        self.fixed_output.setPlainText(fixed_code)
        self.suggestions.clear()
        self.last_applied_fixes = applied_fixes or []
        for f in applied_fixes:
            item_text = f"Line {f.get('line', '?')}: {f.get('message', '')}\n- {f.get('old','')}\n+ {f.get('replacement','')}"
            item = self.suggestions.addItem(item_text)

        self.highlight_lines(highlights)
        self.progress.setValue(100)
        self.status.showMessage("Quick fix applied.")

    def apply_selected_fix(self):
        sel = self.suggestions.currentItem()
        if not sel:
            self.status.showMessage('No fix selected')
            return
        idx = self.suggestions.currentRow()
        if idx < 0 or idx >= len(self.last_applied_fixes):
            self.status.showMessage('Invalid selection')
            return
        fix = self.last_applied_fixes[idx]
        # apply line replacement conservatively
        lines = self.code_input.toPlainText().splitlines()
        ln = fix.get('line', 0)
        if 1 <= ln <= len(lines):
            lines[ln-1] = fix.get('replacement', lines[ln-1])
            self.code_input.setPlainText('\n'.join(lines))
            self.status.showMessage(f"Applied fix on line {ln}")
        else:
            # fallback: global replace old->replacement
            new_text = self.code_input.toPlainText().replace(fix.get('old',''), fix.get('replacement',''))
            self.code_input.setPlainText(new_text)
            self.status.showMessage('Applied fix by global replace')

    def accept_all_fixes(self):
        # Replace editor content with fixed output
        fixed = self.fixed_output.toPlainText()
        if fixed:
            self.code_input.setPlainText(fixed)
            self.status.showMessage('Accepted all fixes (replaced editor content)')
            self.suggestions.clear()
            self.last_applied_fixes = []

    def reject_all_fixes(self):
        self.suggestions.clear()
        self.status.showMessage('Rejected all fixes')
        self.last_applied_fixes = []

    def toggle_model(self, checked: bool):
        self.use_model = bool(checked)
        self.status.showMessage(f"Model {'enabled' if self.use_model else 'disabled'}")

    def save_corrected_code(self):
        corrected_code = self.fixed_output.toPlainText()
        if not corrected_code.strip():
            self.result_output.setText("⚠️ No corrected code to save.")
            return

        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Corrected Code",
            "corrected_code.py",
            "Python Files (*.py);;All Files (*)",
            options=options
        )
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(corrected_code)
                self.status.showMessage(f"Saved: {filename}")
            except Exception as e:
                self.status.showMessage(f"Error saving file: {e}")

    def open_file(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open Source File",
            "",
            "Python Files (*.py);;All Files (*)",
            options=options
        )
        if filename:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    self.code_input.setPlainText(f.read())
                self.status.showMessage(f"Loaded: {filename}")
            except Exception as e:
                self.status.showMessage(f"Error opening file: {e}")

    def clear_all(self):
        self.code_input.clear()
        self.result_output.clear()
        self.fixed_output.clear()
        self.suggestions.clear()
        self.code_input.setExtraSelections([])
        self.status.showMessage("Cleared")

    def highlight_lines(self, lines: list):
        # Use QTextEdit extra selections for non-destructive highlighting
        selections = []
        warn_fmt = QTextCharFormat()
        warn_fmt.setBackground(QColor('#fff0b3'))

        err_fmt = QTextCharFormat()
        err_fmt.setBackground(QColor('#ffcccc'))

        for ln in (lines or []):
            if not isinstance(ln, int) or ln <= 0:
                continue
            block = self.code_input.document().findBlockByNumber(ln - 1)
            if not block.isValid():
                continue
            sel = QTextEdit.ExtraSelection()
            cursor = QTextCursor(block)
            cursor.select(QTextCursor.LineUnderCursor)
            sel.cursor = cursor
            # For now use warning color for all
            sel.format = warn_fmt
            selections.append(sel)

        self.code_input.setExtraSelections(selections)

    def toggle_theme(self):
        if not self.dark:
            # simple dark theme
            self.setStyleSheet("QWidget { background: #1e1e1e; color: #d4d4d4 } QTextEdit { background: #252526; color: #d4d4d4 }")
            self.dark = True
        else:
            self.setStyleSheet("")
            self.dark = False
