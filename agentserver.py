# verbindungsorientierte Kommunikation, aufsetzend auf TCP = SOCK_STREAM
# Kommunikation zwischen TCP/IP-Netz verteilten Prozessen = AF_INET, Internet IP Protokoll
import time
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread, Semaphore
import sys
from time import sleep
import json
from queue import Queue

clients = {}
addresses = {}
msgend = "%"


# -------------------------------------------------------
class Server_cl():
    # -------------------------------------------------------
    # -------------------------------------------------------
    def __init__(self):
        # -------------------------------------------------------

        self.HOST = "127.0.0.1"
        self.PORT = 10001
        self.BUFSIZ = 1024
        self.ADDR = (self.HOST, self.PORT)
        print(self.ADDR)
        self.SERVER = socket(AF_INET, SOCK_STREAM)  # socket
        self.SERVER.bind(self.ADDR)  # bind
        self.mainSERVER = socket(AF_INET, SOCK_STREAM)
        self.rserver = socket(AF_INET, SOCK_STREAM)
        self.HAUPTSERVER = True  # läuft über den Server 1
        self.mainstatus = False
        self.rstatus = False
        if not self.createmain(9000):
            print("Main is down")
        if not self.createrserver(43001):
            print("R is down")
        self.msgfifo = Queue()
        Thread(target=self.reconnect).start()
        Thread(target=self.sendtoclients).start()

    # -------------------------------------------------------
    def accept_incoming_connections(self):
        # -------------------------------------------------------
        # wartet auf neue Clienten mit Server Accept, auf Clientseite Connect
        while True:
            client, client_address = self.SERVER.accept()  # accept
            print(str(client_address) + " ist verbunden.")
            addresses[client_address] = client
            Thread(target=self.handle_client,
                   args=(client, client_address)).start()  # Thread wird gestartet,multithreading

    # -------------------------------------------------------
    # -------------------------------------------------------
    def handle_client(self, client, client_address):  # Client-Socket als Argument
        # -------------------------------------------------------
        while True:
            try:
                msg = client.recv(self.BUFSIZ)
                msg = msg.decode("utf8")

                if len(msg) == 0:
                    raise Exception

                if msg != "{quit}":
                    if len(msg) != 0:
                        print(client_address, msg)
                        self.sendtoserver(client_address, msg)
                else:
                    client.close()
                    print(str(len(clients)) + " Clienten sind verbunden.")
                    break
            except Exception as e:
                print(e)
                print("client is down ")
                break

    # -------------------------------------------------------
    def broadcast(self, msg, prefix=""):  # prefix ist für name identification.
        # -------------------------------------------------------
        # Broadcasts eine Nachricht an alle Clients.
        for sock in clients:
            try:
                sock.send(msg)
            except:
                sock.close()

    def createmain(self, port):
        try:
            self.mainSERVER.connect((self.HOST, port))
            print("main is connected")
            self.mainstatus = True
            Thread(target=self.mainreciever, args=()).start()
            return self.mainstatus

        except Exception as e:
            self.mainSERVER.close()
            self.mainSERVER = socket(AF_INET, SOCK_STREAM)

    def createrserver(self, port):
        try:

            self.rserver.connect((self.HOST, port))
            print("r is connected")
            self.rstatus = True
            Thread(target=self.reciever, args=()).start()
            return self.rstatus
        except Exception as e:
            self.rserver.close()
            self.rserver = socket(AF_INET, SOCK_STREAM)

    def reconnect(self):
        while True:
            if not self.rstatus:
                self.createrserver(43001)
            if not self.mainstatus:
                self.createmain(9000)
            time.sleep(0.5)

    def sendtoserver(self, clienaddress, msg):
        msg = str(clienaddress[0]) + "&" + str(clienaddress[1]) + "&" + msg
        msgb = bytes(msg, encoding="utf8")
        print(msg)
        if self.mainstatus:
            try:
                self.mainSERVER.send(msgb)
                print("sent to main " + msg)
            except:
                print("main is down")
        elif self.rstatus:
            try:
                self.rserver.send(msgb)

                print("sent to R" + msg)
            except:

                print("R is down")
        else:
            print("both server are down")

    def reciever(self):

        while self.rstatus:
            print("waiting msg from r")
            try:
                msgb = self.rserver.recv(self.BUFSIZ)
                self.handel_msg_from_servers(msgb)
            except Exception as e:
                print(e)
                print("R is down")
                self.rstatus = False




    ##################################################
    def mainreciever(self):

        while self.mainstatus:
            print("waiting msg from main")
            try:
                msgb = self.mainSERVER.recv(self.BUFSIZ)
                self.handel_msg_from_servers(msgb)

            except Exception as e:
                print(e)
                print("main is down")
                self.mainstatus = False
                if self.rstatus:
                    try:
                        self.rserver.send(bytes("{maindown}", "utf8"))
                    except Exception as e:
                        print(e)
                break

    def handel_msg_from_servers(self, msgb):
        msg = msgb.decode("utf8")
        msglist = msg.split(msgend)
        for m in msglist:
            if m != "":
                x = m.split("&")
                add = (x[0], int(x[1]))
                newmsg = (add, x[2])
                self.msgfifo.put(newmsg)
                print("server " + x[2])

    def sendtoclients(self):
        while True:
            if not self.msgfifo.empty():
                add, msg = self.msgfifo.get()
                if "{broadcast}" in msg:
                    self.broadcast(msg)
                else:
                    msgb = bytes(msg, "utf8")
                    for clientadd in addresses:
                        if clientadd == add:
                            try:
                                addresses[clientadd].send(msgb)
                            except Exception as e:
                                print(e)
            time.sleep(0.05)

    def broadcast(self,msg):
        msgb = bytes(msg, "utf8")
        for clientadd in addresses:
                try:
                    addresses[clientadd].send(msgb)
                except Exception as e:
                    print(e)
        pass

# -------------------------------------------------------
if __name__ == "__main__":
    # -------------------------------------------------------
    sev = None
    # Prüft, ob Port angegeben wurde
    if len(sys.argv) == 1:
        sev = Server_cl()
        print("AGENT 127.0.0.1:10001")
    elif len(sys.argv) == 2:
        sev = Server_cl('127.0.0.1', int(sys.argv[1]))
        sev.HAUPTSERVER = False
        print("Verbinde zu " + '127.0.0.1' + ":" + str(sys.argv[1]))
    else:
        print("Nur Port oder nichts.")
        exit()

    sev.SERVER.listen(5)  # listen
    ACCEPT_THREAD = Thread(target=sev.accept_incoming_connections)  # neuer Thread erzeugt
    ACCEPT_THREAD.start()  # starte Thread
    ACCEPT_THREAD.join()  # wartet auf das Ende des anderen Threads
    sev.SERVER.close()  # close
