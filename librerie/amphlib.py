from math import cos as cos, sin as sin, acos as acos, pi as pi, sqrt as sqrt, pow as pow
import sys, glob, serial
from PyQt4 import QtCore, QtGui, uic
import binascii

info = 'Amphitrite 2.0'

def deg2rad(deg):
    return deg*pi/180

def rad2deg(rad):
    return rad/pi*180

def appWind(Vw, Vs, alpha, teta): #wind real speed, ship speed, wind real direction, ship direction in degrees
    alpha = deg2rad(alpha-teta) #relative angle (absolute wind) in rad
    Vaw = (Vw**2+Vs**2+2*Vs*Vw*cos(alpha))**0.5 #wind relative speed
    beta = acos((Vw*cos(alpha)+Vs)/Vaw) #wind relative direction
    return Vaw, rad2deg(beta)

def readFile (path):
    file = open (path, 'r') #apre il file in lettura
    lettura = file.readlines()# leggi file
    prova = 'ciao'

    start = 1 #individua la prima iterazione per rilevare il tipo
    elemento, telemetry=[], {} #lista temporanea, lista delle telemetrie
    i = 0

    for riga in lettura:
        elemento.append(riga.split(','))
        if i != 0:
            if start:#prima iterazione, recupera il tipo
                telemetry['type'] = elemento[i][0]
                telemetry['units']={'lat':elemento[i][3], 'lon':elemento[i][5], 'speed':elemento[i][7],'course':elemento[i][9], 'temp':elemento[i][11] , 'attitude':elemento[i][15]}
                start = 0
            if telemetry['type'] == '$MVUP':
                telemetry[i-1]={}
                telemetry[i-1]['time'] = float(elemento[i][1])/1000
                telemetry[i-1]['lat'] = float(elemento[i][2])/1000000
                telemetry[i-1]['lon'] = float(elemento[i][4])/1000000
                telemetry[i-1]['speed'] = float(elemento[i][6])
                telemetry[i-1]['course'] = int(elemento[i][8])
                telemetry[i-1]['temp'] = float(elemento[i][10])
                telemetry[i-1]['roll'] = float(elemento[i][12])
                telemetry[i-1]['pitch'] = float(elemento[i][13])
                telemetry[i-1]['yaw'] = float(elemento[i][14])
                telemetry[i-1]['w_s'] = float(elemento[i][16])
                telemetry[i-1]['w_d'] = [float(elemento[i][18]), float(elemento[i][19])]
                telemetry[i-1]['estensimeter'] = [float(elemento[i][21]),float(elemento[i][22])]
    
        i += 1
    start = 1
    return telemetry


def serial_ports():
    """Lists serial ports

    :raises EnvironmentError:
        On unsupported or unknown platforms
    :returns:
        A list of available serial ports
    """
    if sys.platform.startswith('win'):
        ports = ['COM' + str(i + 1) for i in range(256)]

    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this is to exclude your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')

    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')

    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

def readCommand(device, textBox):
    #command must be like this: $COMM,values*checksum
    #it will write commands on textBox
    comm=[]
    _xor = 0
    stringa = ""
    starter="$"
    if device.inWaiting():#if there is any data
        if device.read() == starter:#if the first data is starter
            c=device.read()
            while c!=",":
                _xor = _xor ^ ord(c)
                stringa = stringa + str(c)
                c = device.read()
            stringa = stringa + c + " "#read and insert comma
            comm.append(ord(device.read()))
            while comm[-1]!=42: #like *
                _xor = _xor ^ comm[-1]
                comm.append(ord(device.read()))
            del comm[-1]#elimina *
            for i in comm:
                stringa = stringa + (str(i)+" ")
            if _xor == ord(device.read()):#cheksum control
                textBox.insertPlainText(QtCore.QString(stringa + '\n'))

def readCommander(device):
    #command must be like this: $COMM,values*checksum
    #it will return type of commands and the list of command-bytes
    comm=[]
    _xor = 0
    type = ""
    starter="$"
    if device.inWaiting():#if there is any data
        if device.read() == starter:#if the first data is starter
            c=device.read()
            while c!=",":
                _xor = _xor ^ ord(c)
                type = type + str(c)
                c = device.read()
            comm.append(ord(device.read()))
            while comm[-1]!=42: #like *
                _xor = _xor ^ comm[-1]
                comm.append(ord(device.read()))
            del comm[-1]#elimina *
            if _xor != ord(device.read()):#cheksum control
                type = "checkError"
            return {'type':type, 'com':comm}
    else:
        return 0




