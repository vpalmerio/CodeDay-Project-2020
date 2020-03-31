#!/usr/bin/env python
import socket
import sys
import select
from pydub import AudioSegment
from pydub.playback import play
import os
import threading
from multiprocessing import Process

# requirements... pip install pydub and pip install ffmpeg (for doorbell sound)

# Plan: python server will act as server and the esps will try to connect to the server, they will send their names through packets

# tasks... Create the website with flask!! e.g. if server.com/lock is asked for, then lock the door!!!
# tropical doorbell sound

# server will ask for updates every couple of seconds, and clients will respond

# possible features: add a way to tell the python server that esp is resetting

# initialize variables
song = AudioSegment.from_wav("Doorbell.wav")
bufferSize = 1024
askedUser = False
userCommand = ''
requestedDevice = ""
askedUserForDevice = False
address = ''
readMessage = ''
expectedMessageLength = 0
amountofClients = 0
endofMessage = ':'
update = 'u'  # update message to esps
websiteFunctionality = True
requestforMotion = False

# proxy variables
proxyreceivingTCP_IP = ""  # it being nothing means any ip can connect
proxyreceivingTCP_PORT = 8081  # the port that the proxy listens to
proxybufferSize = 30000000

# server
receivingTCP_IP = ""  # it being nothing means any ip can connect, will change to only allow doorbell and smartlock
receivingTCP_PORT = 25566  # the port that the server listens to


# proxy server functions
def handleClient(webconn, doorbellAddr):
    # browser request
    camerasock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    camerasock.connect((doorbellAddr, 80)) #socket for the camera website
    print("Proxy: Connecting to server")
    request = webconn.recv(proxybufferSize)
    camerasock.sendall(request)

    while True:
        print("Proxy: Waiting for server to respond")
        data = camerasock.recv(proxybufferSize)
        print(data)
        print("Proxy: Data recieved")

        if (len(data) > 0):
            print("Proxy: Sending data to browser")
            webconn.send(data)  # redirect data to browser
            print("Proxy: Data sent to browser")
        else:
            print("Proxy: All data sent.")
            break


def proxySetup(DoorbellAdd):
    # get address of doorbell
    # setup the socket
    websock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # allows the socket to be reused
    websock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    websock.bind((proxyreceivingTCP_IP, proxyreceivingTCP_PORT))
    websock.listen(10)
    print("Proxy: Client socket created")

    while True:
        print("Proxy: Accepting connections")
        webconn, address = websock.accept()
        print("Proxy: Connection accepted")
        t = threading.Thread(target=handleClient, args=(webconn, DoorbellAdd))
        t.setDaemon(True)
        t.start()


# server variables
# for commands through python server
def sendtoDevice(datainBytes, requestedDevice):
    if requestedDevice == "SMARTLOCK":
        SMARTLOCKCONN.send(datainBytes)
        print("Data sent")

    elif requestedDevice == "DOORBELL":
        DOORBELLCONN.send(datainBytes)
        print("Data sent")


def printMsg(address, readMessage):
    clientMsg = "Message from Client: {}".format(readMessage)
    clientIP = "Client IP Address: {}".format(address)
    print(clientMsg)
    print(clientIP)


# receiving messages
def recvMsg(conn):
    totalData = []  # cant guarantee that packets will be split up or put together, so put data received into an array
    data = ''  # reset variables
    address = ''
    bytesRecieved = 0
    while True:
        data, address = conn.recvfrom(bufferSize)  # waits to recieve info (does not matter the size)
        # data is the message received, address is the ip address from the device that sent the message
        data = data.decode('UTF-8')
        if endofMessage in data:
            totalData.append(data[:data.find(
                endofMessage)])  # the end of the packet has a :, so if you find the : then stop looking for more info
            readMessage = ''.join(totalData)
            printMsg(address, readMessage)
            break
        if not (data):
            print("No new data received")
            break
        totalData.append(data)  # if there is no ':' yet, then just add the data to the array until there is a ':'
        bytesRecieved = bytesRecieved + len(totalData)
        readMessage = ''.join(totalData)
        printMsg(address, readMessage)
    return ''.join(totalData)  # returns all elements of total data as a string

def checkWebsite(webprocessconn):
    webprocessconn.settimeout(1)
    try:
        webcommand = webprocessconn.recv(bufferSize)
        webcommand = webcommand.decode('UTF-8')
        if webcommand == 's':
            global requestforMotion
            requestforMotion = True
            print("Update for motion sensor requested")
            webcommand = None
        else:
            print("Command received from website")
    except socket.timeout:
        print("No command from website received")
        webcommand = None
        pass
    return webcommand


if __name__ == "__main__":

    # setup the socket
    sock = socket.socket(socket.AF_INET,  # open socket to internet
                         socket.SOCK_STREAM)  # use TCP
    # allows the socket to be reused
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((receivingTCP_IP, receivingTCP_PORT))
    sock.listen(2)

    # first device
    print("Waiting for first to connect...")
    conn1, deviceaddr1 = sock.accept()
    amountofClients = amountofClients + 1
    getDeviceName1 = recvMsg(conn1)  # need to input which device to use

    # second device
    # print("Waiting for second device to connect to connect...")
    # conn2, deviceaddr2 = sock.accept()
    # amountofClients = amountofClients + 1
    # getDeviceName2 = recvMsg(conn2)  # device should send bytes identifying itself, recieve msg returns message encoded

    if getDeviceName1 == "D":
        DOORBELLCONN = conn1
        DoorbellAddr = deviceaddr1
    elif getDeviceName1 == "S":
        SMARTLOCKCONN = conn1

    # if (getDeviceName2 == "DOORBELL"):
    #    DOORBELLCONN = conn2
    #    DoorbellAddr = deviceaddr2
    # elif (getDeviceName2 == "SMARTLOCK"):
    #    SMARTLOCKCONN = conn2

    DoorbellAddr = DoorbellAddr[0]
    p = Process(target=proxySetup, args=(DoorbellAddr,))
    p.start()
    print("Started proxy for camera website.")

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
        if websiteFunctionality:
            userCommand = checkWebsite(webprocessconn) # if there is a command from the website, the server will not
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
        sendtoDevice(update.encode('UTF-8'), "DOORBELL")
        print("Waiting for update from DOORBELL...")
        updateInfoD = recvMsg(DOORBELLCONN)

        #print("Sending update request to SMARTLOCK...")
        #sendtoDevice(update.encode('UTF-8'), "SMARTLOCK")
        #print("Waiting for update from SMARTLOCK...")
        #updateInfoS = recvMsg(SMARTLOCKCONN)  # waits for response
        #print(updateInfoS)

        # check for motion sensor
        if "t" in updateInfoD:
            print("Motion sensor was triggered!!")
            if requestforMotion == True:
                motiondata = "trig:"
                print("Received a request, sending data...")
                webprocessconn.send(motiondata.encode('UTF-8'))
                requestforMotion = False
            else:
                print("No request received, continuing...")
        elif "n" in updateInfoD:
            print("Motion sensor was not triggered")
        else:
            print("Did not receive an update on motion sensor")
        # check for proximity sensor
        if "h" in updateInfoD:
            print("Proximity sensor was triggered!")
            play(song)
        elif "i" in updateInfoD:
            print("Proximity sensor was not triggered")
        # check is door is locked
        #if "l" in updateInfoS:
        #   print("Smartlock is locked")
        #elif "n" in updateInfoS:
        #    print("Smartlock isn't locked")

        # check for RFID code:
        if "R1234" in updateInfoD:
            # sends unlock command and waits for response
            unlock = 'u'
            sendtoDevice(unlock.encode('UTF-8'), "SMARTLOCK")
            updateInfoSU = recvMsg(SMARTLOCKCONN)
            if "UN" in updateInfoSU:
                print("Successfully unlocked door")
            else:
                print("Did not receive unlock response. Did the door unlock?")

        if userCommand:  # if there is a command, encode it into bytes and send it to requested device
            sendtoDevice(userCommand.encode('UTF-8'), requestedDevice)

            print("Command: " + userCommand + " sent to: " + requestedDevice)

            userCommand = None

            askedUser = False
