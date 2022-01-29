from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class TableView(QTableWidget):
    def __init__(self, score, player, *args):
        QTableWidget.__init__(self, *args)
        self.rows, self.columns = args
        self.player = player
        self.setShowGrid(True)
        self.setCornerButtonEnabled(False)

        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.setHorizontalHeaderLabels(['słowa', 'pkt.', 'suma'])
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

        self.verticalScrollBar().rangeChanged.connect(self.set_to_max_value)

        self.score = score
        self.score.bind_to(self.submit_turn, player)
        self.count = 0
        self.resizeRowsToContents()

    def clear_rows(self):
        for _ in range(self.rows):
            self.removeRow(0)

    def add_item(self, value):
        if not self.count % 3:
            self.insertRow(self.count // 3)
            self.rows += 1
        item = QTableWidgetItem(str(value))
        item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        item.setFlags(item.flags() ^ (Qt.ItemIsEditable | Qt.ItemIsSelectable))
        # item.setFont(self.font)
        row = self.count // self.columns
        column = self.count % self.columns
        self.setItem(row, column, item)
        self.count += 1

    def submit_turn(self, message, points, total_points):
        if type(message) is list:
            words = ''
            for word in message:
                words += f'{word}, '
            message = words[:-2]
        self.add_item(message)
        self.add_item(points)
        self.add_item(total_points)
        self.resizeRowsToContents()

    def set_to_max_value(self):
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
