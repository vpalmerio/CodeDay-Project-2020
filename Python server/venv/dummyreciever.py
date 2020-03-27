import socket
TCP_IP = '127.0.0.1'
TCP_PORT = 25566
BUFFER_SIZE = 1024
MESSAGE = "D:"
newmessage = "openseaseme:"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
s.send(MESSAGE.encode('UTF-8'))
while True:
    newmessage = str(input("Enter receiver command: "))
    if newmessage == "cancel":
        break
    newmessage = newmessage + ':'

    data = s.recv(BUFFER_SIZE)
    data = data.decode('UTF-8')
    print(data)
    print("received data: ", data)
    if data == "update:":
        # the first letter will be t or n, triggered or not, for motion sensor
        # the second letter will be h or i, triggered or not, for proximity sensor
        newmessage = "th:"
        s.send(newmessage.encode('UTF-8'))
    else:
        s.send(newmessage.encode('UTF-8'))

s.close()