import socket
import sys
import select
from pydub import AudioSegment
from pydub.playback import play


#requiredments... pip install playsound

#Plan: python server will act as server and the esps will try to connect to the server, they will send their names through packets

#TEST SEVER OUT!!!!! - done

# have a constant send and recieve between the clients and server for updates

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
update = 'u' # update message to esps

# server
receivingTCP_IP = ""  # it being nothing means any ip can connect, will change to only allow doorbell and smartlock
receivingTCP_PORT = 25566  # the port that the server listens to

# for commands through python server
def sendtoDevice(datainBytes, requestedDevice):
    if (requestedDevice == "SMARTLOCK"):
        SMARTLOCKCONN.send(datainBytes)
        print("Data sent")

    elif (requestedDevice == "DOORBELL"):
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
        data, address = conn.recvfrom(bufferSize) # waits to recieve info (does not matter the size)
        # data is the message received, address is the ip address from the device that sent the message
        data = data.decode('UTF-8')
        if endofMessage in data:
            totalData.append(data[:data.find(endofMessage)]) #the end of the packet has a :, so if you find the : then stop looking for more info
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


if __name__ == "__main__":

    # setup the socket
    sock = socket.socket(socket.AF_INET,  # open socket to internet
                         socket.SOCK_STREAM)  # use TCP

    sock.bind((receivingTCP_IP, receivingTCP_PORT))
    sock.listen(2)

    # first device
    print("Waiting for first to connect...")
    conn1, deviceaddr1 = sock.accept()
    amountofClients = amountofClients + 1
    getDeviceName1 = recvMsg(conn1)  # need to input which device to use

    # second device
    print("Waiting for second device to connect to connect...")
    conn2, deviceaddr2 = sock.accept()
    amountofClients = amountofClients + 1
    getDeviceName2 = recvMsg(conn2)  # device should send bytes identifying itself, recieve msg returns message encoded

    if (getDeviceName1 == "D"):
        DOORBELLCONN = conn1
    elif (getDeviceName1 == "S"):
        SMARTLOCKCONN = conn1

    if (getDeviceName2 == "DOORBELL"):
        DOORBELLCONN = conn2
    elif (getDeviceName2 == "SMARTLOCK"):
        SMARTLOCKCONN = conn2

    # infinite loop
    while True:
        #command funtion

        if not (askedUser):
            print("Enter command (you have 4 seconds): ")

            userCommand, o, e = select.select([sys.stdin], [], [], 4)

            if (userCommand):
                print("Command received: ", sys.stdin.readline().strip())

                if (userCommand == "exit"):
                    conn1.close()
                    conn2.close()
                    Exit()

                print("Enter 1 or 2 for device (1 is SMARTLOCK, 2 is DOORBELL, or choose c for cancel): ")
                requestedDeviceNumber, o, e = select.select([sys.stdin], [], [])

                if (requestedDeviceNumber):
                    if (requestedDeviceNumber == 1):
                        requestedDevice = "SMARTLOCK"
                    elif (requestedDeviceNumber == 2):
                        requestedDevice = "DOORBELL"
                    elif (requestedDeviceNumber == 'c'):
                        requestedDevice = "cancel"
                    else:
                        print("You did not choose correctly. Ignoring command and continuing")
                        userCommand = ''
                        requestedDeviceNumber = ''
                        requestedDevice = ''

                if (userCommand == "cancel" or requestedDevice == "cancel"):  # resets to ask for userCommand
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
        print(updateInfoD)

        print("Sending update request to SMARTLOCK...")
        sendtoDevice(update.encode('UTF-8'), "SMARTLOCK")
        print("Waiting for update from SMARTLOCK...")
        updateInfoS = recvMsg(SMARTLOCKCONN)
        print(updateInfoS)

        #check for motion sensor
        if "t" in updateInfoD:
            print("Motion sensor was triggered!!")
        elif "n" in updateInfoD:
            print("Motion sensor was not triggered")
        #check for proximity sensor
        if "h" in updateInfoD:
            print("Proximity sensor was triggered!")
            play(song)
        elif "i" in updateInfoD:
            print("Proximity sensor was not triggered")
        #check is door is locked
        if "l" in updateInfoS:
            print("Smartlock is locked")
        elif "n" in updateInfoS:
            print("Smartlock isn't locked")

        if (userCommand):  # if there is a command, encode it into bytes and send it to requested device
            sendtoDevice(userCommand.encode('UTF-8'), requestedDevice)

            print("Command: " + usercommand + " sent to: " + requestedDevice)

            askedUser = False
