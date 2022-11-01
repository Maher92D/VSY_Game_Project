from tkinter import *
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import time
import tkinter.messagebox
import numpy as np


def check_winner(board,mark):
    rowstart = [0,3,6]
    for i in rowstart:
        if board[i] == mark and board[i+1] == mark and board[i+2] == mark:
            return True
    for i in range(0,3):
        if board[i] == mark and board[i+3] == mark and board[i+6] == mark:
            return True
    return (board[0] == mark and board[4] == mark and board[8] == mark) or (board[2] == mark and board[4] == mark and board[6] == mark)


class ConnectionHandler:

    # -------------------------------------------------------
    # -------------------------------------------------------
    def __init__(self, serverip="127.0.0.1", serverport=10001):
        # -------------------------------------------------------
        self.PORT = serverport
        self.HOST = serverip
        self.BUFSIZ = 1024
        self.ADDR = (self.HOST, self.PORT)
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.connected = False
        self.newmsg = False
        self.lastmsg = ""
        self.receive_thread = None

    # -------------------------------------------------------
    def receive(self):
        # -------------------------------------------------------
        # verarbeitet das Erhalten der Nachrichten
        while True:
            if self.connected:  # besteht eine Verbindung?
                try:
                    msg = self.client_socket.recv(self.BUFSIZ).decode("utf8")  # recv
                    print(msg)
                    self.handelmsg(msg)
                except:
                    break

    def handelmsg(self, msg):

        self.lastmsg = msg
        self.newmsg = True

    def getlastmsg(self):
        if self.newmsg:
            self.newmsg = False
            return self.lastmsg
        else:
            return ""

    # -------------------------------------------------------
    def connect(self):
        try:
            self.client_socket.settimeout(30)
            self.client_socket.connect(self.ADDR)
            self.receive_thread = Thread(target=self.receive)
            self.receive_thread.start()
            self.connected = True

            print("connected to ", self.ADDR)

        except:
            self.connected = False
            print("could not connect to the server")
            self.client_socket.close()
            self.client_socket = socket(AF_INET, SOCK_STREAM)
        return self.connected

    def send(self, msg):  # event is passed by binders.
        # -------------------------------------------------------
        msg = msg + "{turn}"  # # nachdem die Nachricht gesendet wurde, wird das Einagbefeld geleert
        print(msg)
        try:
            self.client_socket.send(bytes(msg, "utf8"))  # send

        except:
            print("not sent")

        if msg == "{quit}":
            msg = ""

    # -------------------------------------------------------
    def on_closing(self, event=None):
        # -------------------------------------------------------
        # schließt das Fenster

        self.send()

        exit()

    def sendplay(self,name):
        msg = name + "&{play}"
        print(msg)
        self.client_socket.send(bytes(msg, "utf8"))

    # -------------------------------------------------------


class Game:

    def __init__(self, connector):
        self.connector = connector
        self.firstname = "NoName"
        self.secondname = "NoName"
        self.getlastmsgThread = None
        self.gameclick = "X"
        self.yourturn = False
        self.tk = Tk()
        self.tk.title("Tic Tac Toe")

        labelconfig = dict(font='Times 20 bold', bg='white', fg='black', height=1, width=8)
        self.staticlabel = Label(self.tk, text="Fname", **labelconfig)
        self.staticlabel.grid(row=1, column=0)
        self.firstplayerEntry = Entry(self.tk, font='Times 20 bold', width=8)
        self.firstplayerEntry.insert(0, self.firstname)
        self.firstplayerEntry.grid(row=1, column=1)

        self.connectButton = Button(self.tk, text="connect", font='Times 20 bold', bg='gray', fg='white', height=1,
                                    width=8, command=self.connect)
        self.connectButton.grid(row=1, column=2)

        self.staticlabel2 = Label(self.tk, text="Sname", font='Times 20 bold', bg='white', fg='black', height=1,
                                  width=8)
        self.staticlabel2.grid(row=2, column=0)

        self.secondplayerlabel = Label(self.tk, text=self.secondname, font='Times 20 bold', bg='white', fg='black',
                                       height=1, width=8)
        self.secondplayerlabel.grid(row=2, column=1)
        self.playButton = Button(self.tk, text="play", font='Times 20 bold', bg='gray', fg='white', height=1, width=8,
                                 command=self.play)
        self.playButton.grid(row=2, column=2)

        self.buttons = {}
        self.addbuttons()
        self.resetbuttons = Button(self.tk, text="reset", font='Times 20 bold', bg='gray', fg='white', height=1,
                                   width=8,
                                   command=self.resetgame)
        # self.disableButton()
        self.resetbuttons.grid(row=6, column=1)
        self.turnlabel = Label(self.tk, text="wait", **labelconfig)
        self.turnlabel.grid(row=6, column=0)
        self.resultlabel = Label(self.tk, font='Times 15 bold', bg='white', fg='black',
                                       height=1, width=8)
        self.resultlabel.grid(row=6,column=2)

    def addbuttons(self):
        counter = 0
        for i in range(3, 6):
            for j in range(3):
                newbutton = Button(self.tk, text=" ", font='Times 20 bold', bg='gray', fg='white', height=4, width=8)
                newbutton.grid(row=i, column=j)
                newbutton.configure(command=lambda newbutton=newbutton: self.btnClick(newbutton))
                newbutton.number = counter
                self.buttons[counter] = newbutton
                counter += 1

    def getstatus(self):
        status = "name" + "!" + self.firstname + "!"
        for button in self.buttons.values():
            status += button["text"]
        status += "!{status}"

        return status


    def setstatus(self, status=""):
        try:
            #self.secondplayerlabel.configure(text=status.split("!")[1])
            for key, button in zip(status.split("!")[2], self.buttons.values()):
                if key != " ":
                    button.configure(text=key, state=DISABLED)

        except:
            print("error decoding the status")

    def btnClick(self, button):
        if self.yourturn:
            button["text"] = self.gameclick
            status = self.getstatus()
            self.connector.send(status)
            self.yourturn = False
            self.turnlabel.configure(text="wait")
            self.checkForWin(status)

    def disableButton(self):
        for button in self.buttons.values():
            button.configure(state=DISABLED)

    def enableButton(self):
        for button in self.buttons.values():
            button.configure(state="normal")

    def resetgame(self):
        for button in self.buttons.values():
            button.configure(text=" ")

    def start(self):
        self.tk.mainloop()

    def getlastmsg(self):
        while self.connector.connected:
            msg = self.connector.getlastmsg()
            if msg != "":
                print(msg)
                if "{win}" in msg:
                    tkinter.messagebox.showinfo("Tic-Tac-Toe", "you lost")
                    continue
                if "{wait}" in msg:
                    self.playButton.configure(state=DISABLED)
                if "{found}" in msg:
                    self.playButton.configure(state=DISABLED)
                    if "{ooo}" in msg:
                        self.gameclick = "O"
                    elif "{xxx}" in msg:
                        self.gameclick = "X"
                    self.secondplayer = msg.split("!")[1]
                    self.secondplayerlabel.configure(text=self.secondplayer)
                if "{turn}" in msg:
                    self.yourturn = True
                    self.turnlabel.configure(text="yourturn")
                if "{status}" in msg:
                    self.setstatus(msg)
                if "{maindown}" in msg:
                    print("main server is down")

            time.sleep(0.1)

    def connect(self):
        if not self.connector.connected:
            self.firstname = self.firstplayerEntry.get()
            if self.connector.connect():
                self.connectButton.configure(state=DISABLED, text="connected")
                self.firstplayerEntry.configure(state=DISABLED)
                self.getlastmsgThread = Thread(target=self.getlastmsg)
                self.getlastmsgThread.start()

    def play(self):
        if self.connector.connected:
            self.connector.sendplay(self.firstname)

    def checkForWin(self, status):
        statuslist= list(status.split("!")[2])
        if check_winner(statuslist,self.gameclick):
            tkinter.messagebox.showinfo("Tic-Tac-Toe", "you won")
            self.connector.send("{status}{win}")


if __name__ == '__main__':
    connector = ConnectionHandler()
    newgame = Game(connector)
    newgame.start()
