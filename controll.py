import serial
from time import sleep
import datetime as dt
from matplotlib.animation import FuncAnimation
from matplotlib import pyplot as plt
import threading

#Connection to COM38
serialPort = serial.Serial(port ="COM38", baudrate = 115200, bytesize=8, timeout=2,stopbits=serial.STOPBITS_ONE)
serialString = ""

#Plot initiation
fig = plt.figure()
ax = fig.add_subplot(1,1,1)
xs = []
ys = []

#Parameters for the lowpass filter
T = 5
A = (1 - 1/T)
B = (1/T)
x = 0
rssiVal = -50
console_message = '';

#Plot parameters
def setparameters():
    plt.ylim(bottom=-90,top = -10)
    plt.grid(linestyle='-', linewidth=0.5)
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)
    plt.title('Signal strenght')
    plt.ylabel('rssi (dB)')
    plt.gca().get_lines()[0].set_color('blue')


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


def readValues():
        global rssiVal
        global console_message
        while(1):
                if(serialPort.in_waiting > 0):
                        serialString = serialPort.readline().decode('Ascii').replace('\r\n','')
                        if serialString.lstrip("-").isdigit():
                            rssiVal = float(serialString)
                        else:
                            console_message = serialString

#Thread to read console values as they come
t = threading.Thread(target=readValues)                                
t.start()

#Wait for the initial values
sleep(2)

ani = FuncAnimation(fig,animation,fargs=(xs,ys),interval=1000)
plt.show()