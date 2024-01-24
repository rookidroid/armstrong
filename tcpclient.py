import time
import socket

from PySide6.QtCore import QObject, Signal, Slot


class TCPClient(QObject):
    """
    A class representing a TCP client for socket communication.

    This class provides functionality for establishing a TCP connection, sending messages,
    receiving messages, and handling various states of the TCP client.

    Signals:
        - `sig_status`: Signal emitted when the status of the TCP client changes.
        - `sig_message`: Signal emitted when a message is received.
        - `sig_error`: Signal emitted when an error occurs.

    Constants:
        - `ERROR`: Error status code.
        - `LISTEN`: Listen status code.
        - `CONNECTED`: Connected status code.
        - `TIMEOUT`: Timeout status code.
        - `STOP`: Stop status code.

        - `STATE_IDLE`: Idle state code.
        - `STATE_STOP`: Stop state code.
        - `STATE_DISCONNECT`: Disconnect state code.
        - `STATE_RECEIVING`: Receiving state code.

    Attributes:
        - `ip`: The IP address of the server.
        - `port`: The port number for the connection.
        - `tcp_socket`: The TCP socket used for communication.
        - `state`: The current state of the TCP client.
        - `received`: Flag indicating whether a message has been received.

    Methods:
        - `start`: Start the TCP client and establish a connection.
        - `send`: Send a message to the server.
        - `send_wait`: Send a message to the server and wait for a response.
        - `close`: Close the TCP connection.

    Example:
    ```python
    tcp_client = TCPClient("127.0.0.1", 8080)
    tcp_client.start()
    tcp_client.send("Hello, Server!")
    ```
    """

    sig_status = Signal(int, object)
    sig_message = Signal(object)
    sig_error = Signal(object)
    ERROR = -1
    LISTEN = 1
    CONNECTED = 2
    TIMEOUT = 3
    STOP = 3

    STATE_IDLE = 0
    STATE_STOP = 1
    STATE_DISCONNECT = 2
    STATE_RECEIVING = 3

    def __init__(self, ip, port):
        """
        Initialize the TCPClient.

        :param ip: The IP address of the server.
        :type ip: str
        :param port: The port number for the connection.
        :type port: int
        """
        QObject.__init__(self)

        self.ip = ip
        self.port = port
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.settimeout(180)

        self.state = self.STATE_IDLE

        self.received = False

    @Slot()
    def start(self):
        """
        Start the TCP client and establish a connection.

        This method attempts to connect to the server and handles the connection status.

        :return: None
        """
        try:
            self.tcp_socket.connect((self.ip, self.port))
        except OSError as err:
            # print(err)
            self.sig_error.emit(
                "Unable to establish a connection with "
                + self.ip
                + ":"
                + str(self.port)
                + ". "
                + str(err)
            )
            # self.sig_status.emit(self.STOP, '')
        else:
            # print('connected')
            self.sig_status.emit(self.CONNECTED, self.ip)

            while True:
                if self.state == self.STATE_IDLE:
                    time.sleep(0.1)
                elif self.state == self.STATE_RECEIVING:
                    # time.sleep(1)
                    try:
                        data = self.tcp_socket.recv(4096)
                    except socket.timeout:
                        self.state = self.STATE_IDLE
                    else:
                        if data:
                            self.sig_message.emit(data.decode())
                            self.received = True
                            self.state = self.STATE_IDLE
                        else:
                            break
                elif self.state == self.STATE_DISCONNECT:
                    self.state = self.STATE_IDLE
                    self.tcp_socket.close()
                    # self.sig_status.emit(self.STOP, '')
                    break
        finally:
            self.sig_status.emit(self.STOP, "")

    def send(self, msg):
        """
        Send a message to the server.

        This method sends the provided message to the server.

        :param msg: The message to be sent.
        :type msg: str

        :return: None
        """
        self.state = self.STATE_RECEIVING
        self.tcp_socket.sendall(msg.encode())

    def send_wait(self, msg):
        """
        Send a message to the server and wait for a response.

        This method sends the provided message to the server and waits for a response.
        It returns 0 if a response is received within the specified time, otherwise 1.

        :param msg: The message to be sent.
        :type msg: str

        :return: 0 if a response is received, 1 if not.
        :rtype: int
        """
        self.received = False
        self.state = self.STATE_RECEIVING
        self.tcp_socket.sendall(msg.encode())
        # try:
        #     data = self.tcp_socket.recv(4096)
        # except socket.timeout as t_out:
        #     return 1
        # else:
        #     if data:
        #         self.sig_message.emit(data.decode())
        #         return 0
        #     else:
        #         return 1
        for idx in range(0, 600):
            if self.received:
                return 0
            time.sleep(0.1)
        return 1

    def close(self):
        """
        Close the TCP connection.

        This method initiates the closing of the TCP connection.

        :return: None
        """
        self.state = self.STATE_DISCONNECT
        self.sig_status.emit(self.STOP, "")
        self.tcp_socket.close()
