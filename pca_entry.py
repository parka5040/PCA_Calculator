from src.pca_gui import PCACalculatorApp
from PyQt6.QtWidgets import QApplication
import sys

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PCACalculatorApp()
    window.show()
    sys.exit(app.exec())