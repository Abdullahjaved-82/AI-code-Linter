import sys
from PyQt5.QtWidgets import QApplication
from linter import analyze_code
from ui.main_ui import CodeLinterUI

def main():
    app = QApplication(sys.argv)
    window = CodeLinterUI(analyze_callback=analyze_code)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
