#!/usr/bin/env python
from flask import Flask, send_from_directory
import socket
import os
import communicationclass

#tasks: implement log in page and sensor data

# website ip and port to connect to python server
TCP_IP = '127.0.0.1'
TCP_PORT = 8079

app = Flask(__name__)


@app.route("/")
def about():
    return app.send_static_file('main3.html')

@app.route("/LoginToDing")
def login():
    return app.send_static_file('login.html')

@app.route("/lock")
def lock():
    MESSAGE = "l"
    s.send(MESSAGE.encode('UTF-8'))
    print("Lock command sent to server")
    return app.send_static_file('lock.html')


@app.route("/unlock")
def unlocked():
    MESSAGE = "u"
    s.send(MESSAGE.encode('UTF-8'))
    print("Unlock command sent to server")
    return app.send_static_file('unlock.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route("/VideoFeed")
def video():

    return app.send_static_file('newfeed.html')


@app.route("/sensordata")
def sensordata():
    MESSAGE = "s"
    print("Sending update request")
    s.send(MESSAGE.encode('UTF-8'))
    print("waiting for a response")
    sensorupdate = comm.recvMsg(s)
    if sensorupdate == 'trig':
        return app.send_static_file('sensoractivated.html')
    elif sensorupdate == 'not':
        return app.send_static_file('sensornotactivated.html')


if __name__ == "__main__":
    # create communication class object
    comm = communicationclass.Communication()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Trying to connect to python server...")
    s.connect((TCP_IP, TCP_PORT))
    print("Connected, starting webserver")
    app.run(host='127.0.0.1', port=80)
