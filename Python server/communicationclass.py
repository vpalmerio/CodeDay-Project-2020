import socket


class Communication:

    def __init__(self):
        self.bufferSize = 1024
        self.endofMessage = ':'
        # server variables

    # for commands through python server
    def sendtoDevice(self, datainBytes, requestedDevice):
        requestedDevice.send(datainBytes)

    def printMesg(self, address, readMessage):
        clientMsg = "Message from Client: {}".format(readMessage)
        clientIP = "Client IP Address: {}".format(address)
        print(clientMsg)
        print(clientIP)

    # receiving messages
    def recvMsg(self, conn):
        totalData = []  # cant guarantee that packets will be split up or put together, so put data received into an array
        bytesRecieved = 0
        while True:
            data, address = conn.recvfrom(self.bufferSize)  # waits to recieve info (does not matter the size)
            # data is the message received, address is the ip address from the device that sent the message
            data = data.decode('UTF-8')
            if self.endofMessage in data:
                totalData.append(data[:data.find(
                    self.endofMessage)])  # the end of the packet has a :, so if you find the : then stop looking for more info
                readMessage = ''.join(totalData)
                self.printMesg(address, readMessage)
                break
            if not (data):
                print("No new data received")
                break
            totalData.append(data)  # if there is no ':' yet, then just add the data to the array until there is a ':'
            bytesRecieved = bytesRecieved + len(totalData)
            readMessage = ''.join(totalData)
            self.printMesg(address, readMessage)
        return ''.join(totalData)  # returns all elements of total data as a string
