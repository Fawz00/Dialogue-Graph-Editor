import sys
import time
from PyQt6.QtWidgets import QApplication, QLabel
from PyQt6.QtCore import QThread, QTimer


latest_value = 0


class Worker(QThread):
    def run(self):
        global latest_value

        counter = 0

        while True:
            counter += 1
            latest_value = counter


app = QApplication(sys.argv)

label = QLabel()
label.resize(400, 100)
label.show()


worker = Worker()
worker.start()


def update_gui():
    label.setText(str(latest_value))


timer = QTimer()
timer.timeout.connect(update_gui)
timer.start(16)  # 60Hz GUI update


sys.exit(app.exec())