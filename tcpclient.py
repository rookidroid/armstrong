"""
This module is used in "ArmStrong" for providing TCP connection with the robot arm.

By: Zhengyu Peng <zhengyu.peng@aptiv.com>

"""

import socket

from PySide6.QtCore import QObject, Signal, Slot


class TCPClient(QObject):
    """
    Represents a TCP client for communication with a server.

    This class provides methods to connect to a server, send and
    receive messages, and handle the status
    of the connection.

    :param str ip: The IP address of the server.
    :param int port: The port number for the connection.

    :ivar ip: The IP address of the server.
    :ivar port: The port number for the connection.
    :ivar tcp_socket: The underlying socket for communication.
    :ivar signal: A signal indicating the status of the client
    (SIG_NORMAL, SIG_STOP, SIG_DISCONNECT).

    :cvar status: A signal indicating the status of the client
    (ERROR, LISTEN, CONNECTED, TIMEOUT, STOP).
    :cvar message: A signal indicating a received message.

    :cvar ERROR: Constant representing an error status.
    :cvar LISTEN: Constant representing a listening status.
    :cvar CONNECTED: Constant representing a connected status.
    :cvar TIMEOUT: Constant representing a timeout status.
    :cvar STOP: Constant representing a stop status.

    :cvar SIG_NORMAL: Constant representing a normal signal.
    :cvar SIG_STOP: Constant representing a stop signal.
    :cvar SIG_DISCONNECT: Constant representing a disconnect signal.
    """

    status = Signal(int, object)
    message = Signal(object)
    ERROR = -1
    LISTEN = 1
    CONNECTED = 2
    TIMEOUT = 3
    STOP = 3

    SIG_NORMAL = 0
    SIG_STOP = 1
    SIG_DISCONNECT = 2

    def __init__(self, ip, port):
        """
        Initialize the TCPClient.

        :param str ip: The IP address of the server.
        :param int port: The port number for the connection.
        """
        QObject.__init__(self)

        self.ip = ip
        self.port = port
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.settimeout(1)

        self.signal = self.SIG_NORMAL

    @Slot()
    def start(self):
        """
        Start the TCP client.

        Connect to the server, handle received messages, and update the status.

        :return: None
        """
        try:
            self.tcp_socket.connect((self.ip, self.port))
        except OSError as err:
            print(err)
            # self.status.emit(self.STOP, '')
        else:
            # print('connected')
            self.status.emit(self.CONNECTED, self.ip)

            while True:
                if self.signal == self.SIG_NORMAL:
                    try:
                        data = self.tcp_socket.recv(4096)
                    except socket.timeout:
                        pass
                    else:
                        if data:
                            self.message.emit(data.decode())
                        else:
                            break
                elif self.signal == self.SIG_DISCONNECT:
                    self.signal = self.SIG_NORMAL
                    self.tcp_socket.close()
                    # self.status.emit(self.STOP, '')
                    break
        finally:
            self.status.emit(self.STOP, "")

    def send(self, msg):
        """
        Send a message to the server.

        :param str msg: The message to send.

        :return: None
        """
        self.tcp_socket.sendall(msg.encode())

    def sendrecv(self, msg):
        """
        Send a message to the server and wait for a response.

        :param str msg: The message to send.

        :return: int
            - 0 if successful.
            - -1 if a timeout occurs.
        """
        self.tcp_socket.sendall(msg.encode())
        try:
            data = self.tcp_socket.recv(4096)
        except socket.timeout:
            return -1
        else:
            if data:
                self.message.emit(data.decode())
                return 0

            return -1

    def close(self):
        """
        Close the TCP client.

        :return: None
        """
        self.signal = self.SIG_DISCONNECT
