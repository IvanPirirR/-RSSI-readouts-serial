import serial
import datetime as dt
from matplotlib.animation import FuncAnimation
from matplotlib import pyplot as plt
import threading
import queue
import csv
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QLCDNumber, QFrame, QGridLayout, QMainWindow
from PyQt5.QtGui import QFont, QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

#Gloval variables
console_message = ''
rssiVal = None

#Setting queue
q1 = queue.Queue(30)
mutex = threading.Lock()

#Connection to COM38
serialPort = serial.Serial(port ="COM38", baudrate = 115200, bytesize=8, timeout=2,stopbits=serial.STOPBITS_ONE)
serialString = ""

#Plot initiation
fig = plt.figure()
ax = fig.add_subplot(1,1,1)
xs = []
ys = []


#Class for the window
class MainWindow(QMainWindow):

    def __init__(self,parent=None):
        super(MainWindow, self).__init__(parent)
        self.initializeUI()

    def initializeUI(self):
        #self.setGeometry(200, 100, 250, 200)
        self.setWindowTitle("Display rssi value")
        self.setUpFrame()
        self.setUpMainWindow()
        self.setUpStopButton()
        self.setUpStartButton()
        self.setUpSaveButton()
        self.setUpUpdateButton()
        self.setUpNumber()
        self.show()

    def setUpFrame(self):
        main_frame = QFrame(self)
        main_frame.setStyleSheet("Qwidget { background-color: %s}"% QColor(210,210,235,255).name())
        self.main_layout = QGridLayout()
        main_frame.setLayout(self.main_layout)
        self.setCentralWidget(main_frame)

    def setUpNumber(self):
        self.number_display = QLCDNumber(self)
        self.number_display.move(120,20)
        self.number_display.display(0)
        self.number_display.setSegmentStyle(QLCDNumber.Flat)
        self.main_layout.addWidget(self.number_display, *(1,0))

    def setUpMainWindow(self):
        name_label = QLabel(self)
        name_label.setFont(QFont('Arial',15))
        name_label.setText("rssi value:")
        name_label.move(50,25)
        self.main_layout.addWidget(name_label, *(0,0))

    def setUpUpdateButton(self):
        update_button=QPushButton(self)
        update_button.setText("Update")
        #update_button.move(80,130)
        self.main_layout.addWidget(update_button, *(4,0))
        update_button.clicked.connect(self.update_click)

    def setUpSaveButton(self):
        save_button=QPushButton(self)
        save_button.setText("Save")
        #save_button.move(80,160)
        self.main_layout.addWidget(save_button, *(5,0))
        save_button.clicked.connect(self.save_click)

    def setUpStopButton(self):
        stop_button=QPushButton(self)
        stop_button.setToolTip("Stop scanning")
        #stop_button.move(80,100)
        self.main_layout.addWidget(stop_button, *(3,0))
        stop_button.setText("Stop")
        stop_button.clicked.connect(self.stop_click)

    def setUpStartButton(self):
        start_button = QPushButton(self)
        start_button.setToolTip("Start (passive) scanning")
        #start_button.move(80,70)
        self.main_layout.addWidget(start_button, *(2,0))
        start_button.setText("Start")
        start_button.clicked.connect(self.start_click)

    def update_click(self):
        self.number_display.display(rssiVal)

    def start_click(self):
        serialPort.write(bytes("1ptestname",'utf-8'))
        print("Start")

    def stop_click(self):
        serialPort.write(bytes("1stestname",'utf-8'))
        print("Stop")

    def save_click(self):
        saveValues()
        print("Saved")


#Parameters for the lowpass filter
T = 5
A = (1 - 1/T)
B = (1/T)
x = 0

#Plot parameters
def setparameters():
    plt.ylim(bottom=-90,top = -10)
    plt.grid(linestyle='-', linewidth=0.5)
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)
    plt.title('Signal strenght')
    plt.ylabel('rssi (dB)')
    plt.gca().get_lines()[0].set_color('blue')
    plt.gca().invert_yaxis()


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
        ax.clear()
        ax.plot(xs,ys)

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
                            rssiVal = float(serialString)

                            mutex.acquire()
                            if(not q1.full()):
                                q1.put(rssiVal)
                            else:
                                q1.get()
                                q1.put(rssiVal)
                            mutex.release()

                        else:
                            console_message = serialString


#Thread to read console values as they come
t = threading.Thread(target=readValues)                                
t.start()

#ani = FuncAnimation(fig,animation,fargs=(xs,ys),interval=1000)
#plt.show()

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

    #Plot initiation
    #plt.show()

    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
