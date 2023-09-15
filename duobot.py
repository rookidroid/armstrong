import sys
from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import QThread, QFile
from PySide6.QtUiTools import QUiLoader

from pathlib import Path
import json

from tcpclient import TCPClient

from util import (
    start_leftbot_sequence,
    start_rightbot_sequence,
    stop_sequence,
    save_config,
)
from util import html_received_msg, html_sent_msg, html_err_msg

AZ_CENTER_THOD = 0
AZ_EDGE_THOD = 28
EL_UP_THOD = 0.5

AZ_MARGIN = 2

_VERSION_ = "v3.1"
STATUS_STR = (
    '<a href="https://hpc-gitlab.aptiv.com/zjx8rj/automation/-/tree/main/duobot_gui">Source Code</a>'
    + "&nbsp;•&nbsp;"
    + '<a href="https://hpc-gitlab.aptiv.com/zjx8rj/automation/-/issues">Issue Tracker</a>'
    + "&nbsp;•&nbsp;"
    + '<a href="https://hpc-gitlab.aptiv.com/zjx8rj/automation/-/tree/main/duobot_matlab">MATLAB API</a>'
    + "&nbsp;•&nbsp;"
    + '<a href="https://hpc-gitlab.aptiv.com/zjx8rj/automation/-/tree/main/#duobot">CANape Lib</a>'
)


class MyApp(QtWidgets.QMainWindow):
    def __init__(self):
        super(MyApp, self).__init__()

        self.az_l = 0
        self.el_l = 0
        self.pol_l = 0
        self.az_r = 0
        self.el_r = 0
        self.pol_r = 0

        config_file = Path("config.json")
        if config_file.exists():
            self.config = json.load(open("config.json", "r"))
        else:
            self.config = dict()
            json.dump(self.config, open("config.json", "w+"))

        """Load UI"""
        ui_file_name = "mainwindow.ui"
        ui_file = QFile(ui_file_name)
        loader = QUiLoader()
        self.ui = loader.load(ui_file)
        ui_file.close()
        self.init_ui()

        if not self.dev_mode:
            self.ui.pushButton_start.clicked.connect(
                self.on_connect_button_clicked_left
            )

        self.ui.pushButton_connect_r.clicked.connect(
            self.on_connect_button_clicked_right
        )
        self.ui.doubleSpinBox_az_r.valueChanged.connect(self.spinbox_az_r)
        self.ui.horizontalSlider_az_r.valueChanged.connect(self.slider_az_r)
        self.ui.doubleSpinBox_el_rl.valueChanged.connect(self.spinbox_el_rl)
        self.ui.verticalSlider_el_rl.valueChanged.connect(self.slider_el_rl)
        self.ui.dial_pol_r.valueChanged.connect(self.dial_pol_r)
        self.ui.doubleSpinBox_pol_r.valueChanged.connect(self.spinbox_pol_r)
        self.ui.pushButton_home_r.clicked.connect(self.on_home_button_clicked_right)
        self.ui.pushButton_set_r.clicked.connect(self.on_set_button_clicked_right)

        #######################################
        self.ui.pushButton_connect_l.clicked.connect(
            self.on_connect_button_clicked_left
        )
        self.ui.doubleSpinBox_az_l.valueChanged.connect(self.spinbox_az_l)
        self.ui.horizontalSlider_az_l.valueChanged.connect(self.slider_az_l)
        self.ui.doubleSpinBox_el_ll.valueChanged.connect(self.spinbox_el_ll)
        self.ui.verticalSlider_el_ll.valueChanged.connect(self.slider_el_ll)
        self.ui.dial_pol_l.valueChanged.connect(self.dial_pol_l)
        self.ui.doubleSpinBox_pol_l.valueChanged.connect(self.spinbox_pol_l)
        self.ui.pushButton_home_l.clicked.connect(self.on_home_button_clicked_left)
        self.ui.pushButton_set_l.clicked.connect(self.on_set_button_clicked_left)

        self.ui.show()

    def init_ui(self):
        self.ui.pushButton_start.setStyleSheet("background-color: green; color: white;")
        self.ui.groupBox.setStyleSheet("background-color: #B3E5FC;")
        self.ui.groupBox_2.setStyleSheet("background-color: #B3E5FC;")
        self.ui.groupBox_3.setStyleSheet("background-color: #B3E5FC;")
        self.ui.groupBox_5.setStyleSheet("background-color: #DCEDC8;")
        self.ui.groupBox_7.setStyleSheet("background-color: #DCEDC8;")
        self.ui.groupBox_8.setStyleSheet("background-color: #DCEDC8;")

        self.ui.groupBox_r.setEnabled(False)
        self.ui.groupBox_l.setEnabled(False)

        # TCP Client
        self.config["IP_RIGHT"] = self.config.get("IP_RIGHT", "192.168.0.32")
        self.config["CTRL_PORT_RIGHT"] = self.config.get("CTRL_PORT_RIGHT", 10002)
        self.config["CMD_PORT_RIGHT"] = self.config.get("CMD_PORT_RIGHT", 10003)
        self.config["SPEED_RIGHT"] = self.config.get("SPEED_RIGHT", 25)

        self.config["IP_LEFT"] = self.config.get("IP_LEFT", "192.168.0.33")
        self.config["CTRL_PORT_LEFT"] = self.config.get("CTRL_PORT_LEFT", 10002)
        self.config["CMD_PORT_LEFT"] = self.config.get("CMD_PORT_LEFT", 10003)
        self.config["SPEED_LEFT"] = self.config.get("SPEED_LEFT", 25)

        self.dev_mode = self.config.get("DEVMODE", False)

        self.ui.lineEdit_ip_r.setText(self.config["IP_RIGHT"])
        self.ui.doubleSpinBox_ctrl_r.setValue(self.config["CTRL_PORT_RIGHT"])
        self.ui.doubleSpinBox_cmd_r.setValue(self.config["CMD_PORT_RIGHT"])
        self.ui.doubleSpinBox_speed_r.setValue(self.config["SPEED_RIGHT"])

        self.ui.lineEdit_ip_l.setText(self.config["IP_LEFT"])
        self.ui.doubleSpinBox_ctrl_l.setValue(self.config["CTRL_PORT_LEFT"])
        self.ui.doubleSpinBox_cmd_l.setValue(self.config["CMD_PORT_LEFT"])
        self.ui.doubleSpinBox_speed_l.setValue(self.config["SPEED_LEFT"])

        status_label = QtWidgets.QLabel("&nbsp;" + _VERSION_ + " • " + STATUS_STR)
        status_label.setTextFormat(QtCore.Qt.RichText)
        status_label.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        status_label.setOpenExternalLinks(True)
        self.ui.statusBar().addWidget(status_label)

        self.ui.groupBox_l.setStyleSheet(
            ":enabled { background-color: white;} :disabled {background-color: #EEEEEE}"
        )
        self.ui.groupBox_r.setStyleSheet(
            ":enabled { background-color: white;} :disabled {background-color: #EEEEEE}"
        )

        self.ui.pushButton_home_l.setStyleSheet(
            ":enabled { background-color: #81D4FA;} :disabled {background-color: #E0E0E0}"
        )
        self.ui.pushButton_set_l.setStyleSheet(
            ":enabled { background-color: #81D4FA;} :disabled {background-color: #E0E0E0}"
        )
        self.ui.pushButton_home_r.setStyleSheet(
            ":enabled { background-color: #C5E1A5;} :disabled {background-color: #E0E0E0}"
        )
        self.ui.pushButton_set_r.setStyleSheet(
            ":enabled { background-color: #C5E1A5;} :disabled {background-color: #E0E0E0}"
        )

        if self.dev_mode:
            self.ui.pushButton_connect_l.setVisible(True)
            self.ui.pushButton_connect_r.setVisible(True)
        else:
            self.ui.pushButton_connect_l.setVisible(False)
            self.ui.pushButton_connect_r.setVisible(False)

        save_config(self.config)

    def on_connect_button_clicked_right(self):
        self.ui.pushButton_start.setEnabled(False)
        self.ui.pushButton_start.setStyleSheet("background-color: grey; color: white;")

        if self.ui.pushButton_connect_r.text() == "START":
            self.ui.pushButton_connect_r.setEnabled(False)

            self.ui.lineEdit_ip_r.setEnabled(False)
            self.ui.doubleSpinBox_ctrl_r.setEnabled(False)
            self.ui.doubleSpinBox_cmd_r.setEnabled(False)

            self.ctrl_thread_r = QThread()
            self.ctrl_socket_r = TCPClient(
                self.ui.lineEdit_ip_r.text(), int(self.ui.doubleSpinBox_ctrl_r.value())
            )

            self.ctrl_socket_r.sig_status.connect(self.on_ctrl_status_update_right)
            self.ctrl_socket_r.sig_error.connect(self.on_tcp_client_error_right)
            self.ctrl_socket_r.sig_message.connect(
                self.on_tcp_client_message_ready_right
            )
            self.ctrl_thread_r.started.connect(self.ctrl_socket_r.start)
            self.ctrl_socket_r.moveToThread(self.ctrl_thread_r)
            self.ctrl_thread_r.start()

        elif self.ui.pushButton_connect_r.text() == "STOP":
            self.ui.pushButton_connect_r.setEnabled(False)
            stop_sequence(
                self.display_message_right, self.ctrl_socket_r, self.cmd_socket_r
            )

            self.ctrl_socket_r.close()
            self.cmd_socket_r.close()

    def on_ctrl_status_update_right(self, status, addr):
        if status == TCPClient.STOP:
            self.ui.pushButton_connect_r.setText("START")

            self.ctrl_socket_r.sig_status.disconnect()
            self.ctrl_socket_r.sig_message.disconnect()
            self.ctrl_thread_r.quit()

            self.ui.lineEdit_ip_r.setEnabled(True)
            self.ui.doubleSpinBox_ctrl_r.setEnabled(True)
            self.ui.doubleSpinBox_cmd_r.setEnabled(True)

            self.ui.groupBox_r.setEnabled(False)

            self.ui.pushButton_connect_r.setEnabled(True)

            if (
                self.ui.pushButton_connect_r.text() == "START"
                and self.ui.pushButton_connect_l.text() == "START"
            ):
                self.ui.pushButton_start.setStyleSheet(
                    "background-color: green; color: white;"
                )
                self.ui.pushButton_start.setText("START")
                self.ui.pushButton_start.setEnabled(True)

        elif status == TCPClient.CONNECTED:
            self.connect_cmd_port_right()

    def connect_cmd_port_right(self):
        self.cmd_thread_r = QThread()
        self.cmd_socket_r = TCPClient(
            self.ui.lineEdit_ip_r.text(), int(self.ui.doubleSpinBox_cmd_r.value())
        )

        self.cmd_socket_r.sig_status.connect(self.on_cmd_status_update_right)
        self.cmd_socket_r.sig_message.connect(self.on_tcp_client_message_ready_right)
        self.cmd_thread_r.started.connect(self.cmd_socket_r.start)
        self.cmd_socket_r.moveToThread(self.cmd_thread_r)
        self.cmd_thread_r.start()

    def on_cmd_status_update_right(self, status, addr):
        if status == TCPClient.STOP:
            self.ctrl_socket_r.close()

            self.ui.pushButton_connect_r.setText("START")

            self.cmd_socket_r.sig_status.disconnect()
            self.cmd_socket_r.sig_message.disconnect()
            self.cmd_thread_r.quit()

            self.ui.lineEdit_ip_r.setEnabled(True)
            self.ui.doubleSpinBox_ctrl_r.setEnabled(True)
            self.ui.doubleSpinBox_cmd_r.setEnabled(True)

            self.ui.pushButton_connect_r.setEnabled(False)

        elif status == TCPClient.CONNECTED:
            self.config["IP_RIGHT"] = self.ui.lineEdit_ip_r.text()
            self.config["CTRL_PORT_RIGHT"] = self.ui.doubleSpinBox_ctrl_r.value()
            self.config["CMD_PORT_RIGHT"] = self.ui.doubleSpinBox_cmd_r.value()
            save_config(self.config)

            if (
                start_rightbot_sequence(self.display_message_right, self.ctrl_socket_r)
                == 0
            ):
                self.config["SPEED_RIGHT"] = self.ui.doubleSpinBox_speed_r.value()
                save_config(self.config)

                msg = "6.0\r\n"
                self.display_message_right(msg)
                self.cmd_socket_r.send_wait(msg)

            self.ui.pushButton_connect_r.setText("STOP")
        self.ui.pushButton_connect_r.setEnabled(True)

        if not self.dev_mode:
            if (
                self.ui.pushButton_connect_r.text() == "STOP"
                and self.ui.pushButton_connect_l.text() == "STOP"
                and self.ui.pushButton_connect_r.isEnabled()
                and self.ui.pushButton_connect_l.isEnabled()
            ):
                self.ui.pushButton_start.setStyleSheet(
                    "background-color: red; color: white;"
                )
                self.ui.pushButton_start.setText("STOP")
                self.ui.pushButton_start.setEnabled(True)
            elif (
                self.ui.pushButton_connect_r.text() == "START"
                and self.ui.pushButton_connect_l.text() == "START"
                and self.ui.pushButton_connect_r.isEnabled()
                and self.ui.pushButton_connect_l.isEnabled()
            ):
                self.ui.pushButton_start.setStyleSheet(
                    "background-color: green; color: white;"
                )
                self.ui.pushButton_start.setText("START")
                self.ui.pushButton_start.setEnabled(True)

    def on_tcp_client_message_ready_right(self, msg):
        msg_list = msg.split()
        # if msg_list[0] == 'Right':
        if msg_list[0] == self.config["RIGHT_SN"]:
            self.az_r = float(msg_list[2])
            self.el_r = float(msg_list[3])
            self.pol_r = float(msg_list[4])
            self.ui.doubleSpinBox_az_r.setValue(self.az_r)
            self.ui.doubleSpinBox_el_rl.setValue(self.el_r)
            self.ui.doubleSpinBox_pol_r.setValue(self.pol_r)

            self.ui.groupBox_r.setEnabled(True)
            self.ui.groupBox_rightbot.setEnabled(True)

            self.ui.pushButton_set_r.setEnabled(False)

            if msg_list[1] == "+2":
                self.ui.groupBox_leftbot.setEnabled(True)

        self.ui.textBrowser_r.append(html_received_msg(msg))

    def on_tcp_client_error_right(self, msg):
        self.ui.textBrowser_r.append(html_err_msg(msg))

        if not self.dev_mode and self.ui.pushButton_connect_l.text() == "STOP":
            stop_sequence(
                self.display_message_left, self.ctrl_socket_l, self.cmd_socket_l
            )
            self.ui.pushButton_connect_l.setEnabled(False)

    def spinbox_az_r(self, val):
        self.ui.horizontalSlider_az_r.setValue(val * 10)
        if abs(val) <= AZ_CENTER_THOD:
            self.ui.verticalSlider_el_rl.setEnabled(True)
            self.ui.doubleSpinBox_el_rl.setEnabled(True)
            self.ui.verticalSlider_el_rr.setEnabled(False)
            self.ui.doubleSpinBox_el_rr.setEnabled(False)

            self.ui.verticalSlider_el_rl.setMaximum(50)
            self.ui.doubleSpinBox_el_rl.setMaximum(5)

            self.ui.verticalSlider_el_rr.setMaximum(50)
            self.ui.doubleSpinBox_el_rr.setMaximum(5)

            self.ui.label_elr1.setText("+5°")
            self.ui.label_elr2.setText("+5°")
        elif abs(val) >= AZ_EDGE_THOD:
            self.ui.verticalSlider_el_rl.setEnabled(False)
            self.ui.doubleSpinBox_el_rl.setEnabled(False)
            self.ui.verticalSlider_el_rr.setEnabled(True)
            self.ui.doubleSpinBox_el_rr.setEnabled(True)

            self.ui.verticalSlider_el_rl.setMaximum(50)
            self.ui.doubleSpinBox_el_rl.setMaximum(5)

            self.ui.verticalSlider_el_rr.setMaximum(50)
            self.ui.doubleSpinBox_el_rr.setMaximum(5)

            self.ui.label_elr1.setText("+5°")
            self.ui.label_elr2.setText("+5°")
        else:
            self.ui.verticalSlider_el_rl.setEnabled(True)
            self.ui.doubleSpinBox_el_rl.setEnabled(True)
            self.ui.verticalSlider_el_rr.setEnabled(True)
            self.ui.doubleSpinBox_el_rr.setEnabled(True)

            self.ui.verticalSlider_el_rl.setMaximum(EL_UP_THOD * 10)
            self.ui.doubleSpinBox_el_rl.setMaximum(EL_UP_THOD)

            self.ui.verticalSlider_el_rr.setMaximum(EL_UP_THOD * 10)
            self.ui.doubleSpinBox_el_rr.setMaximum(EL_UP_THOD)

            self.ui.label_elr1.setText(str(EL_UP_THOD) + "°")
            self.ui.label_elr2.setText(str(EL_UP_THOD) + "°")
        self.ui.pushButton_set_r.setEnabled(True)

    def slider_az_r(self, val):
        self.ui.doubleSpinBox_az_r.setValue(val / 10)

        if abs(val / 10) <= AZ_CENTER_THOD:
            self.ui.verticalSlider_el_rl.setEnabled(True)
            self.ui.doubleSpinBox_el_rl.setEnabled(True)
            self.ui.verticalSlider_el_rr.setEnabled(False)
            self.ui.doubleSpinBox_el_rr.setEnabled(False)

            self.ui.verticalSlider_el_rl.setMaximum(50)
            self.ui.doubleSpinBox_el_rl.setMaximum(5)

            self.ui.verticalSlider_el_rr.setMaximum(50)
            self.ui.doubleSpinBox_el_rr.setMaximum(5)

            self.ui.label_elr1.setText("+5°")
            self.ui.label_elr2.setText("+5°")
        elif abs(val / 10) >= AZ_EDGE_THOD:
            self.ui.verticalSlider_el_rl.setEnabled(False)
            self.ui.doubleSpinBox_el_rl.setEnabled(False)
            self.ui.verticalSlider_el_rr.setEnabled(True)
            self.ui.doubleSpinBox_el_rr.setEnabled(True)

            self.ui.verticalSlider_el_rl.setMaximum(50)
            self.ui.doubleSpinBox_el_rl.setMaximum(5)

            self.ui.verticalSlider_el_rr.setMaximum(50)
            self.ui.doubleSpinBox_el_rr.setMaximum(5)

            self.ui.label_elr1.setText("+5°")
            self.ui.label_elr2.setText("+5°")
        else:
            self.ui.verticalSlider_el_rl.setEnabled(True)
            self.ui.doubleSpinBox_el_rl.setEnabled(True)
            self.ui.verticalSlider_el_rr.setEnabled(True)
            self.ui.doubleSpinBox_el_rr.setEnabled(True)

            self.ui.verticalSlider_el_rl.setMaximum(EL_UP_THOD * 10)
            self.ui.doubleSpinBox_el_rl.setMaximum(EL_UP_THOD)

            self.ui.verticalSlider_el_rr.setMaximum(EL_UP_THOD * 10)
            self.ui.doubleSpinBox_el_rr.setMaximum(EL_UP_THOD)

            self.ui.label_elr1.setText(str(EL_UP_THOD) + "°")
            self.ui.label_elr2.setText(str(EL_UP_THOD) + "°")
        self.ui.pushButton_set_r.setEnabled(True)

    def spinbox_el_rl(self, val):
        self.ui.verticalSlider_el_rl.setValue(val * 10)
        if val <= EL_UP_THOD:
            self.ui.doubleSpinBox_az_r.setEnabled(True)
            self.ui.horizontalSlider_az_r.setEnabled(True)
        else:
            self.ui.doubleSpinBox_az_r.setEnabled(False)
            self.ui.horizontalSlider_az_r.setEnabled(False)
        self.ui.pushButton_set_r.setEnabled(True)

    def slider_el_rl(self, val):
        self.ui.doubleSpinBox_el_rl.setValue(val / 10)
        if val / 10 <= EL_UP_THOD:
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
        self.ui.groupBox_leftbot.setEnabled(False)
        msg = "1.0\r\n"
        self.display_message_right(msg)
        self.cmd_socket_r.send(msg)

    def on_set_button_clicked_right(self):
        right_az = self.ui.doubleSpinBox_az_r.value()

        if abs(right_az - self.az_l) >= AZ_MARGIN:
            self.ui.groupBox_rightbot.setEnabled(False)
            self.ui.groupBox_leftbot.setEnabled(False)
            self.ui.pushButton_set_r.setEnabled(False)
            msg = (
                "2.0 "
                + str(self.ui.doubleSpinBox_az_r.value())
                + " "
                + str(self.ui.doubleSpinBox_el_rl.value())
                + " "
                + str(self.ui.doubleSpinBox_pol_r.value())
                + " "
                + str(self.ui.doubleSpinBox_speed_r.value())
                + "\r\n"
            )
            self.display_message_right(msg)
            self.cmd_socket_r.send(msg)

            self.config["SPEED_RIGHT"] = self.ui.doubleSpinBox_speed_r.value()
            save_config(self.config)
        else:
            self.ui.textBrowser_r.append(
                html_err_msg(
                    "[ERROR] Right-bot is likely to \
                             collide with left-bot"
                )
            )

    def display_message_right(self, msg):
        self.ui.textBrowser_r.append(html_sent_msg(msg))

    ##########################################################
    def on_connect_button_clicked_left(self):
        if self.ui.pushButton_connect_l.text() == "START":
            self.ui.pushButton_connect_l.setEnabled(False)

            self.ui.lineEdit_ip_l.setEnabled(False)
            self.ui.doubleSpinBox_ctrl_l.setEnabled(False)
            self.ui.doubleSpinBox_cmd_l.setEnabled(False)

            self.ctrl_thread_l = QThread()
            self.ctrl_socket_l = TCPClient(
                self.ui.lineEdit_ip_l.text(), int(self.ui.doubleSpinBox_ctrl_l.value())
            )

            self.ctrl_socket_l.sig_status.connect(self.on_ctrl_status_update_left)
            self.ctrl_socket_l.sig_error.connect(self.on_tcp_client_error_left)
            self.ctrl_socket_l.sig_message.connect(
                self.on_tcp_client_message_ready_left
            )
            self.ctrl_thread_l.started.connect(self.ctrl_socket_l.start)
            self.ctrl_socket_l.moveToThread(self.ctrl_thread_l)
            self.ctrl_thread_l.start()

        elif self.ui.pushButton_connect_l.text() == "STOP":
            self.ui.pushButton_connect_l.setEnabled(False)
            stop_sequence(
                self.display_message_left, self.ctrl_socket_l, self.cmd_socket_l
            )

            self.ctrl_socket_l.close()
            self.cmd_socket_l.close()

    def on_ctrl_status_update_left(self, status, addr):
        if status == TCPClient.STOP:
            self.ui.pushButton_connect_l.setText("START")

            self.ctrl_socket_l.sig_status.disconnect()
            self.ctrl_socket_l.sig_message.disconnect()
            self.ctrl_thread_l.quit()

            self.ui.lineEdit_ip_l.setEnabled(True)
            self.ui.doubleSpinBox_ctrl_l.setEnabled(True)
            self.ui.doubleSpinBox_cmd_l.setEnabled(True)

            self.ui.groupBox_l.setEnabled(False)

            self.ui.pushButton_connect_l.setEnabled(True)

            if (
                self.ui.pushButton_connect_r.text() == "START"
                and self.ui.pushButton_connect_l.text() == "START"
            ):
                self.ui.pushButton_start.setStyleSheet(
                    "background-color: green; color: white;"
                )
                self.ui.pushButton_start.setText("START")
                self.ui.pushButton_start.setEnabled(True)

        elif status == TCPClient.CONNECTED:
            self.connect_cmd_port_left()

    def connect_cmd_port_left(self):
        self.cmd_thread_l = QThread()
        self.cmd_socket_l = TCPClient(
            self.ui.lineEdit_ip_l.text(), int(self.ui.doubleSpinBox_cmd_l.value())
        )

        self.cmd_socket_l.sig_status.connect(self.on_cmd_status_update_left)
        self.cmd_socket_l.sig_message.connect(self.on_tcp_client_message_ready_left)
        self.cmd_thread_l.started.connect(self.cmd_socket_l.start)
        self.cmd_socket_l.moveToThread(self.cmd_thread_l)
        self.cmd_thread_l.start()

    def on_cmd_status_update_left(self, status, addr):
        if status == TCPClient.STOP:
            self.ctrl_socket_l.close()

            self.ui.pushButton_connect_l.setText("START")

            self.cmd_socket_l.sig_status.disconnect()
            self.cmd_socket_l.sig_message.disconnect()
            self.cmd_thread_l.quit()

            self.ui.lineEdit_ip_l.setEnabled(True)
            self.ui.doubleSpinBox_ctrl_l.setEnabled(True)
            self.ui.doubleSpinBox_cmd_l.setEnabled(True)

            self.ui.pushButton_connect_l.setEnabled(False)

        elif status == TCPClient.CONNECTED:
            self.config["IP_LEFT"] = self.ui.lineEdit_ip_l.text()
            self.config["CTRL_PORT_LEFT"] = self.ui.doubleSpinBox_ctrl_l.value()
            self.config["CMD_PORT_LEFT"] = self.ui.doubleSpinBox_cmd_l.value()
            save_config(self.config)

            if (
                start_leftbot_sequence(self.display_message_left, self.ctrl_socket_l)
                == 0
            ):
                self.config["SPEED_LEFT"] = self.ui.doubleSpinBox_speed_l.value()
                save_config(self.config)

                msg = "6.0\r\n"
                self.display_message_left(msg)
                self.cmd_socket_l.send_wait(msg)

            self.ui.pushButton_connect_l.setText("STOP")

        self.ui.pushButton_connect_l.setEnabled(True)

        if not self.dev_mode:
            self.on_connect_button_clicked_right()

        # if not self.dev_mode:
        #     if self.ui.pushButton_connect_r.text() == 'STOP' and \
        #             self.ui.pushButton_connect_l.text() == 'STOP' and \
        #             self.ui.pushButton_connect_r.isEnabled() and \
        #             self.ui.pushButton_connect_l.isEnabled():

        #         self.ui.pushButton_start.setStyleSheet(
        #             "background-color: red; color: white;")
        #         self.ui.pushButton_start.setText('STOP')
        #         self.ui.pushButton_start.setEnabled(True)
        #     elif self.ui.pushButton_connect_r.text() == 'START' and \
        #             self.ui.pushButton_connect_l.text() == 'START' and \
        #             self.ui.pushButton_connect_r.isEnabled() and \
        #             self.ui.pushButton_connect_l.isEnabled():

        #         self.ui.pushButton_start.setStyleSheet(
        #             "background-color: green; color: white;")
        #         self.ui.pushButton_start.setText('START')
        #         self.ui.pushButton_start.setEnabled(True)

    def on_tcp_client_message_ready_left(self, msg):
        msg_list = msg.split()
        # print(msg_list)
        # if msg_list[0] == 'Left':
        if msg_list[0] == self.config["LEFT_SN"]:
            self.az_l = float(msg_list[2])
            self.el_l = float(msg_list[3])
            self.pol_l = float(msg_list[4])
            self.ui.doubleSpinBox_az_l.setValue(self.az_l)
            self.ui.doubleSpinBox_el_ll.setValue(self.el_l)
            self.ui.doubleSpinBox_pol_l.setValue(self.pol_l)

            self.ui.groupBox_l.setEnabled(True)
            self.ui.groupBox_leftbot.setEnabled(True)

            self.ui.pushButton_set_l.setEnabled(False)

            if msg_list[1] == "+2":
                self.ui.groupBox_rightbot.setEnabled(True)

        self.ui.textBrowser_l.append(html_received_msg(msg))

    def on_tcp_client_error_left(self, msg):
        self.ui.textBrowser_l.append(html_err_msg(msg))

        if not self.dev_mode and self.ui.pushButton_connect_r.text() == "STOP":
            stop_sequence(
                self.display_message_right, self.ctrl_socket_r, self.cmd_socket_r
            )

            self.ui.pushButton_connect_r.setEnabled(False)

    def spinbox_az_l(self, val):
        self.ui.horizontalSlider_az_l.setValue(val * 10)
        if abs(val) <= AZ_CENTER_THOD:
            self.ui.verticalSlider_el_ll.setEnabled(True)
            self.ui.doubleSpinBox_el_ll.setEnabled(True)
            self.ui.verticalSlider_el_lr.setEnabled(False)
            self.ui.doubleSpinBox_el_lr.setEnabled(False)

            self.ui.verticalSlider_el_ll.setMaximum(50)
            self.ui.doubleSpinBox_el_ll.setMaximum(5)

            self.ui.verticalSlider_el_lr.setMaximum(50)
            self.ui.doubleSpinBox_el_lr.setMaximum(5)

            self.ui.label_ell1.setText("+5°")
            self.ui.label_ell2.setText("+5°")
        elif abs(val) >= AZ_EDGE_THOD:
            self.ui.verticalSlider_el_ll.setEnabled(False)
            self.ui.doubleSpinBox_el_ll.setEnabled(False)
            self.ui.verticalSlider_el_lr.setEnabled(True)
            self.ui.doubleSpinBox_el_lr.setEnabled(True)

            self.ui.verticalSlider_el_ll.setMaximum(50)
            self.ui.doubleSpinBox_el_ll.setMaximum(5)

            self.ui.verticalSlider_el_lr.setMaximum(50)
            self.ui.doubleSpinBox_el_lr.setMaximum(5)

            self.ui.label_ell1.setText("+5°")
            self.ui.label_ell2.setText("+5°")
        else:
            self.ui.verticalSlider_el_ll.setEnabled(True)
            self.ui.doubleSpinBox_el_ll.setEnabled(True)
            self.ui.verticalSlider_el_lr.setEnabled(True)
            self.ui.doubleSpinBox_el_lr.setEnabled(True)

            self.ui.verticalSlider_el_ll.setMaximum(EL_UP_THOD * 10)
            self.ui.doubleSpinBox_el_ll.setMaximum(EL_UP_THOD)

            self.ui.verticalSlider_el_lr.setMaximum(EL_UP_THOD * 10)
            self.ui.doubleSpinBox_el_lr.setMaximum(EL_UP_THOD)

            self.ui.label_ell1.setText(str(EL_UP_THOD) + "°")
            self.ui.label_ell2.setText(str(EL_UP_THOD) + "°")
        self.ui.pushButton_set_l.setEnabled(True)

    def slider_az_l(self, val):
        self.ui.doubleSpinBox_az_l.setValue(val / 10)

        if abs(val / 10) <= AZ_CENTER_THOD:
            self.ui.verticalSlider_el_ll.setEnabled(False)
            self.ui.doubleSpinBox_el_ll.setEnabled(False)
            self.ui.verticalSlider_el_lr.setEnabled(True)
            self.ui.doubleSpinBox_el_lr.setEnabled(True)

            self.ui.verticalSlider_el_ll.setMaximum(50)
            self.ui.doubleSpinBox_el_ll.setMaximum(5)

            self.ui.verticalSlider_el_lr.setMaximum(50)
            self.ui.doubleSpinBox_el_lr.setMaximum(5)

            self.ui.label_ell1.setText("+5°")
            self.ui.label_ell2.setText("+5°")
        elif abs(val / 10) >= AZ_EDGE_THOD:
            self.ui.verticalSlider_el_ll.setEnabled(True)
            self.ui.doubleSpinBox_el_ll.setEnabled(True)
            self.ui.verticalSlider_el_lr.setEnabled(False)
            self.ui.doubleSpinBox_el_lr.setEnabled(False)

            self.ui.verticalSlider_el_ll.setMaximum(50)
            self.ui.doubleSpinBox_el_ll.setMaximum(5)

            self.ui.verticalSlider_el_lr.setMaximum(50)
            self.ui.doubleSpinBox_el_lr.setMaximum(5)

            self.ui.label_ell1.setText("+5°")
            self.ui.label_ell2.setText("+5°")
        else:
            self.ui.verticalSlider_el_ll.setEnabled(True)
            self.ui.doubleSpinBox_el_ll.setEnabled(True)
            self.ui.verticalSlider_el_lr.setEnabled(True)
            self.ui.doubleSpinBox_el_lr.setEnabled(True)

            self.ui.verticalSlider_el_ll.setMaximum(EL_UP_THOD * 10)
            self.ui.doubleSpinBox_el_ll.setMaximum(EL_UP_THOD)

            self.ui.verticalSlider_el_lr.setMaximum(EL_UP_THOD * 10)
            self.ui.doubleSpinBox_el_lr.setMaximum(EL_UP_THOD)

            self.ui.label_ell1.setText(str(EL_UP_THOD) + "°")
            self.ui.label_ell2.setText(str(EL_UP_THOD) + "°")
        self.ui.pushButton_set_l.setEnabled(True)

    def spinbox_el_ll(self, val):
        self.ui.verticalSlider_el_ll.setValue(val * 10)
        if val <= EL_UP_THOD:
            self.ui.doubleSpinBox_az_l.setEnabled(True)
            self.ui.horizontalSlider_az_l.setEnabled(True)
        else:
            self.ui.doubleSpinBox_az_l.setEnabled(False)
            self.ui.horizontalSlider_az_l.setEnabled(False)
        self.ui.pushButton_set_l.setEnabled(True)

    def slider_el_ll(self, val):
        self.ui.doubleSpinBox_el_ll.setValue(val / 10)
        if val / 10 <= EL_UP_THOD:
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
        self.ui.groupBox_rightbot.setEnabled(False)
        msg = "1.0\r\n"
        self.display_message_left(msg)
        self.cmd_socket_l.send(msg)

    def on_set_button_clicked_left(self):
        left_az = self.ui.doubleSpinBox_az_l.value()

        if abs(self.az_r - left_az) >= AZ_MARGIN:
            self.ui.groupBox_leftbot.setEnabled(False)
            self.ui.groupBox_rightbot.setEnabled(False)
            self.ui.pushButton_set_l.setEnabled(False)
            msg = (
                "2.0 "
                + str(self.ui.doubleSpinBox_az_l.value())
                + " "
                + str(self.ui.doubleSpinBox_el_ll.value())
                + " "
                + str(self.ui.doubleSpinBox_pol_l.value())
                + " "
                + str(self.ui.doubleSpinBox_speed_l.value())
                + "\r\n"
            )
            self.display_message_left(msg)
            self.cmd_socket_l.send(msg)

            self.config["SPEED_LEFT"] = self.ui.doubleSpinBox_speed_l.value()
            save_config(self.config)
        else:
            self.ui.textBrowser_l.append(
                html_err_msg(
                    "[ERROR] Left-bot is likely to \
                             collide with right-bot"
                )
            )

    def display_message_left(self, msg):
        self.ui.textBrowser_l.append(html_sent_msg(msg))


if __name__ == "__main__":
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)

    app = QtWidgets.QApplication(sys.argv)

    window = MyApp()

    sys.exit(app.exec())
