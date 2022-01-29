import sys
from PyQt5.QtWidgets import QApplication
from scrabble import Scrabble

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName('Scrabble')

    main = Scrabble()
    main.showMaximized()
    sys.exit(app.exec_())
