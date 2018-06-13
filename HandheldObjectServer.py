#!/usr/bin/env python
"""Dummy server than sends data to a client.
Multiple clients allowed
Data is send in packets: "x x x y y y t;"
x, y, t are float numbers.
Not pretty but gets the job done.
q to end all transmissions, <enter> to send empty string and stop single transmission
"""

import socket
import time
import logging
import threading
import random

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')

# dummy data
acceleration = [1, 0, 0]
rotation = [10, 0, 0]
delimiter = ";"

send_data = True
mySocket = socket.socket()


def main():
    global send_data
    threading.Thread(target=startServer, daemon=True).start()
    while (input("q for end, enter to kill connection: ") != 'q'):
        send_data = False
        time.sleep(0.1)
        send_data = True
    mySocket.close()


def startServer():
    global mySocket
    host = "127.0.0.1"
    port = 5000

    mySocket.bind((host, port))

    mySocket.listen(2)
    while True:
        conn, addr = mySocket.accept()
        conn.settimeout(10)
        logging.info("connection from " + str(addr))
        threading.Thread(target=serveSingleClient, args=(conn, addr),
                         daemon=True).start()
        # if not send_data:
        #     mySocket.close()
        #     break


def serveSingleClient(conn, address):
    global send_data
    try:
        while send_data:
            # send fake acceleration data
            acceleration[0] = (random.random() - 0.5) / 3000
            rotation[0] = (random.random() - 0.5) * 20
            message = ''
            for i in acceleration:
                message += str(i) + ' '
            for i in rotation:
                message += str(i) + ' '
            message += str(time.time()) + ' '
            message += delimiter

            conn.send(message.encode())
            time.sleep(1 / 100)
    except socket.error:
        logging.exception("failed to send data")
    finally:
        conn.close()
        logging.info("connection closed")


if __name__ == '__main__':
    main()
