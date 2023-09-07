from PySide6.QtCore import QObject, Signal, Slot
import socket
import time


class TCPClient(QObject):
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
        QObject.__init__(self)

        self.ip = ip
        self.port = port
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.settimeout(180)

        self.state = self.STATE_RECEIVING

        self.received = False

    @Slot()
    def start(self):
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
                    except socket.timeout as t_out:
                        self.state = self.STATE_IDLE
                        pass
                    else:
                        if data:
                            self.sig_message.emit(data.decode())
                            self.received = True
                            # self.state = self.STATE_IDLE
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
        # self.state = self.STATE_RECEIVING
        self.tcp_socket.sendall(msg.encode())

    def send_wait(self, msg):
        self.received = False
        # self.state = self.STATE_RECEIVING
        self.tcp_socket.sendall(msg.encode())
        for idx in range(0, 600):
            if self.received:
                return 0
            time.sleep(0.1)
        return 1

    def close(self):
        self.state = self.STATE_DISCONNECT
        self.sig_status.emit(self.STOP, "")
        self.tcp_socket.close()
