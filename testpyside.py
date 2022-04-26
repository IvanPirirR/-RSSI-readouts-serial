import sys
from tracemalloc import start, stop
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton
from PyQt5.QtGui import QPixmap
from matplotlib import image

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initializeUI()
    def initializeUI(self):
        self.setGeometry(200, 100, 200, 200)
        self.setWindowTitle("QLabel example")
        self.setUpMainWindow()
        self.setUpStopButton()
        self.setUpStartButton()
        self.show()
    def setUpMainWindow(self):
        hello_label = QLabel(self)
        hello_label.setText("Hello")
        hello_label.move(50,20)
    def setUpStopButton(self):
        stop_button=QPushButton(self)
        stop_button.setToolTip("Stop scanning")
        stop_button.move(50,140)
        stop_button.setText("Stop")
        stop_button.clicked.connect(self.stop_click)
    def setUpStartButton(self):
        start_button = QPushButton(self)
        start_button.setToolTip("Start (passive) scanning")
        start_button.move(50,100)
        start_button.setText("Start")
        start_button.clicked.connect(self.start_click)
    def start_click(self):
        print("Start")
    def stop_click(self):
        print("Stop")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())


