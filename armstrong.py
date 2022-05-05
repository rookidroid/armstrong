import sys
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt
from PySide6.QtCore import QThread, QFile
from PySide6.QtUiTools import QUiLoader

from pathlib import Path
import json

from tcpclient import TCPClient


class MyApp(QtWidgets.QMainWindow):

    def __init__(self):
        super(MyApp, self).__init__()

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

        self.ui.pushButton_ctrl.clicked.connect(
            self.on_ctrl_connect_button_clicked
        )
        # self.ui.pushButton_cmd.clicked.connect(
        #     self.on_cmd_connect_button_clicked
        # )
        # self.ui.pushButton_init.clicked.connect(
        #     self.on_init_button_clicked
        # )

        self.ui.pushButton_load.clicked.connect(
            self.on_load_button_clicked
        )

        self.ui.pushButton_home.clicked.connect(
            self.on_home_button_clicked
        )

        self.ui.pushButton_set.clicked.connect(
            self.on_set_button_clicked
        )

        self.ui.dial_az.valueChanged.connect(
            self.az_dial
        )
        self.ui.doubleSpinBox_az.valueChanged.connect(
            self.az_spinbox
        )
        self.ui.dial_el.valueChanged.connect(
            self.el_dial
        )
        self.ui.doubleSpinBox_el.valueChanged.connect(
            self.el_spinbox
        )
        self.ui.dial_roll.valueChanged.connect(
            self.roll_dial
        )
        self.ui.doubleSpinBox_roll.valueChanged.connect(
            self.roll_spinbox
        )

        self.ui.horizontalSlider_x.valueChanged.connect(
            self.x_slider
        )
        self.ui.doubleSpinBox_x.valueChanged.connect(
            self.x_spinbox
        )

        self.ui.horizontalSlider_y.valueChanged.connect(
            self.y_slider
        )
        self.ui.doubleSpinBox_y.valueChanged.connect(
            self.y_spinbox
        )

        self.ui.horizontalSlider_z.valueChanged.connect(
            self.z_slider
        )
        self.ui.doubleSpinBox_z.valueChanged.connect(
            self.z_spinbox
        )

        self.ui.horizontalSlider_tool.valueChanged.connect(
            self.tool_slider
        )
        self.ui.doubleSpinBox_tool.valueChanged.connect(
            self.tool_spinbox
        )

        self.ui.show()

    def init_ui(self):
        self.ui.groupBox_ctrl.setEnabled(False)

        # TCP Client
        self.config['IP'] = self.config.get('IP', '192.168.0.20')
        self.config['CTRL_PORT'] = self.config.get('CTRL_PORT', '10002')
        self.config['CMD_PORT'] = self.config.get('CMD_PORT', '10003')
        self.config['SPEED'] = self.config.get('SPEED', 30)
        self.ui.lineEdit_ip.setText(self.config['IP'])
        self.ui.lineEdit_ctrl_port.setText(self.config['CTRL_PORT'])
        self.ui.lineEdit_cmd_port.setText(self.config['CMD_PORT'])

        self.ui.spinBox_speed.setValue(self.config['SPEED'])

        self.config['TOOL'] = self.config.get('TOOL', 60)
        self.ui.doubleSpinBox_tool.setValue(self.config['TOOL'])

        self.save_config()

    def save_config(self):
        try:
            json.dump(self.config, open('config.json', 'w+'))
        except PermissionError as err:
            pass

    def on_load_button_clicked(self):
        tsk_cmd = str(2.0)
        azi = '0.0'
        ele = '0.0'
        rol = '0.0'
        x_offset = '0.0'
        y_offset = '0.0'
        z_offset = '0.0'
        tool_offset = '0.0'

        msg = tsk_cmd+','+azi+','+ele+','+rol+','+x_offset + \
            ','+y_offset+','+z_offset+','+tool_offset+'\r\n'

        self.display_message(msg)
        self.cmd_socket.sendrecv(msg)
        self.ui.pushButton_set.setEnabled(True)

    def on_home_button_clicked(self):
        self.config['TOOL'] = self.ui.doubleSpinBox_tool.value()
        self.save_config()

        tsk_cmd = str(1.0)
        azi = '0.0'
        ele = '0.0'
        rol = '0.0'
        x_offset = '0.0'
        y_offset = '0.0'
        z_offset = '0.0'
        tool_offset = str(self.config['TOOL'])

        msg = tsk_cmd+','+azi+','+ele+','+rol+','+x_offset + \
            ','+y_offset+','+z_offset+','+tool_offset+'\r\n'

        self.display_message(msg)
        self.cmd_socket.sendrecv(msg)
        self.ui.pushButton_set.setEnabled(True)

        # self.ui.lineEdit_cmd_port.setEnabled(False)
    def on_set_button_clicked(self):
        self.ui.pushButton_set.setEnabled(False)
        tsk_cmd = str(3.0)
        azi = str(self.ui.doubleSpinBox_az.value())
        ele = str(self.ui.doubleSpinBox_el.value())
        rol = str(self.ui.doubleSpinBox_roll.value())
        x_offset = str(self.ui.doubleSpinBox_x.value())
        y_offset = str(self.ui.doubleSpinBox_y.value())
        z_offset = str(self.ui.doubleSpinBox_z.value())
        tool_offset = str(self.ui.doubleSpinBox_tool.value())

        msg = tsk_cmd+','+azi+','+ele+','+rol+','+x_offset + \
            ','+y_offset+','+z_offset+','+tool_offset+'\r\n'

        self.display_message(msg)
        self.cmd_socket.sendrecv(msg)

        self.config['TOOL'] = self.ui.doubleSpinBox_tool.value()
        self.save_config()

    def x_slider(self, val):
        self.ui.doubleSpinBox_x.setValue(val)

    def x_spinbox(self, val):
        self.ui.horizontalSlider_x.setValue(val)
        self.ui.pushButton_set.setEnabled(True)

    def y_slider(self, val):
        self.ui.doubleSpinBox_y.setValue(val)

    def y_spinbox(self, val):
        self.ui.horizontalSlider_y.setValue(val)
        self.ui.pushButton_set.setEnabled(True)

    def z_slider(self, val):
        self.ui.doubleSpinBox_z.setValue(val)

    def z_spinbox(self, val):
        self.ui.horizontalSlider_z.setValue(val)
        self.ui.pushButton_set.setEnabled(True)

    def tool_slider(self, val):
        self.ui.doubleSpinBox_tool.setValue(val)

    def tool_spinbox(self, val):
        self.ui.horizontalSlider_tool.setValue(val)
        self.ui.pushButton_set.setEnabled(True)

    def az_dial(self, val):
        self.ui.doubleSpinBox_az.setValue(val)

    def az_spinbox(self, val):
        self.ui.dial_az.setValue(val)
        self.ui.pushButton_set.setEnabled(True)

    def el_dial(self, val):
        self.ui.doubleSpinBox_el.setValue(val)

    def el_spinbox(self, val):
        self.ui.dial_el.setValue(val)
        self.ui.pushButton_set.setEnabled(True)

    def roll_dial(self, val):
        self.ui.doubleSpinBox_roll.setValue(val)

    def roll_spinbox(self, val):
        self.ui.dial_roll.setValue(val)
        self.ui.pushButton_set.setEnabled(True)

    def on_ctrl_connect_button_clicked(self):
        if self.ui.pushButton_ctrl.text() == 'Connect and Initialize':
            self.ui.pushButton_ctrl.setEnabled(False)

            self.ui.lineEdit_ip.setEnabled(False)
            self.ui.lineEdit_ctrl_port.setEnabled(False)
            self.ui.lineEdit_cmd_port.setEnabled(False)
            self.ui.spinBox_speed.setEnabled(False)

            self.ctrl_thread = QThread()
            self.ctrl_socket = TCPClient(
                self.ui.lineEdit_ip.text(),
                int(self.ui.lineEdit_ctrl_port.text()))

            self.ctrl_socket.status.connect(self.on_ctrl_status_update)
            self.ctrl_socket.message.connect(self.on_tcp_client_message_ready)
            self.ctrl_thread.started.connect(self.ctrl_socket.start)
            self.ctrl_socket.moveToThread(self.ctrl_thread)
            self.ctrl_thread.start()

        elif self.ui.pushButton_ctrl.text() == 'Stop and Disconnect':
            self.ui.pushButton_init.setText('Initialize')
            self.display_message('1;1;STOP')
            self.ctrl_socket.sendrecv('1;1;STOP')
            self.display_message('1;1;SRVOFF')
            self.ctrl_socket.sendrecv('1;1;SRVOFF')
            self.display_message('1;1;CNTLOFF')
            self.ctrl_socket.sendrecv('1;1;CNTLOFF')

            self.ui.pushButton_ctrl.setEnabled(False)
            self.ctrl_socket.close()
            self.cmd_socket.close()

    def on_ctrl_status_update(self, status, addr):
        if status == TCPClient.STOP:
            self.ui.pushButton_ctrl.setText('Connect and Initialize')

            self.ctrl_socket.status.disconnect()
            self.ctrl_socket.message.disconnect()
            self.ctrl_thread.quit()

            self.ui.lineEdit_ip.setEnabled(True)
            self.ui.lineEdit_ctrl_port.setEnabled(True)
            self.ui.lineEdit_cmd_port.setEnabled(True)
            self.ui.spinBox_speed.setEnabled(True)

            self.ui.groupBox_ctrl.setEnabled(False)

        elif status == TCPClient.CONNECTED:
            self.on_cmd_connect_button_clicked()

        # self.ui.pushButton_ctrl.setEnabled(True)

    def on_cmd_connect_button_clicked(self):
        self.cmd_thread = QThread()
        self.cmd_socket = TCPClient(
            self.ui.lineEdit_ip.text(),
            int(self.ui.lineEdit_cmd_port.text()))

        self.cmd_socket.status.connect(self.on_cmd_status_update)
        self.cmd_socket.message.connect(self.on_tcp_client_message_ready)
        self.cmd_thread.started.connect(self.cmd_socket.start)
        self.cmd_socket.moveToThread(self.cmd_thread)
        self.cmd_thread.start()

    def on_cmd_status_update(self, status, addr):
        if status == TCPClient.STOP:
            self.ctrl_socket.close()

            self.ui.pushButton_ctrl.setText('Connect and Initialize')

            self.cmd_socket.status.disconnect()
            self.cmd_socket.message.disconnect()
            self.cmd_thread.quit()

            self.ui.lineEdit_ip.setEnabled(True)
            self.ui.lineEdit_ctrl_port.setEnabled(True)
            self.ui.lineEdit_cmd_port.setEnabled(True)
            self.ui.spinBox_speed.setEnabled(True)

            self.ui.groupBox_ctrl.setEnabled(False)

        elif status == TCPClient.CONNECTED:
            self.config['IP'] = self.ui.lineEdit_ip.text()
            self.config['CTRL_PORT'] = self.ui.lineEdit_ctrl_port.text()
            self.config['CMD_PORT'] = self.ui.lineEdit_cmd_port.text()
            self.save_config()

            self.ui.pushButton_init.setText('Stop')

            speed = self.ui.spinBox_speed.value()

            success = 0
            self.display_message('1;1;RSTALRM')
            success += self.ctrl_socket.sendrecv('1;1;RSTALRM')
            self.display_message('1;1;STOP')
            success += self.ctrl_socket.sendrecv('1;1;STOP')
            self.display_message('1;1;CNTLON')
            success += self.ctrl_socket.sendrecv('1;1;CNTLON')
            self.display_message('1;1;STATE')
            success += self.ctrl_socket.sendrecv('1;1;STATE')
            self.display_message('1;1;SRVON')
            success += self.ctrl_socket.sendrecv('1;1;SRVON')
            self.display_message('1;1;SLOTINIT')
            success += self.ctrl_socket.sendrecv('1;1;SLOTINIT')
            self.display_message('1;1;RUNSIM2SOCKET;0')
            success += self.ctrl_socket.sendrecv('1;1;RUNSIM2SOCKET;0')
            self.display_message('1;1;OVRD='+str(speed))
            success += self.ctrl_socket.sendrecv('1;1;OVRD='+str(speed))

            success = 0
            if success == 0:
                self.config['SPEED'] = speed
                self.save_config()

                self.ui.groupBox_predefine.setEnabled(True)
                self.ui.groupBox_position.setEnabled(True)
                self.ui.pushButton_set.setEnabled(True)

        self.ui.pushButton_ctrl.setText('Stop and Disconnect')
        self.ui.pushButton_ctrl.setEnabled(True)

    def on_tcp_client_message_ready(self, msg):
        self.ui.textBrowser.append(
            '<p style="text-align: center;">' +
            '<span style="color: #2196F3;"><strong>' +
            'Received: ' +
            '</strong></span>' +
            '<span style="color: #2196F3;">' +
            msg +
            '</span></p>')

    def display_message(self, msg):
        self.ui.textBrowser.append(
            '<p style="text-align: left;">' +
            '<span style="color: #000000;"><strong>' +
            'Sent: ' +
            '</strong></span>' +
            '<span style="color: #000000;">' +
            msg +
            '</span></p>')


if __name__ == "__main__":
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    # window.show()
    sys.exit(app.exec())
