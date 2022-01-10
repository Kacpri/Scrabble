import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from board import Board
from table_view import TableView
from score import Score
from clock import Clock


class MyWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.player_name = 'Gracz'
        self.score = Score()

        self.font = QFont('Calibri', 15)

        self.table = TableView(self.score, 23, 2)
        self.table.setFixedWidth(230)

        self.table_dock_widget = QDockWidget('Wyniki')
        self.table_dock_widget.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.table_dock_widget.setFixedWidth(230)
        self.table_dock_widget.setTitleBarWidget(QWidget())
        self.table_dock_widget.setWidget(self.table)

        self.left_widget = QWidget()

        self.left_layout = QVBoxLayout()

        self.player_label = QLabel('Gracz')
        self.player_label.setText('Gracz')
        self.player_label.setAlignment(Qt.AlignLeft)
        # player_label.setFont(font)

        self.player_clock = Clock()
        self.player_clock.set_time(15)
        self.player_clock.setAlignment(Qt.AlignRight)
        self.player_clock.setFont(self.font)

        self.player_widget = QWidget()
        self.player_layout = QHBoxLayout()
        self.player_layout.addWidget(self.player_label)
        self.player_layout.addWidget(self.player_clock)
        self.player_widget.setLayout(self.player_layout)

        self.ai_label = QLabel('AI')
        self.ai_label.setText('AI')
        self.ai_label.setAlignment(Qt.AlignLeft)
        # ai_label.setFont(font)

        self.ai_clock = Clock()
        self.ai_clock.set_time(15)
        self.ai_clock.setAlignment(Qt.AlignRight)
        self.ai_clock.setFont(self.font)

        self.ai_widget = QWidget()
        self.ai_layout = QHBoxLayout()
        self.ai_layout.addWidget(self.ai_label)
        self.ai_layout.addWidget(self.ai_clock)
        self.ai_widget.setLayout(self.ai_layout)

        self.information_label = QLabel('Podaj swoje imię:')
        self.information_label.setGeometry(200, 250, 100, 50)
        self.information_label.setWordWrap(True)

        self.textfield = QLineEdit()
        self.confirm_button = QPushButton('Potwierdź')

        self.confirm_button.clicked.connect(self.confirm_button_clicked)
        self.textfield.returnPressed.connect(self.confirm_button.click)

        self.board = Board(self.score, self.player_clock, self.ai_clock, self.information_label.setText)
        self.board.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.board.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.end_turn_button = QPushButton('Zakończ ruch')

        self.end_turn_button.setDisabled(True)

        self.exchange_letters_button = QPushButton('Wymień litery')

        self.exchange_letters_button.setDisabled(True)

        self.start_button = QPushButton('Rozpocznij grę')

        self.resign_button = QPushButton('Poddaj się')
        self.resign_button.setDisabled(True)

        self.end_turn_button.clicked.connect(self.board.end_turn)

        self.exchange_letters_button.clicked.connect(self.board.exchange_letters)

        self.start_button.clicked.connect(self.start_button_clicked)

        self.resign_button.clicked.connect(self.board.resign)
        self.resign_button.clicked.connect(lambda: self.ai_clock.set_time(15))
        self.resign_button.clicked.connect(lambda: self.player_clock.set_time(15))
        self.resign_button.clicked.connect(lambda: self.start_button.setDisabled(False))
        self.resign_button.clicked.connect(lambda: self.end_turn_button.setDisabled(True))
        self.resign_button.clicked.connect(lambda: self.exchange_letters_button.setDisabled(True))
        self.resign_button.clicked.connect(lambda: self.resign_button.setDisabled(True))

        self.left_layout.addWidget(self.player_widget)
        self.left_layout.addWidget(self.ai_widget)
        self.left_layout.addStretch()
        self.left_layout.addWidget(self.information_label)
        self.left_layout.addWidget(self.textfield)
        self.left_layout.addWidget(self.confirm_button)
        self.left_layout.addStretch()
        self.left_layout.addWidget(self.start_button)
        self.left_layout.addWidget(self.end_turn_button)
        self.left_layout.addWidget(self.exchange_letters_button)
        self.left_layout.addWidget(self.resign_button)

        # layout.addWidget(player_clock)
        # layout.addWidget(ai_clock)

        self.left_widget.setLayout(self.left_layout)
        self.left_dock_widget = QDockWidget()
        self.left_dock_widget.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.left_dock_widget.setTitleBarWidget(QWidget())
        self.left_dock_widget.setFixedWidth(218)
        self.left_dock_widget.setWidget(self.left_widget)

        self.setCentralWidget(self.board)
        self.addDockWidget(Qt.RightDockWidgetArea, self.table_dock_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.left_dock_widget)

        width = self.board.width() + self.table_dock_widget.width() + self.left_dock_widget.width()
        height = int(self.board.height() * 1.6)

        self.setFixedSize(width, height)

    def confirm_button_clicked(self):
        new_name = self.textfield.text()
        if not new_name:
            return
        self.player_name = new_name
        self.player_label.setText(self.player_name)

    def start_button_clicked(self):
        self.start_button.setDisabled(True)
        self.end_turn_button.setDisabled(False)
        self.exchange_letters_button.setDisabled(False)
        self.resign_button.setDisabled(False)
        self.table.set_headers()
        is_ai_turn = self.board.start_game()
        players = [self.player_name, 'AI']
        if is_ai_turn:
            players = reversed(players)
        self.score.set_players(players)
        self.table.set_headers()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName('Scrabble')

    main = MyWindow()
    main.show()

    sys.exit(app.exec_())
