# verbindungsorientierte Kommunikation, aufsetzend auf TCP = SOCK_STREAM
# Kommunikation zwischen TCP/IP-Netz verteilten Prozessen = AF_INET, Internet IP Protokoll
import os
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread, Semaphore
import sys
import pickle

p1 = ''
msgend = "%"
clients = {}
addresses = {}


class playerC:

    def __init__(self,ip,port,name):
        self.ip = ip
        self.port = port
        self.name = name
        self.status = "wait"
        self.mate = None
        self.socket = socket

    def getasstring(self):
        return self.ip+self.port+self.name

# -------------------------------------------------------
class Server_cl():
    # -------------------------------------------------------
    # -------------------------------------------------------
    def __init__(self, host, port):
        # -------------------------------------------------------
        self.ACCEPT_THREAD = None
        self.HOST = host
        self.PORT = port

        self.BUFSIZ = 1024
        self.ADDR = (self.HOST, self.PORT)
        print("Try: ",self.ADDR)
        self.SERVER = socket(AF_INET, SOCK_STREAM)  # socket
        self.SERVER.bind(self.ADDR)  # bind
        self.playersfile = "./data"
        self.playerslist = []

    # -------------------------------------------------------
    def startserver(self):
        self.SERVER.listen(5)  # listen
        self.ACCEPT_THREAD = Thread(target=self.accept_incoming_connections)
        self.ACCEPT_THREAD.start()  # starte Thread

    def accept_incoming_connections(self):

        while True:
            client, client_address = self.SERVER.accept()  # accept
            print("agent : "+str(client_address) + " ist verbunden.")
            addresses[client_address] = client
            Thread(target=self.handle_client, args=(client,client_address,)).start()

    def handle_client(self, client,client_address):  # Client-Socket als Argument
        def send(newmsg):
            print(newmsg)
            client.send(bytes(newmsg+msgend, "utf8"))
        while True:

            try:
                msg = client.recv(self.BUFSIZ)
                msg = msg.decode("utf8")
                if len(msg) == 0:
                    print("agent is down")
                if "{maindown}" in msg:
                    print("the main server now")
                    self.loadplayers()
                    self.broadcast("{mainserver}")
            except Exception as e:
                print("agent is down : "+str(client_address))
                break

            if msg != "{quit}":
                print(msg)
                msg = msg.split("&")
                if "{play}" in msg:
                    newplayer = playerC(msg[0],msg[1],msg[2])
                    self.playerslist.append(newplayer)
                    newmsg = msg[0]+"&"+msg[1]+"&{wait}"
                    send(newmsg)
                    self.saveplayers()

                if len(msg) > 2:
                    if "{status}" in msg[2]:
                        for player in self.playerslist:
                            if msg[0] == player.ip and msg[1] == player.port:
                                send(player.mate.ip+"&"+player.mate.port+"&"+msg[2])
                waitplayer = None
                for player in self.playerslist:
                    if player.status == "wait":
                        if waitplayer is not None:
                            player.mate = waitplayer
                            player.status = "playing"
                            send(player.ip+"&"+player.port+"&name!"+waitplayer.name+"!{found}{ooo}")
                            waitplayer.mate = player
                            waitplayer.status = "playing"
                            send(waitplayer.ip + "&" + waitplayer.port + "&name!"+player.name+"!{found}{turn}{xxx}")
                            print("playing: ",waitplayer.getasstring(),player.getasstring())
                            waitplayer = None
                            self.saveplayers()
                        else:
                            waitplayer = player


    def saveplayers(self):
        with open(self.playersfile, "wb") as f:
            pickle.dump(self.playerslist, f)

    def loadplayers(self):
        if os.path.getsize(self.playersfile) > 0:
            with open(self.playersfile, "rb") as f:
                unpickler = pickle.Unpickler(f)
                self.playerslist = unpickler.load()


    def broadcast(self, newmsg):
        print("broadcast")
        broadcast = "127.0.0.1&0000&{broadcast}"
        for sock in addresses.values():
            try:
                print(newmsg)
                sock.send(bytes(broadcast+newmsg+ msgend, "utf8"))

            except Exception as e:
                print(e)
                sock.close()


if __name__ == "__main__":
    try:
        sev = Server_cl('127.0.0.1', 9000)
        sev.startserver()
        print("Verbinde zu 127.0.0.1:9000")
    except:
        print("failed")
        sev = Server_cl('127.0.0.1', 43001)
        sev.startserver()
        print("Verbinde zu 127.0.0.1:43001")


