import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from board import Board
from table_view import TableView
from score import Score


def main():
    app = QApplication(sys.argv)
    players = ['Gracz', 'AI']
    score = Score(players)
    board = Board(score)
    main_window = QMainWindow()
    main_window.setCentralWidget(board)

    button = QPushButton('Zakończ ruch')
    button.clicked.connect(board.end_turn)
    button.setStyleSheet("QPushButton { background-color: grey; color: white; font-size: 20px; "
                         "margin-bottom: 4px; margin-left: 400px; margin-right: 400px;"
                         "padding: 3px}"
                         "QPushButton:hover { background-color: #333333 }"
                         "QPushButton:pressed { background-color: black }")
    button.resize(200, 200)

    button_dock_widget = QDockWidget()
    button_dock_widget.setFeatures(QDockWidget.NoDockWidgetFeatures)
    button_dock_widget.setTitleBarWidget(QWidget())
    button_dock_widget.setWidget(button)
    table = TableView(score, 23, 2)
    table.setFixedWidth(230)

    table_dock_widget = QDockWidget('Wyniki')
    table_dock_widget.setFeatures(QDockWidget.NoDockWidgetFeatures)
    table_dock_widget.setFixedWidth(230)
    table_dock_widget.setTitleBarWidget(QWidget())
    table_dock_widget.setWidget(table)

    third_dock_widget = QDockWidget()
    third_dock_widget.setFeatures(QDockWidget.NoDockWidgetFeatures)
    third_dock_widget.setTitleBarWidget(QWidget())
    third_dock_widget.setFixedWidth(218)

    main_window.addDockWidget(Qt.BottomDockWidgetArea, button_dock_widget)
    main_window.addDockWidget(Qt.RightDockWidgetArea, table_dock_widget)
    main_window.addDockWidget(Qt.LeftDockWidgetArea, third_dock_widget)

    width = board.width() + table_dock_widget.width() + third_dock_widget.width()
    height = int(board.height() * 1.6)

    main_window.setFixedSize(width, height)
    main_window.show()
    # main.showMaximized()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
