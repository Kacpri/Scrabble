from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import QTimer, QTime


class Clock(QLabel):

    def __init__(self):
        super().__init__()
        self.time_left = QTime(0, 0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)

        self.is_paused = True
        self.is_set = False

    def set_time(self, minutes, seconds=0):
        self.stop()
        self.time_left = QTime(0, minutes, seconds)
        self.setText(self.time_left.toString('mm:ss'))
        self.is_set = True
        self.setStyleSheet('')

    def start(self):
        if self.is_paused and self.is_set:
            self.timer.start(1000)
            self.is_paused = False

    def stop(self):
        if not self.is_paused:
            self.timer.stop()
            self.is_paused = True

    def update_time(self):
        self.time_left = self.time_left.addSecs(-1)
        if self.time_left.minute() == 0 and self.time_left.second() == 0:
            self.stop()
            self.is_set = False
            self.setStyleSheet('QLabel { color: red}')
        self.setText(self.time_left.toString('mm:ss'))
