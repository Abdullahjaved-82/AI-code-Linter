# AI Code Linter

A lightweight AI-assisted code linter with a PyQt5 GUI. This project provides a rule-based Python linter and a stub for future CodeBERT integration.

Getting started

1. Create a virtual environment and install dependencies:

```powershell
python -m venv .venv; .\.venv\\Scripts\\Activate.ps1; pip install -r requirements.txt
```

2. Run the app:

```powershell
python main.py
```

What changed in this commit

- `linter.py`: replaced pylint-based flow with AST-driven rule checks, returns (report_text, fixed_code, highlights).
- `ui/main_ui.py`: added Open/Clear buttons, made Analyze use the new analyzer signature, added simple line highlighting.
- `models/codebert_stub.py`: lazy-loading CodeBERT wrapper stub for future ML integration.
- `requirements.txt`: primary dependencies list.

Next steps

- Implement model-based classification head and optional fine-tuning.
- Add unit tests for `linter` rules and integration tests for the UI.
- Add packaging (PyInstaller) and PDF export for reports.

# AI Code Linter  

An intelligent code analysis tool powered by **NLP** and **transformer-based models** (e.g., CodeBERT).  
It automatically detects **bugs, bad practices, and potential improvements** in source code.  
Built with **Python** (PyQt5 for UI) and integrated with pre-trained ML models, this project aims to make coding **cleaner, smarter, and more efficient**.  

---

## ✨ Features
- 🔍 Automatic detection of syntax issues, bugs, and code smells  
- 🤖 Powered by CodeBERT and transformer models  
- 🖥️ Simple GUI built with PyQt5  
- ⚡ Suggestions for code quality improvement  
- 📂 Multi-language code support (extensible)  

---

## 📦 Installation  

1. Clone the repository  
   ```bash
   git clone https://github.com/your-username/ai-code-linter.git
   cd ai-code-linter

   See `PROJECT_SUMMARY.txt` for a concise project overview suitable for submission. If you need a PDF of the summary and have Python available, you can create one locally after installing `reportlab`:

   ```powershell
   pip install reportlab
   python -c "from reportlab.lib.pagesizes import letter; from reportlab.pdfgen import canvas; import sys
   f='PROJECT_SUMMARY.txt';c=canvas.Canvas('PROJECT_SUMMARY.pdf', pagesize=letter); text=c.beginText(40,750)
   open(f,'r',encoding='utf-8').read().splitlines();
   for i,line in enumerate(open(f,'r',encoding='utf-8')):
         text.textLine(line.rstrip())
         if (i+1)%60==0:
               c.drawText(text); c.showPage(); text=c.beginText(40,750)
   c.drawText(text); c.save()"
   ```

