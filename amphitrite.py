#!/usr/bin/python

"""
    amphitrite.py v2.0
    
    Dott.Andrea Mastrangelo
    19/03/2015
    
    MAIN FEATURES:
    
    Gui written with PyQt4
    """
#   cd /Users/gregoriomastrangelo/Desktop/Programmazione/Programmi/Python/amphitrite_v20
#   cd /Users/mastraa/Desktop/1001Vela/6000/Emessi/6024_ProgrammiDecodifica/amphitrite_v20
#   cd /Users/superuser/Google Drive/1001Vela/6000_Strumentazione/Emessi/6024_ProgrammiDecodifica/amphitrite_v20

import sys
import serial
sys.path.append('librerie')
import amphlib as lib
from PyQt4 import QtCore, QtGui, uic
from time import strftime


gui = "gui/mainGui.ui"
#gui = "gui/ui_imagedialog.ui" #older gui file

baudValues = ["9600", "57600", "115200"]

class InfoWindow(QtGui.QWidget):
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = uic.loadUi("gui/info.ui")
        self.ui.show()

class ImageDialog(QtGui.QMainWindow): #definisce la classe in modo che si possano assegnare delle funzioni ai vari tools
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        
        #variables
        global baudValues
        global gui
        self.cycleNumber = 0
        self.device = 0
        self.i = 0 #cicle counter for che watch
        self.serialFlag = 1 #to know if the received data package is finished and set a new line
        self.status = 0; #connection status
        self.iconStatus = ["icons/red.png", "icons/green.png"] #icon list
        self.interval = 200 #timer interval
        
        #timer set
        self.timer = QtCore.QTimer(self) #timer set
        self.timer.timeout.connect(self.timerFunctions) #timer function assignement
        self.timer.start(self.interval) #timer start with assigned interval (millis)
        
        self.ui = uic.loadUi(gui) #load GUI
        self.ui.lcdTime.setDigitCount(8) #modifiche all'elemento indicato (objectName su QtDesigner)
        self.ui.lcdTime.display(strftime("%H"+":"+"%M"+":"+"%S"))
        self.ui.BaudList.addItems(baudValues)
        self.ui.readFreq.setSliderPosition(1000/self.interval)
        self.ui.readFreqText.setText(QtCore.QString(str(1000/self.interval)))
        
        #button - function connection
        self.ui.SerialCheckButton.clicked.connect(self.SerialCheck)
        self.ui.connButton.clicked.connect(self.Connection)
        self.ui.persBaudSett.clicked.connect(self.addPersBaud)
        self.ui.sendButton.clicked.connect(lambda: self.Sender(self.device, self.ui.serialText))
        self.ui.serialText.returnPressed.connect(lambda: self.Sender(self.device, self.ui.serialText))
        self.ui.clearData.clicked.connect(lambda: self.clear(self.ui.receivedData))
        self.ui.readFreq.valueChanged.connect(self.getValue)
        self.ui.readFreqText.textEdited.connect(self.getValue)
        self.ui.byteData.toggled.connect(lambda: self.newLine(self.ui.receivedData))
        
        self.SerialCheck()#first serial check attempt
        
        self.ui.show() #show application window

    def timerFunctions(self):
        self.cycleNumber += 1#cycle counter
        #print (self.cycleNumber, self.interval)#debugger tools
        self.i = self.i + 1
        timeStr = strftime("%H"+":"+"%M"+":"+"%S")
        if self.i == 1000/self.interval: #it works at 1Hz
            self.Time(timeStr) #clock update
            self.i = 0 #reset cycle counter
        if self.device:
            self.Receive(timeStr) #call serial reading

    def Time(self, data):
        self.ui.lcdTime.display(data)

    def SerialCheck(self):
        seriali = lib.serial_ports() #get serial ports available
        self.ui.SerialList.clear() #you must clear before add
        for item in seriali:
            self.ui.SerialList.addItem(item) #insert serial port available in combo box

    def Connection(self): #start reading usb port
        gui = self.ui
        self.status = not self.status #status toggle
        icon  = QtGui.QPixmap(self.iconStatus[self.status]) #switch button icon
        gui.connButton.setIcon(QtGui.QIcon(icon)) #setIcon
        #clear parameters summary
        gui.baudLabel.clear()
        gui.serialLabel.clear()
        if self.status:
            baud = self.ui.BaudList.currentText() #get baudrate
            port = self.ui.SerialList.currentText() #get port
            #parameter summary
            self.device = serial.Serial(str(port), int(baud)) #open connection
            gui.sendButton.setEnabled(1)
            gui.SerialList.setEnabled(0)
            gui.SerialCheckButton.setEnabled(0)
            gui.BaudList.setEnabled(0)
        else:
            self.device.close() #close connection
            gui.sendButton.setEnabled(0)
            gui.SerialList.setEnabled(1)
            gui.SerialCheckButton.setEnabled(1)
            gui.BaudList.setEnabled(1)
            self.device = 0

    def addPersBaud(self):#add new baudrate to the list
        self.ui.BaudList.addItem(self.ui.persBaud.text())
        self.ui.persBaud.clear()

    def Sender(self, device, sendBox):
        if self.ui.checkSumBox.isChecked():
            ender=""
        elif self.ui.radioButton_none.isChecked():
            ender = ''
        elif self.ui.radioButton_n.isChecked():
            ender = '\n'
        elif self.ui.radioButton_r.isChecked():
            ender = ''
        elif self.ui.radioButton_nr.isChecked():
            ender = ''
        sended = lib.Send(device, "$",ender,[",","*"],(str(sendBox.text())).split(","))
        self.ui.sendedData.insertPlainText(QtCore.QString(sended+"\n"))#sended debug data
        self.clear(sendBox)#clear text

    def Receive(self, _timeStr):
        if self.device.inWaiting():#if serial buffer has byte(s)
            if self.ui.byteData.isChecked():#read as bytes
                comando = lib.readCommand(self.device)
                if comando:
                    self.ui.receivedData.insertHtml(QtCore.QString(lib.checkCommand(comando, _timeStr)))
            else:#read as ascii string
                if self.serialFlag:#if the string was completely read
                    self.serialFlag = 0#we are reading
                    if self.ui.newLineCheck.isChecked():#if we want new line
                        data = "\n" + _timeStr + ":\t" + self.device.read(self.device.inWaiting())
                    else:#if we don't
                        data = _timeStr + ":\t" + self.device.read(self.device.inWaiting())
                else:#if datas are bytes of older packet
                    data = self.device.read(self.device.inWaiting())
                self.ui.receivedData.insertPlainText(QtCore.QString(data))
        else:
            self.serialFlag = 1#end reading
        if self.ui.autoScrollCheck.isChecked():# scroll textArea
            c =  self.ui.receivedData.textCursor()
            c.movePosition(QtGui.QTextCursor.End)
            self.ui.receivedData.setTextCursor(c)

    def clear(self, textBox):
        textBox.setText('')
    
    def newLine(self, textBox):
        textBox.append('\n')

    def getValue(self, position):# get slider position or textFreq val
        if isinstance( position, int ):# if the function has been called by slider
            self.ui.readFreqText.setText(QtCore.QString(str(position)))
            self.timer.setInterval(1000/position)
            self.interval = 1000/position
        else:#if function has been called by textEdit
            position = int(position)
            self.timer.setInterval(1000/position)
            self.interval = 1000/position
            self.ui.readFreq.setSliderPosition(position)


app = QtGui.QApplication(sys.argv)
window = ImageDialog()

sys.exit(app.exec_())