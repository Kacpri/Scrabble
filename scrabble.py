from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QScrollArea, QLineEdit, \
    QPushButton, QDockWidget

from board import Board
from score_view import ScoreView
from score import Score
from clock import Clock
from math import sqrt


class Scrabble(QMainWindow):
    def __init__(self, parent=None):
        super(Scrabble, self).__init__(parent)
        self.score = Score()
        self.player_name = 'Gracz'
        self.is_game_started = False

        self.turn_buttons = []
        self.other_widgets = []
        self.button_size = 40
        self.font_size = 12
        self.timer_font_size = 15

        self.right_table = ScoreView(self.score, 'SI z ewaluacją', 0, 3)
        self.left_table = ScoreView(self.score, 'SI bez ewaluacji', 0, 3)

        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout()

        self.player_label = QLabel('SI bez ewaluacji')

        self.player_clock = Clock()
        self.player_clock.set_time(15)

        self.player_widget = QWidget()
        self.player_layout = QHBoxLayout()
        self.player_layout.addWidget(self.player_label, alignment=Qt.AlignLeft)
        self.player_layout.addWidget(self.player_clock, alignment=Qt.AlignRight)
        self.player_widget.setLayout(self.player_layout)

        self.ai_label = QLabel('SI z ewaluacją')

        self.ai_clock = Clock()
        self.ai_clock.set_time(15)
        self.ai_clock.setAlignment(Qt.AlignRight)

        self.ai_widget = QWidget()
        self.ai_layout = QHBoxLayout()
        self.ai_layout.addWidget(self.ai_label, alignment=Qt.AlignLeft)
        self.ai_layout.addWidget(self.ai_clock, alignment=Qt.AlignRight)
        self.ai_widget.setLayout(self.ai_layout)

        self.sack_label = QLabel('Litery w worku:')

        self.sack_counter = QLabel('100')

        self.sack_widget = QWidget()
        self.sack_layout = QHBoxLayout()
        self.sack_layout.addWidget(self.sack_label, alignment=Qt.AlignLeft)
        self.sack_layout.addWidget(self.sack_counter, alignment=Qt.AlignRight)
        self.sack_widget.setLayout(self.sack_layout)

        self.information_area = QScrollArea()
        self.information_area.setWidgetResizable(True)
        self.information_area.verticalScrollBar().rangeChanged.connect(self.set_to_max_value)

        self.information_label = QLabel('Witaj, jak masz na imię?')
        self.information_label.setAlignment(Qt.AlignTop)
        self.information_label.setWordWrap(True)
        self.information_label.setMargin(5)

        self.information_area.setWidget(self.information_label)

        self.prompt_label = QLabel('Przedstaw się')
        self.other_widgets.append(self.prompt_label)

        self.start_resign_button = QPushButton('Rozpocznij grę', self)

        self.start_resign_button.clicked.connect(self.start_resign_button_clicked)

        self.board = Board(self.score, self.player_clock, self.ai_clock, self.add_info, self.prompt_label.setText,
                           self.sack_counter.setText)

        self.right_layout.addWidget(self.player_widget)
        self.right_layout.addWidget(self.left_table)
        self.right_layout.addWidget(self.ai_widget)
        self.right_layout.addWidget(self.right_table)
        self.right_layout.addWidget(self.sack_widget)
        self.right_layout.addWidget(self.start_resign_button)

        self.right_widget.setLayout(self.right_layout)
        self.right_dock_widget = QDockWidget()
        self.right_dock_widget.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.right_dock_widget.setTitleBarWidget(QWidget())
        self.right_dock_widget.setFixedWidth(300)
        self.right_dock_widget.setWidget(self.right_widget)

        self.setCentralWidget(self.board)
        self.addDockWidget(Qt.RightDockWidgetArea, self.right_dock_widget)

    def add_info(self, info):
        current = self.information_label.text()
        new = current + '\n\n' + info
        self.information_label.setText(new)

    def set_to_max_value(self):
        self.information_area.verticalScrollBar().setValue(self.information_area.verticalScrollBar().maximum())

    def start_resign_button_clicked(self):
        if self.is_game_started:
            self.setCentralWidget(self.board)
            self.ai_clock.set_time(15)
            self.player_clock.set_time(15)
            self.right_table.clear_rows()
            self.left_table.clear_rows()
            self.is_game_started = False
            self.start_resign_button.setText('Rozpocznij grę')
            self.board.score.clear()
            self.board.reset_game()
        else:
            self.is_game_started = True
            self.start_resign_button.setText('Poddaj się')
            self.board.start_game()

    def resizeEvent(self, event):
        if self.board:
            self.board.auto_resize()
        font_size = round(sqrt(self.height() // 10))
        if self.font_size != font_size:
            self.font_size = font_size
            timer_font_size = round(self.font_size * 1.5)

            self.setFont(QFont('Verdana', self.font_size))
            self.player_clock.setFont(QFont('Verdana', timer_font_size))
            self.ai_clock.setFont(QFont('Verdana', timer_font_size))
            self.sack_counter.setFont(QFont('Verdana', timer_font_size))

            self.right_table.resizeRowsToContents()
            self.left_table.resizeRowsToContents()

        button_size = round(sqrt(self.height()))
        if self.button_size != button_size:
            self.button_size = button_size
            for button in self.turn_buttons + self.other_widgets:
                button.setFixedHeight(self.button_size)

        QMainWindow.resizeEvent(self, event)
