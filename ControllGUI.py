import sys
from time import sleep
import serial
import datetime as dt
import threading
import queue
import csv
from matplotlib.animation import FuncAnimation
from PyQt5.QtWidgets import QDialog, QApplication, QPushButton, QGridLayout, QFrame, QLCDNumber, QLabel, QTextEdit
from PyQt5.QtGui import QColor, QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

#Gloval variables
console_message = ''
rssiVal = -40

#Setting queue
q1 = queue.Queue(30)
mutex = threading.Lock()

#Parameters for the lowpass filter
T = 5
A = (1 - 1/T)
B = (1/T)
x = 0

#Connection to COM38
serialPort = serial.Serial(port ="COM38", baudrate = 115200, bytesize=8, timeout=2,stopbits=serial.STOPBITS_ONE)
serialString = ""

#Plot initiation
xs = []
ys = []

#Function to change the name
def changeName(name):
    a = b'\x00'
    if len(name) > 8:
        print("Name too long")
    else:
        new_name = a + bytes('c','utf-8') + bytes(name,'utf-8') + a*(8-len(name))
        print(new_name)


#Class for the window
class MainWindow(QDialog):

    def __init__(self,parent=None):
        super(MainWindow, self).__init__(parent)
        self.figure = plt.figure()
        self.ax = self.figure.add_subplot(1,1,1)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.initializeUI()

    def initializeUI(self):
        self.setGeometry(200, 100, 820, 550)
        self.setWindowTitle("Display rssi value")
        self.setUpFrame()
        self.setUpMainLabel()
        self.setUpStopButton()
        self.setUpStartButton()
        self.setUpSaveButton()
        self.setUpUpdateButton()
        self.setUpNumber()
        self.setUpPlot()
        self.setUpTexbox()
        self.show()

    def setUpTexbox(self):
        text_label = QLabel(self)
        self.main_texbox = QTextEdit(self)
        text_label.setText("Name")
        self.main_texbox.setGeometry(50,200,116,25)
        text_label.setGeometry(10,200,100,25)
        name_button = QPushButton(self)
        name_button.setText("Change name")
        name_button.clicked.connect(self.name_click)
        self.main_layout.addWidget(name_button, 5,0,1,2)


    def setUpPlot(self):
        self.main_layout.addWidget(self.toolbar,0,2,1,1)
        self.main_layout.addWidget(self.canvas, 1,2,8,1)

    def setUpFrame(self):
        main_frame = QFrame(self)
        main_frame.setStyleSheet("Qwidget { background-color: %s}"% QColor(250,210,235,255).name())
        self.main_layout = QGridLayout()
        main_frame.setLayout(self.main_layout)

    def setUpNumber(self):
        self.number_display = QLCDNumber(self)
        self.number_display.display(0)
        self.number_display.setSegmentStyle(QLCDNumber.Flat)
        self.main_layout.addWidget(self.number_display, 0,1,1,1)

    def setUpMainLabel(self):
        name_label = QLabel(self)
        name_label.setFont(QFont('Arial',15))
        name_label.setText("rssi value:")
        self.main_layout.addWidget(name_label, 0,0,1,1)

    def setUpUpdateButton(self):
        update_button=QPushButton(self)
        update_button.setText("Update")
        self.main_layout.addWidget(update_button, 3,0,1,2)
        update_button.clicked.connect(self.update_click)

    def setUpSaveButton(self):
        save_button=QPushButton(self)
        save_button.setText("Save")
        self.main_layout.addWidget(save_button, 4,0,1,2)
        save_button.clicked.connect(self.save_click)

    def setUpStopButton(self):
        stop_button=QPushButton(self)
        stop_button.setToolTip("Stop scanning")
        self.main_layout.addWidget(stop_button, 2,0,1,2)
        stop_button.setText("Stop")
        stop_button.clicked.connect(self.stop_click)

    def setUpStartButton(self):
        start_button = QPushButton(self)
        start_button.setToolTip("Start (passive) scanning")
        self.main_layout.addWidget(start_button, 1,0,1,2)
        start_button.setText("Start")
        start_button.clicked.connect(self.start_click)

    def update_click(self):
        self.number_display.display(rssiVal)

    def name_click(self):
        changeName(self.main_texbox.toPlainText())

    def start_click(self):
        serialPort.write(bytes("1pxxxxxxxx",'utf-8'))
        print("Start")

    def stop_click(self):
        serialPort.write(bytes("1sxxxxxxxx",'utf-8'))
        print("Stop")

    def save_click(self):
        saveValues()
        print("Saved")


#Plot parameters
def setparameters():
    plt.ylim(bottom=-90,top = -10)
    plt.grid(linestyle='-', linewidth=0.5)
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)
    plt.title('Signal magnitude')
    plt.ylabel('rssi (dB)')
    plt.gca().get_lines()[0].set_color('blue')
    #plt.gca().invert_yaxis()


#Function for the animation
def animation(i,xs,ys):
        
        y = rssiVal

        #Lowpass filter
        global x
        if x == 0:
            x = y
        x = A*x + B*y

        #Add value to plot
        xs.append(dt.datetime.now().strftime('%H:%M:%S'))
        ys.append(x)
        xs = xs[-20:]
        ys = ys[-20:]
        main.ax.clear()
        main.ax.plot(xs,ys)
        #main.canvas.draw()

        #Set parameters
        setparameters()


#set up thread for reading the console
def readValues():
        global rssiVal
        global console_message
        while(1):
                if(serialPort.in_waiting > 0):
                        serialString = serialPort.readline().decode('Ascii').replace('\r\n','')
                        if serialString.lstrip("-").isdigit():
                            rssiVal = int(serialString)

                            mutex.acquire()
                            if(not q1.full()):
                                q1.put(rssiVal)
                            else:
                                q1.get()
                                q1.put(rssiVal)
                            mutex.release()

                        else:
                            console_message = serialString
                            print(console_message)

#Thread to read console values as they come
t = threading.Thread(target=readValues)                       
t.start()

#Save values inside the queue
def saveValues():
    filename = "new_savefile.csv"
    arr = []

    mutex.acquire()
    while not q1.empty():
        arr.append(q1.get())
    mutex.release()

    with open(filename, "w") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(arr)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    main = MainWindow()
    ani = FuncAnimation(main.figure,animation,fargs=(xs,ys),interval=1000)


    sys.exit(app.exec_())