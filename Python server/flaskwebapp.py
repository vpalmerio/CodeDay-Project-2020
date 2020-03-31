#!/usr/bin/env python
from flask import Flask, send_from_directory
import socket
import os

#tasks: implement log in page and sensor data

# website ip and port to connect to python server
TCP_IP = '127.0.0.1'
TCP_PORT = 8079
bufferSize = 1024
endofMessage = ':'

def printMsg(address, readMessage):
    clientMsg = "Message from Client: {}".format(readMessage)
    clientIP = "Client IP Address: {}".format(address)
    print(clientMsg)
    print(clientIP)

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

app = Flask(__name__)


@app.route("/")
def about():
    print("No commands sent")
    return app.send_static_file('main.html')


@app.route("/lock")
def lock():
    MESSAGE = "l:"
    # s.send(MESSAGE.encode('UTF-8'))
    print("Lock command sent to server")
    return app.send_static_file('lock.html')


@app.route("/unlock")
def unlocked():
    MESSAGE = "u:"
    s.send(MESSAGE.encode('UTF-8'))
    print("Unlock command sent to server")
    return app.send_static_file('unlock.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route("/VideoFeed")
def video():

    return app.send_static_file('videofeed.html')


@app.route("/sensordata")
def sensordata():
    MESSAGE = "s"
    print("Sending update request")
    s.send(MESSAGE.encode('UTF-8'))
    print("waiting for a response")
    sensorupdate = recvMsg(s)
    if sensorupdate == 'trig':
        return app.send_static_file('sensoractivated.html')
    elif sensorupdate == 'not':
        return


if __name__ == "__main__":
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Trying to connect to python server...")
    s.connect((TCP_IP, TCP_PORT))
    print("Connected, starting webserver")
    app.run(host='0.0.0.0', port=8080)
