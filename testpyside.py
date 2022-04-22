import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtGui import QPixmap
from matplotlib import image

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initializeUI()
    def initializeUI(self):
        self.setGeometry(200, 100, 400, 300)
        self.setWindowTitle("QLabel example")
        self.setUpMainWindow()
        self.show()
    def setUpMainWindow(self):
        hello_label = QLabel(self)
        hello_label.setText("Hello")
        hello_label.move(105,15)
        image = "images/world.png"
        try:
            with open(image):
                world_label = QLabel(self)
                pixmap = QPixmap(image)
                world_label.setPixmap(pixmap)
                world_label.move(25,40)
        except FileNotFoundError as error:
            print(f'Image not found. \nError: {error}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())


