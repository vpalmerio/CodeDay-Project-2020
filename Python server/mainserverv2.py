#!/usr/bin/env python
import socket
import sys
import select
from pydub import AudioSegment
from pydub.playback import play
import os
import threading
from multiprocessing import Process
import communicationclass

# requirements... pip install pydub and pip install ffmpeg (for doorbell sound)

# possible features: add a way to tell the python server that esp is resetting

# initialize variables

debugMode = False
websiteFunctionality = True


class Proxy:

    def __init__(self):
        # proxy variables
        self.proxyreceivingTCP_IP = ""  # it being nothing means any ip can connect
        self.proxyreceivingTCP_PORT = 8081  # the port that the proxy listens to
        self.proxybufferSize = 30000000

    # proxy server functions
    def handleClient(self, webconn, doorbellAddr):
        # browser request
        camerasock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        camerasock.connect((doorbellAddr, 80))  # socket for the camera website
        print("Proxy: Connecting to server")
        request = webconn.recv(self.proxybufferSize)
        camerasock.sendall(request)

        while True:
            print("Proxy: Waiting for server to respond")
            data = camerasock.recv(self.proxybufferSize)
            print(data)
            print("Proxy: Data received")

            if len(data) > 0:
                print("Proxy: Sending data to browser")
                webconn.send(data)  # redirect data to browser
                print("Proxy: Data sent to browser")
            else:
                print("Proxy: All data sent.")
                break

    def proxySetup(self, DoorbellAdd):
        # get address of doorbell
        # setup the socket
        websock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # allows the socket to be reused
        websock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        websock.bind((self.proxyreceivingTCP_IP, self.proxyreceivingTCP_PORT))
        websock.listen(10)
        print("Proxy: Client socket created")

        while True:
            print("Proxy: Accepting connections")
            webconn, address = websock.accept()
            print("Proxy: Connection accepted")
            t = threading.Thread(target=self.handleClient, args=(webconn, DoorbellAdd))
            t.setDaemon(True)
            t.start()


def checkWebsite(webprocessconn):
    webprocessconn.settimeout(1)
    try:
        webcommand = webprocessconn.recv(8192)
        webcommand = webcommand.decode('UTF-8')
        if webcommand == 's':
            global requestforMotion
            requestforMotion = True
            print("Update for motion sensor requested")
            webcommand = ''
        elif webcommand:
            print("Command received from website")
    except socket.timeout:
        print("No command from website received")
        webcommand = ''
        pass
    return webcommand


def controlLights(DoorbellAddr, command):
    if command == "on":
        # tell the camera phone's light to turn on if motion sensor is triggered
        webrequest = b'GET /enabletorch HTTP/1.1\r\nHost: localhost:8081\r\nUser-Agent: Mozilla/5.0 (X11; Ubuntu; ' \
                     b'Linux x86_64; rv:74.0) Gecko/20100101 Firefox/74.0\r\nAccept: text/html,' \
                     b'application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\nAccept-Language: ' \
                     b'en-US,en;q=0.5\r\nAccept-Encoding: gzip, deflate\r\nDNT: 1\r\nConnection: ' \
                     b'keep-alive\r\nUpgrade-Insecure-Requests: 1\r\n\r\n '

        tempwebsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tempwebsocket.connect((DoorbellAddr, 8080))
        tempwebsocket.sendall(webrequest)
        tempwebsocket.close()
        # end of temp web socket
    elif command == "off":
        # disable light
        webrequest2 = b'GET /enabletorch HTTP/1.1\r\nHost: localhost:8081\r\nUser-Agent: Mozilla/5.0 (X11; Ubuntu; ' \
                      b'Linux x86_64; rv:74.0) Gecko/20100101 Firefox/74.0\r\nAccept: text/html,' \
                      b'application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\nAccept-Language: ' \
                      b'en-US,en;q=0.5\r\nAccept-Encoding: gzip, deflate\r\nDNT: 1\r\nConnection: ' \
                      b'keep-alive\r\nUpgrade-Insecure-Requests: 1\r\n\r\n '
        tempwebsocket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tempwebsocket2.connect((DoorbellAddr, 8080))
        tempwebsocket2.sendall(webrequest2)
        tempwebsocket2.close()


if __name__ == "__main__":

    # setup initial variables
    askedUser = False
    userCommand = ''
    requestedDevice = ""
    update = 'u'  # update message to esps
    requestforMotion = False  # variable for when website requests motion data or not

    # setup communication class object
    comm = communicationclass.Communication()

    # doorbell sound
    song = AudioSegment.from_wav("Doorbell.wav")

    # setup the socket
    sock = socket.socket(socket.AF_INET,  # open socket to internet
                         socket.SOCK_STREAM)  # use TCP

    # allows the socket to be reused
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # bind socket to ip and port
    receivingTCP_IP = ""  # it being nothing means any ip can connect, will change to only allow doorbell and smartlock
    receivingTCP_PORT = 25566  # the port that the server listens to
    sock.bind((receivingTCP_IP, receivingTCP_PORT))

    sock.listen(2)

    # first device
    print("Waiting for first to connect...")
    conn1, deviceaddr1 = sock.accept()
    getDeviceName1 = comm.recvMsg(conn1)  # need to input which device to use

    if not debugMode:
        # second device
        print("Waiting for second device to connect to connect...")
        conn2, deviceaddr2 = sock.accept()
        getDeviceName2 = comm.recvMsg(
            conn2)  # device should send bytes identifying itself, recieve msg returns message encoded

    # identify the devices
    if getDeviceName1 == "D":
        DOORBELLCONN = conn1
        DoorbellAddr = deviceaddr1
    elif getDeviceName1 == "S":
        SMARTLOCKCONN = conn1

    if not debugMode:
        if getDeviceName2 == "D":
            DOORBELLCONN = conn2
            DoorbellAddr = deviceaddr2
        elif getDeviceName2 == "S":
            SMARTLOCKCONN = conn2

    # start the proxy server for the camera stream
    proxy = Proxy()
    DoorbellAddr = DoorbellAddr[0]  # camera ip
    p = Process(target=proxy.proxySetup, args=(DoorbellAddr,))
    p.start()
    print("Started proxy for camera website.")

    # setup the website
    if websiteFunctionality:
        print("Setting up website socket")
        webprocesssock = socket.socket(socket.AF_INET,  # open socket to internet
                                       socket.SOCK_STREAM)  # use TCP
        # allows the socket to be reused
        webprocesssock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        webprocesssock.bind(("127.0.0.1", 8079))
        webprocesssock.listen(1)
        print("Socket started. Listenning for website process...")
        webprocessconn, webprocessaddr = webprocesssock.accept()
        print("Website process connected")

    # infinite loop
    while True:
        # command funtion
        if debugMode:
            print("New loop!")

        if websiteFunctionality:
            userCommand = checkWebsite(webprocessconn)  # if there is a command from the website, the server will not
            # ask for input

        if not userCommand:
            if not askedUser:
                print("Enter command (you have 4 seconds): ")

                userCommand, o, e = select.select([sys.stdin], [], [], 4)

                if userCommand:
                    print("Command received: ", sys.stdin.readline().strip())

                    if userCommand == "exit":
                        conn1.close()
                        conn2.close()
                        Exit()

                    print("Enter 1 or 2 for device (1 is SMARTLOCK, 2 is DOORBELL, or choose c for cancel): ")
                    requestedDeviceNumber, o, e = select.select([sys.stdin], [], [])

                    if requestedDeviceNumber:
                        if requestedDeviceNumber == 1:
                            requestedDevice = "SMARTLOCK"
                        elif requestedDeviceNumber == 2:
                            requestedDevice = "DOORBELL"
                        elif requestedDeviceNumber == 'c':
                            requestedDevice = "cancel"
                        else:
                            print("You did not choose correctly. Ignoring command and continuing")
                            userCommand = ''
                            requestedDeviceNumber = ''
                            requestedDevice = ''

                    if userCommand == "cancel" or requestedDevice == "cancel":  # resets to ask for userCommand
                        userCommand = ""
                        askedUser = False
                    else:
                        askedUser = True

                else:
                    print("No command entered. Continuing...")

        # ask for updates function
        print("Sending update request to DOORBELL...")
        comm.sendtoDevice(update.encode('UTF-8'), DOORBELLCONN)
        print("Waiting for update from DOORBELL...")
        updateInfoD = comm.recvMsg(DOORBELLCONN)

        # change the smartlock conn soon
        if not debugMode:
            print("Sending update request to SMARTLOCK...")
            comm.sendtoDevice(update.encode('UTF-8'), SMARTLOCKCONN)
            print("Waiting for update from SMARTLOCK...")
            updateInfoS = comm.recvMsg(SMARTLOCKCONN)  # waits for response
            print(updateInfoS)

        # check for RFID code:
        if "Z" in updateInfoD:
            print("Received RFID Data")
            # take out the RFID data from the packet
            RFID = []
            BeginningofMessage = 'Z'
            EndofMessage = "/"
            RFID.append(updateInfoD[1:updateInfoD.find(
                EndofMessage)])  # the end of the RFID data is a /, so if you find the / then stop looking for more info
            RFIDdecoded = ''.join(RFID)  # turn RFID data into a string
            print("RFID Card: " + RFIDdecoded)

            # check if RFID data matches the hardcoded unlock code
            if RFIDdecoded == "e5 b3 3f 23":
                # sends unlock command and waits for response
                unlock = 'U'
                print("Sending unlock code to smart lock")

                if not debugMode:
                    comm.sendtoDevice(unlock.encode('UTF-8'), SMARTLOCKCONN)
                    updateInfoSU = comm.recvMsg(SMARTLOCKCONN)
                    if "UN" in updateInfoSU:
                        print("Successfully unlocked door")
                    else:
                        print("Did not receive unlock response. Did the door unlock?")

            # remove the RFID data from the packet since we already dealt with it and we dont confuse the server
            updateInfoD = updateInfoD[updateInfoD.find(EndofMessage) + 1:]
            print("New UpdateInfoD: " + updateInfoD)

        # check for motion sensor
        if "t" in updateInfoD:
            print("Motion sensor was triggered!!")
            # light process for lights
            controlLights(DoorbellAddr, "on")
            if requestforMotion:
                motiondata = "trig:"
                print("Received a request, sending data...")
                webprocessconn.send(motiondata.encode('UTF-8'))
                requestforMotion = False
            else:
                print("No request received, continuing...")
        elif "n" in updateInfoD:
            print("Motion sensor was not triggered")
            controlLights(DoorbellAddr, "off")
        else:
            print("Did not receive an update on motion sensor")

        # check for proximity sensor
        if "h" in updateInfoD:
            print("Proximity sensor was triggered!")
            play(song)
        elif "i" in updateInfoD:
            print("Proximity sensor was not triggered")

        if not debugMode:
            # check if lock is locked
            if "d" in updateInfoS:
                print("Smartlock is locked")
            elif "c" in updateInfoS:
                print("Smartlock isn't locked")
            # check if door is open
            if "a" in updateInfoS:
                print("Door is open")
            elif "b" in updateInfoS:
                print("Door is closed")

        if userCommand:  # if there is a command, encode it into bytes and send it to requested device
            userCommand = userCommand.encode('UTF-8')
            comm.sendtoDevice(userCommand, requestedDevice)

            print("Command: " + userCommand + " sent to: " + requestedDevice)

            userCommand = None

            askedUser = False
