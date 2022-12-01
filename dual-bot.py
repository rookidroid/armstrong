import sys
import math
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt
from PySide6.QtCore import QThread, QFile
from PySide6.QtUiTools import QUiLoader

from pathlib import Path
import json

from tcpclient import TCPClient

AZ_CENTER_THOD = 0
AZ_EDGE_THOD = 28
EL_UP_THOD = -2


class MyApp(QtWidgets.QMainWindow):

    def __init__(self):
        super(MyApp, self).__init__()

        self.version = 'v1.0'

        config_file = Path('config.json')
        if config_file.exists():
            self.config = json.load(open('config.json', 'r'))
        else:
            self.config = dict()
            json.dump(self.config, open('config.json', 'w+'))

        """Load UI"""
        ui_file_name = "mainwindow.ui"
        ui_file = QFile(ui_file_name)
        loader = QUiLoader()
        self.ui = loader.load(ui_file)
        ui_file.close()
        self.init_ui()

        self.ui.pushButton_connect_r.clicked.connect(
            self.on_connect_button_clicked_right)
        self.ui.doubleSpinBox_az_r.valueChanged.connect(
            self.spinbox_az_r)
        self.ui.horizontalSlider_az_r.valueChanged.connect(
            self.slider_az_r)
        self.ui.doubleSpinBox_el_rl.valueChanged.connect(
            self.spinbox_el_rl)
        self.ui.verticalSlider_el_rl.valueChanged.connect(
            self.slider_el_rl)
        self.ui.dial_pol_r.valueChanged.connect(
            self.dial_pol_r)
        self.ui.doubleSpinBox_pol_r.valueChanged.connect(
            self.spinbox_pol_r)
        self.ui.pushButton_home_r.clicked.connect(
            self.on_home_button_clicked_right)
        self.ui.pushButton_set_r.clicked.connect(
            self.on_set_button_clicked_right)

        #######################################
        self.ui.pushButton_connect_l.clicked.connect(
            self.on_connect_button_clicked_left)
        self.ui.doubleSpinBox_az_l.valueChanged.connect(
            self.spinbox_az_l)
        self.ui.horizontalSlider_az_l.valueChanged.connect(
            self.slider_az_l)
        self.ui.doubleSpinBox_el_ll.valueChanged.connect(
            self.spinbox_el_ll)
        self.ui.verticalSlider_el_ll.valueChanged.connect(
            self.slider_el_ll)
        self.ui.dial_pol_l.valueChanged.connect(
            self.dial_pol_l)
        self.ui.doubleSpinBox_pol_l.valueChanged.connect(
            self.spinbox_pol_l)
        self.ui.pushButton_home_l.clicked.connect(
            self.on_home_button_clicked_left)
        self.ui.pushButton_set_l.clicked.connect(
            self.on_set_button_clicked_left)

        self.ui.show()

    def init_ui(self):
        self.ui.groupBox_r.setEnabled(False)
        self.ui.groupBox_l.setEnabled(False)

        self.ui.statusbar.showMessage(self.version)

        # TCP Client
        self.config['IP_RIGHT'] = self.config.get('IP_RIGHT', '192.168.0.32')
        self.config['CTRL_PORT_RIGHT'] = self.config.get(
            'CTRL_PORT_RIGHT', 10002)
        self.config['CMD_PORT_RIGHT'] = self.config.get(
            'CMD_PORT_RIGHT', 10003)
        self.config['SPEED_RIGHT'] = self.config.get('SPEED_RIGHT', 25)

        self.config['IP_LEFT'] = self.config.get('IP_LEFT', '192.168.0.33')
        self.config['CTRL_PORT_LEFT'] = self.config.get(
            'CTRL_PORT_LEFT', 10002)
        self.config['CMD_PORT_LEFT'] = self.config.get(
            'CMD_PORT_LEFT', 10003)
        self.config['SPEED_LEFT'] = self.config.get('SPEED_LEFT', 25)

        self.ui.lineEdit_ip_r.setText(self.config['IP_RIGHT'])
        self.ui.doubleSpinBox_ctrl_r.setValue(self.config['CTRL_PORT_RIGHT'])
        self.ui.doubleSpinBox_cmd_r.setValue(self.config['CMD_PORT_RIGHT'])
        self.ui.doubleSpinBox_speed_r.setValue(self.config['SPEED_RIGHT'])

        self.ui.lineEdit_ip_l.setText(self.config['IP_LEFT'])
        self.ui.doubleSpinBox_ctrl_l.setValue(self.config['CTRL_PORT_LEFT'])
        self.ui.doubleSpinBox_cmd_l.setValue(self.config['CMD_PORT_LEFT'])
        self.ui.doubleSpinBox_speed_l.setValue(self.config['SPEED_LEFT'])

        self.save_config()

    def save_config(self):
        try:
            json.dump(self.config, open('config.json', 'w+'))
        except PermissionError as err:
            pass

    def on_connect_button_clicked_right(self):
        if self.ui.pushButton_connect_r.text() == 'Connect and Initialize':
            self.ui.pushButton_connect_r.setEnabled(False)

            self.ui.lineEdit_ip_r.setEnabled(False)
            self.ui.doubleSpinBox_ctrl_r.setEnabled(False)
            self.ui.doubleSpinBox_cmd_r.setEnabled(False)

            self.ctrl_thread_r = QThread()
            self.ctrl_socket_r = TCPClient(
                self.ui.lineEdit_ip_r.text(),
                int(self.ui.doubleSpinBox_ctrl_r.value()))

            self.ctrl_socket_r.status.connect(self.on_ctrl_status_update_right)
            self.ctrl_socket_r.message.connect(
                self.on_tcp_client_message_ready_right)
            self.ctrl_thread_r.started.connect(self.ctrl_socket_r.start)
            self.ctrl_socket_r.moveToThread(self.ctrl_thread_r)
            self.ctrl_thread_r.start()

        elif self.ui.pushButton_connect_r.text() == 'Stop and Disconnect':

            self.display_message_right('1;1;STOP')
            self.ctrl_socket_r.sendrecv('1;1;STOP')
            self.display_message_right('1;1;SRVOFF')
            self.ctrl_socket_r.sendrecv('1;1;SRVOFF')
            self.display_message_right('1;1;CNTLOFF')
            self.ctrl_socket_r.sendrecv('1;1;CNTLOFF')
            self.display_message_right('1;1;CLOSE')
            self.ctrl_socket_r.sendrecv('1;1;CLOSE')

            self.ui.pushButton_connect_r.setEnabled(False)
            self.ctrl_socket_r.close()
            self.cmd_socket_r.close()

    def on_ctrl_status_update_right(self, status, addr):
        if status == TCPClient.STOP:
            self.ui.pushButton_connect_r.setText('Connect and Initialize')

            self.ctrl_socket_r.status.disconnect()
            self.ctrl_socket_r.message.disconnect()
            self.ctrl_thread_r.quit()

            self.ui.lineEdit_ip_r.setEnabled(True)
            self.ui.doubleSpinBox_ctrl_r.setEnabled(True)
            self.ui.doubleSpinBox_cmd_r.setEnabled(True)

            self.ui.groupBox_r.setEnabled(False)

            self.ui.pushButton_connect_r.setEnabled(True)

        elif status == TCPClient.CONNECTED:
            self.connect_cmd_port_right()

    def connect_cmd_port_right(self):
        self.cmd_thread_r = QThread()
        self.cmd_socket_r = TCPClient(
            self.ui.lineEdit_ip_r.text(),
            int(self.ui.doubleSpinBox_cmd_r.value()))

        self.cmd_socket_r.status.connect(self.on_cmd_status_update_right)
        self.cmd_socket_r.message.connect(
            self.on_tcp_client_message_ready_right)
        self.cmd_thread_r.started.connect(self.cmd_socket_r.start)
        self.cmd_socket_r.moveToThread(self.cmd_thread_r)
        self.cmd_thread_r.start()

    def on_cmd_status_update_right(self, status, addr):
        if status == TCPClient.STOP:
            self.ctrl_socket_r.close()

            self.ui.pushButton_connect_r.setText('Connect and Initialize')

            self.cmd_socket_r.status.disconnect()
            self.cmd_socket_r.message.disconnect()
            self.cmd_thread_r.quit()

            self.ui.lineEdit_ip_r.setEnabled(True)
            self.ui.doubleSpinBox_ctrl_r.setEnabled(True)
            self.ui.doubleSpinBox_cmd_r.setEnabled(True)

            self.ui.pushButton_connect_r.setEnabled(False)

        elif status == TCPClient.CONNECTED:
            self.config['IP_RIGHT'] = self.ui.lineEdit_ip_r.text()
            self.config['CTRL_PORT_RIGHT'] = \
                self.ui.doubleSpinBox_ctrl_r.value()
            self.config['CMD_PORT_RIGHT'] = \
                self.ui.doubleSpinBox_cmd_r.value()
            self.save_config()

            success = 0
            self.display_message_right('1;1;RSTALRM')
            success += self.ctrl_socket_r.sendrecv('1;1;RSTALRM')
            self.display_message_right('1;1;STOP')
            success += self.ctrl_socket_r.sendrecv('1;1;STOP')
            self.display_message_right('1;1;OPEN=')
            success += self.ctrl_socket_r.sendrecv('1;1;OPEN=')
            self.display_message_right('1;1;CNTLON')
            success += self.ctrl_socket_r.sendrecv('1;1;CNTLON')
            self.display_message_right('1;1;SRVON')
            success += self.ctrl_socket_r.sendrecv('1;1;SRVON')
            self.display_message_right('1;1;RUN')
            success += self.ctrl_socket_r.sendrecv('1;1;RUN')

            if success == 0:
                self.config['SPEED_RIGHT'] = \
                    self.ui.doubleSpinBox_speed_r.value()
                self.save_config()

                # self.ui.groupBox_r.setEnabled(True)

                msg = '6.0\r\n'
                self.display_message_right(msg)
                self.cmd_socket_r.sendrecv(msg)

            self.ui.pushButton_connect_r.setText('Stop and Disconnect')
        self.ui.pushButton_connect_r.setEnabled(True)

    def on_tcp_client_message_ready_right(self, msg):
        msg_list = msg.split()
        if msg_list[0] == '+6' or msg_list[0] == '+2':
            print('query')
            az = float(msg_list[1])
            el = float(msg_list[2])
            pol = float(msg_list[3])
            self.ui.doubleSpinBox_az_r.setValue(az)
            self.ui.doubleSpinBox_el_rl.setValue(el)
            self.ui.doubleSpinBox_pol_r.setValue(pol)

            self.ui.groupBox_r.setEnabled(True)
            self.ui.groupBox_rightbot.setEnabled(True)

        self.ui.textBrowser_r.append(
            '<p style="text-align: center;">' +
            '<span style="color: #2196F3;"><strong>' +
            'Received: ' +
            '</strong></span>' +
            '<span style="color: #2196F3;">' +
            msg +
            '</span></p>')

    def spinbox_az_r(self, val):
        self.ui.horizontalSlider_az_r.setValue(val*10)
        if abs(val) <= AZ_CENTER_THOD:
            self.ui.verticalSlider_el_rl.setEnabled(True)
            self.ui.doubleSpinBox_el_rl.setEnabled(True)
            self.ui.verticalSlider_el_rr.setEnabled(False)
            self.ui.doubleSpinBox_el_rr.setEnabled(False)

            self.ui.verticalSlider_el_rl.setMaximum(50)
            self.ui.doubleSpinBox_el_rl.setMaximum(5)

            self.ui.verticalSlider_el_rr.setMaximum(50)
            self.ui.doubleSpinBox_el_rr.setMaximum(5)
        elif abs(val) >= AZ_EDGE_THOD:
            self.ui.verticalSlider_el_rl.setEnabled(False)
            self.ui.doubleSpinBox_el_rl.setEnabled(False)
            self.ui.verticalSlider_el_rr.setEnabled(True)
            self.ui.doubleSpinBox_el_rr.setEnabled(True)

            self.ui.verticalSlider_el_rl.setMaximum(50)
            self.ui.doubleSpinBox_el_rl.setMaximum(5)

            self.ui.verticalSlider_el_rr.setMaximum(50)
            self.ui.doubleSpinBox_el_rr.setMaximum(5)
        else:
            self.ui.verticalSlider_el_rl.setEnabled(True)
            self.ui.doubleSpinBox_el_rl.setEnabled(True)
            self.ui.verticalSlider_el_rr.setEnabled(True)
            self.ui.doubleSpinBox_el_rr.setEnabled(True)

            self.ui.verticalSlider_el_rl.setMaximum(EL_UP_THOD*10)
            self.ui.doubleSpinBox_el_rl.setMaximum(EL_UP_THOD)

            self.ui.verticalSlider_el_rr.setMaximum(EL_UP_THOD*10)
            self.ui.doubleSpinBox_el_rr.setMaximum(EL_UP_THOD)
        self.ui.pushButton_set_r.setEnabled(True)

    def slider_az_r(self, val):
        self.ui.doubleSpinBox_az_r.setValue(val/10)

        if abs(val/10) <= AZ_CENTER_THOD:
            self.ui.verticalSlider_el_rl.setEnabled(True)
            self.ui.doubleSpinBox_el_rl.setEnabled(True)
            self.ui.verticalSlider_el_rr.setEnabled(False)
            self.ui.doubleSpinBox_el_rr.setEnabled(False)

            self.ui.verticalSlider_el_rl.setMaximum(50)
            self.ui.doubleSpinBox_el_rl.setMaximum(5)

            self.ui.verticalSlider_el_rr.setMaximum(50)
            self.ui.doubleSpinBox_el_rr.setMaximum(5)
        elif abs(val/10) >= AZ_EDGE_THOD:
            self.ui.verticalSlider_el_rl.setEnabled(False)
            self.ui.doubleSpinBox_el_rl.setEnabled(False)
            self.ui.verticalSlider_el_rr.setEnabled(True)
            self.ui.doubleSpinBox_el_rr.setEnabled(True)

            self.ui.verticalSlider_el_rl.setMaximum(50)
            self.ui.doubleSpinBox_el_rl.setMaximum(5)

            self.ui.verticalSlider_el_rr.setMaximum(50)
            self.ui.doubleSpinBox_el_rr.setMaximum(5)
        else:
            self.ui.verticalSlider_el_rl.setEnabled(True)
            self.ui.doubleSpinBox_el_rl.setEnabled(True)
            self.ui.verticalSlider_el_rr.setEnabled(True)
            self.ui.doubleSpinBox_el_rr.setEnabled(True)

            self.ui.verticalSlider_el_rl.setMaximum(EL_UP_THOD*10)
            self.ui.doubleSpinBox_el_rl.setMaximum(EL_UP_THOD)

            self.ui.verticalSlider_el_rr.setMaximum(EL_UP_THOD*10)
            self.ui.doubleSpinBox_el_rr.setMaximum(EL_UP_THOD)
        self.ui.pushButton_set_r.setEnabled(True)

    def spinbox_el_rl(self, val):
        self.ui.verticalSlider_el_rl.setValue(val*10)
        if val <= EL_UP_THOD:
            self.ui.doubleSpinBox_az_r.setEnabled(True)
            self.ui.horizontalSlider_az_r.setEnabled(True)
        else:
            self.ui.doubleSpinBox_az_r.setEnabled(False)
            self.ui.horizontalSlider_az_r.setEnabled(False)
        self.ui.pushButton_set_r.setEnabled(True)

    def slider_el_rl(self, val):
        self.ui.doubleSpinBox_el_rl.setValue(val/10)
        if val/10 <= EL_UP_THOD:
            self.ui.doubleSpinBox_az_r.setEnabled(True)
            self.ui.horizontalSlider_az_r.setEnabled(True)
        else:
            self.ui.doubleSpinBox_az_r.setEnabled(False)
            self.ui.horizontalSlider_az_r.setEnabled(False)
        self.ui.pushButton_set_r.setEnabled(True)

    def dial_pol_r(self, val):
        self.ui.doubleSpinBox_pol_r.setValue(val)
        self.ui.pushButton_set_r.setEnabled(True)

    def spinbox_pol_r(self, val):
        self.ui.dial_pol_r.setValue(int(val))
        self.ui.pushButton_set_r.setEnabled(True)

    def on_home_button_clicked_right(self):
        self.ui.groupBox_rightbot.setEnabled(False)
        msg = '1.0\r\n'
        self.display_message_right(msg)
        self.cmd_socket_r.send(msg)

    def on_set_button_clicked_right(self):
        self.ui.groupBox_rightbot.setEnabled(False)
        self.ui.pushButton_set_r.setEnabled(False)
        msg = '2.0 ' +\
            str(self.ui.doubleSpinBox_az_r.value())+' ' +\
            str(self.ui.doubleSpinBox_el_rl.value())+' ' +\
            str(self.ui.doubleSpinBox_pol_r.value())+' ' +\
            str(self.ui.doubleSpinBox_speed_r.value())+'\r\n'
        self.display_message_right(msg)
        self.cmd_socket_r.send(msg)

    def display_message_right(self, msg):
        self.ui.textBrowser_r.append(
            '<p style="text-align: left;">' +
            '<span style="color: #000000;"><strong>' +
            'Sent: ' +
            '</strong></span>' +
            '<span style="color: #000000;">' +
            msg +
            '</span></p>')

    ##########################################################
    def on_connect_button_clicked_left(self):
        if self.ui.pushButton_connect_l.text() == 'Connect and Initialize':
            self.ui.pushButton_connect_l.setEnabled(False)

            self.ui.lineEdit_ip_l.setEnabled(False)
            self.ui.doubleSpinBox_ctrl_l.setEnabled(False)
            self.ui.doubleSpinBox_cmd_l.setEnabled(False)

            self.ctrl_thread_l = QThread()
            self.ctrl_socket_l = TCPClient(
                self.ui.lineEdit_ip_l.text(),
                int(self.ui.doubleSpinBox_ctrl_l.value()))

            self.ctrl_socket_l.status.connect(self.on_ctrl_status_update_left)
            self.ctrl_socket_l.message.connect(
                self.on_tcp_client_message_ready_left)
            self.ctrl_thread_l.started.connect(self.ctrl_socket_l.start)
            self.ctrl_socket_l.moveToThread(self.ctrl_thread_l)
            self.ctrl_thread_l.start()

        elif self.ui.pushButton_connect_l.text() == 'Stop and Disconnect':

            self.display_message_left('1;1;STOP')
            self.ctrl_socket_l.sendrecv('1;1;STOP')
            self.display_message_left('1;1;SRVOFF')
            self.ctrl_socket_l.sendrecv('1;1;SRVOFF')
            self.display_message_left('1;1;CNTLOFF')
            self.ctrl_socket_l.sendrecv('1;1;CNTLOFF')
            self.display_message_left('1;1;CLOSE')
            self.ctrl_socket_l.sendrecv('1;1;CLOSE')

            self.ui.pushButton_connect_l.setEnabled(False)
            self.ctrl_socket_l.close()
            self.cmd_socket_l.close()

    def on_ctrl_status_update_left(self, status, addr):
        if status == TCPClient.STOP:
            self.ui.pushButton_connect_l.setText('Connect and Initialize')

            self.ctrl_socket_l.status.disconnect()
            self.ctrl_socket_l.message.disconnect()
            self.ctrl_thread_l.quit()

            self.ui.lineEdit_ip_l.setEnabled(True)
            self.ui.doubleSpinBox_ctrl_l.setEnabled(True)
            self.ui.doubleSpinBox_cmd_l.setEnabled(True)

            self.ui.groupBox_l.setEnabled(False)

            self.ui.pushButton_connect_l.setEnabled(True)

        elif status == TCPClient.CONNECTED:
            self.connect_cmd_port_left()

    def connect_cmd_port_left(self):
        self.cmd_thread_l = QThread()
        self.cmd_socket_l = TCPClient(
            self.ui.lineEdit_ip_l.text(),
            int(self.ui.doubleSpinBox_cmd_l.value()))

        self.cmd_socket_l.status.connect(self.on_cmd_status_update_left)
        self.cmd_socket_l.message.connect(
            self.on_tcp_client_message_ready_left)
        self.cmd_thread_l.started.connect(self.cmd_socket_l.start)
        self.cmd_socket_l.moveToThread(self.cmd_thread_l)
        self.cmd_thread_l.start()

    def on_cmd_status_update_left(self, status, addr):
        if status == TCPClient.STOP:
            self.ctrl_socket_l.close()

            self.ui.pushButton_connect_l.setText('Connect and Initialize')

            self.cmd_socket_l.status.disconnect()
            self.cmd_socket_l.message.disconnect()
            self.cmd_thread_l.quit()

            self.ui.lineEdit_ip_l.setEnabled(True)
            self.ui.doubleSpinBox_ctrl_l.setEnabled(True)
            self.ui.doubleSpinBox_cmd_l.setEnabled(True)

            self.ui.pushButton_connect_l.setEnabled(False)

        elif status == TCPClient.CONNECTED:
            self.config['IP_LEFT'] = self.ui.lineEdit_ip_l.text()
            self.config['CTRL_PORT_LEFT'] = \
                self.ui.doubleSpinBox_ctrl_l.value()
            self.config['CMD_PORT_LEFT'] = \
                self.ui.doubleSpinBox_cmd_l.value()
            self.save_config()

            success = 0
            self.display_message_left('1;1;RSTALRM')
            success += self.ctrl_socket_l.sendrecv('1;1;RSTALRM')
            self.display_message_left('1;1;STOP')
            success += self.ctrl_socket_l.sendrecv('1;1;STOP')
            self.display_message_left('1;1;OPEN=')
            success += self.ctrl_socket_l.sendrecv('1;1;OPEN=')
            self.display_message_left('1;1;CNTLON')
            success += self.ctrl_socket_l.sendrecv('1;1;CNTLON')
            self.display_message_left('1;1;SRVON')
            success += self.ctrl_socket_l.sendrecv('1;1;SRVON')
            self.display_message_left('1;1;RUN')
            success += self.ctrl_socket_l.sendrecv('1;1;RUN')

            if success == 0:
                self.config['SPEED_LEFT'] = \
                    self.ui.doubleSpinBox_speed_l.value()
                self.save_config()

                # self.ui.groupBox_l.setEnabled(True)

                msg = '6.0\r\n'
                self.display_message_left(msg)
                self.cmd_socket_l.sendrecv(msg)

            self.ui.pushButton_connect_l.setText('Stop and Disconnect')
        self.ui.pushButton_connect_l.setEnabled(True)

    def on_tcp_client_message_ready_left(self, msg):
        msg_list = msg.split()
        if msg_list[0] == '+6' or msg_list[0] == '+2':
            print('query')
            az = float(msg_list[1])
            el = float(msg_list[2])
            pol = float(msg_list[3])
            self.ui.doubleSpinBox_az_l.setValue(az)
            self.ui.doubleSpinBox_el_ll.setValue(el)
            self.ui.doubleSpinBox_pol_l.setValue(pol)

            self.ui.groupBox_l.setEnabled(True)
            self.ui.groupBox_leftbot.setEnabled(True)

        self.ui.textBrowser_l.append(
            '<p style="text-align: center;">' +
            '<span style="color: #2196F3;"><strong>' +
            'Received: ' +
            '</strong></span>' +
            '<span style="color: #2196F3;">' +
            msg +
            '</span></p>')

    def spinbox_az_l(self, val):
        self.ui.horizontalSlider_az_l.setValue(val*10)
        if abs(val) <= AZ_CENTER_THOD:
            self.ui.verticalSlider_el_ll.setEnabled(True)
            self.ui.doubleSpinBox_el_ll.setEnabled(True)
            self.ui.verticalSlider_el_lr.setEnabled(False)
            self.ui.doubleSpinBox_el_lr.setEnabled(False)

            self.ui.verticalSlider_el_ll.setMaximum(50)
            self.ui.doubleSpinBox_el_ll.setMaximum(5)

            self.ui.verticalSlider_el_lr.setMaximum(50)
            self.ui.doubleSpinBox_el_lr.setMaximum(5)
        elif abs(val) >= AZ_EDGE_THOD:
            self.ui.verticalSlider_el_ll.setEnabled(False)
            self.ui.doubleSpinBox_el_ll.setEnabled(False)
            self.ui.verticalSlider_el_lr.setEnabled(True)
            self.ui.doubleSpinBox_el_lr.setEnabled(True)

            self.ui.verticalSlider_el_ll.setMaximum(50)
            self.ui.doubleSpinBox_el_ll.setMaximum(5)

            self.ui.verticalSlider_el_lr.setMaximum(50)
            self.ui.doubleSpinBox_el_lr.setMaximum(5)
        else:
            self.ui.verticalSlider_el_ll.setEnabled(True)
            self.ui.doubleSpinBox_el_ll.setEnabled(True)
            self.ui.verticalSlider_el_lr.setEnabled(True)
            self.ui.doubleSpinBox_el_lr.setEnabled(True)

            self.ui.verticalSlider_el_ll.setMaximum(EL_UP_THOD*10)
            self.ui.doubleSpinBox_el_ll.setMaximum(EL_UP_THOD)

            self.ui.verticalSlider_el_lr.setMaximum(EL_UP_THOD*10)
            self.ui.doubleSpinBox_el_lr.setMaximum(EL_UP_THOD)
        self.ui.pushButton_set_l.setEnabled(True)

    def slider_az_l(self, val):
        self.ui.doubleSpinBox_az_l.setValue(val/10)

        if abs(val/10) <= AZ_CENTER_THOD:
            self.ui.verticalSlider_el_ll.setEnabled(False)
            self.ui.doubleSpinBox_el_ll.setEnabled(False)
            self.ui.verticalSlider_el_lr.setEnabled(True)
            self.ui.doubleSpinBox_el_lr.setEnabled(True)

            self.ui.verticalSlider_el_ll.setMaximum(50)
            self.ui.doubleSpinBox_el_ll.setMaximum(5)

            self.ui.verticalSlider_el_lr.setMaximum(50)
            self.ui.doubleSpinBox_el_lr.setMaximum(5)
        elif abs(val/10) >= AZ_EDGE_THOD:
            self.ui.verticalSlider_el_ll.setEnabled(True)
            self.ui.doubleSpinBox_el_ll.setEnabled(True)
            self.ui.verticalSlider_el_lr.setEnabled(False)
            self.ui.doubleSpinBox_el_lr.setEnabled(False)

            self.ui.verticalSlider_el_ll.setMaximum(50)
            self.ui.doubleSpinBox_el_ll.setMaximum(5)

            self.ui.verticalSlider_el_lr.setMaximum(50)
            self.ui.doubleSpinBox_el_lr.setMaximum(5)
        else:
            self.ui.verticalSlider_el_ll.setEnabled(True)
            self.ui.doubleSpinBox_el_ll.setEnabled(True)
            self.ui.verticalSlider_el_lr.setEnabled(True)
            self.ui.doubleSpinBox_el_lr.setEnabled(True)

            self.ui.verticalSlider_el_ll.setMaximum(EL_UP_THOD*10)
            self.ui.doubleSpinBox_el_ll.setMaximum(EL_UP_THOD)

            self.ui.verticalSlider_el_lr.setMaximum(EL_UP_THOD*10)
            self.ui.doubleSpinBox_el_lr.setMaximum(EL_UP_THOD)
        self.ui.pushButton_set_l.setEnabled(True)

    def spinbox_el_ll(self, val):
        self.ui.verticalSlider_el_ll.setValue(val*10)
        if val <= EL_UP_THOD:
            self.ui.doubleSpinBox_az_l.setEnabled(True)
            self.ui.horizontalSlider_az_l.setEnabled(True)
        else:
            self.ui.doubleSpinBox_az_l.setEnabled(False)
            self.ui.horizontalSlider_az_l.setEnabled(False)
        self.ui.pushButton_set_l.setEnabled(True)

    def slider_el_ll(self, val):
        self.ui.doubleSpinBox_el_ll.setValue(val/10)
        if val/10 <= EL_UP_THOD:
            self.ui.doubleSpinBox_az_l.setEnabled(True)
            self.ui.horizontalSlider_az_l.setEnabled(True)
        else:
            self.ui.doubleSpinBox_az_l.setEnabled(False)
            self.ui.horizontalSlider_az_l.setEnabled(False)
        self.ui.pushButton_set_l.setEnabled(True)

    def dial_pol_l(self, val):
        self.ui.doubleSpinBox_pol_l.setValue(val)
        self.ui.pushButton_set_l.setEnabled(True)

    def spinbox_pol_l(self, val):
        self.ui.dial_pol_l.setValue(int(val))
        self.ui.pushButton_set_l.setEnabled(True)

    def on_home_button_clicked_left(self):
        self.ui.groupBox_leftbot.setEnabled(False)
        msg = '1.0\r\n'
        self.display_message_left(msg)
        self.cmd_socket_l.send(msg)

    def on_set_button_clicked_left(self):
        self.ui.groupBox_leftbot.setEnabled(False)
        self.ui.pushButton_set_l.setEnabled(False)
        msg = '2.0 ' +\
            str(self.ui.doubleSpinBox_az_l.value())+' ' +\
            str(self.ui.doubleSpinBox_el_ll.value())+' ' +\
            str(self.ui.doubleSpinBox_pol_l.value())+' ' +\
            str(self.ui.doubleSpinBox_speed_l.value())+'\r\n'
        self.display_message_left(msg)
        self.cmd_socket_l.send(msg)

    def display_message_left(self, msg):
        self.ui.textBrowser_l.append(
            '<p style="text-align: left;">' +
            '<span style="color: #000000;"><strong>' +
            'Sent: ' +
            '</strong></span>' +
            '<span style="color: #000000;">' +
            msg +
            '</span></p>')


if __name__ == "__main__":
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)

    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()

    sys.exit(app.exec())
