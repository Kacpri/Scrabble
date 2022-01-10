from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class TableView(QTableWidget):
    def __init__(self, data, *args):
        QTableWidget.__init__(self, *args)
        self.setShowGrid(True)
        self.setCornerButtonEnabled(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.rows, self.columns = args
        self.data = data
        self.data.bind_to(self.add_value)
        self.count = 0
        # self.set_headers()
        self.init_rows()

    def set_headers(self):
        self.setHorizontalHeaderLabels(self.data.get_player_names())

    def init_rows(self):
        for count in range(self.columns * self.rows):
            self.add_value("")
        self.count = 0

    def add_value(self, value):
        item = QTableWidgetItem(str(value))
        item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        item.setFlags(item.flags() ^ (Qt.ItemIsEditable | Qt.ItemIsSelectable))
        row = int(self.count / 2)
        column = self.count % 2
        self.setItem(row, column, item)
        self.count += 1


