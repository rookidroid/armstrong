import sys
import math
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt
from PySide6.QtCore import QThread, QFile
from PySide6.QtUiTools import QUiLoader

from pathlib import Path
import json

from tcpclient import TCPClient

PI = 3.14159265359
# SPEED_MAX = 50
YAW_MIN = -180
YAW_MAX = 180
PITCH_MIN = -40
PITCH_MAX = 40
ROLL_MIN = -180
ROLL_MAX = 180
# X_MIN = -100
# X_MAX = 100
# Y_MIN = -100
# Y_MAX = 100
# Z_MIN = -100
# Z_MAX = 100
# TOOL_MIN = 0
# TOOL_MAX = 200
THETA_Y_MIN = -90
THETA_Y_MAX = 90
THETA_Z_MIN = -90
THETA_Z_MAX = 90
AZIMUTH_MIN = -90
AZIMUTH_MAX = 90
ELEVATION_MIN = -90
ELEVATION_MAX = 90


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

        self.ui.comboBox_coord.currentIndexChanged.connect(
            self.coordinate_changed
        )

        self.ui.show()

    def init_ui(self):
        self.ui.groupBox_ctrl.setEnabled(False)

        self.ui.comboBox_coord.addItems([
            'Robot Coordinate',
            'Radar DoA (Backmount using Yaw and Pitch)',
            'Radar DoA (Backmount using Yaw and Roll)',
            'Radar DoA (Sidemount using Yaw and Roll)',
            'Radar Detection (Backmount using Yaw and Pitch)',
            'Radar Detection (Backmount using Yaw and Roll)',
            'Radar Detection (Sidemount using Yaw and Roll)'])

        self.ui.comboBox_coord.setCurrentIndex(
            self.config.get('COORDINATE', 0))
        self.coordinate_changed(self.config.get('COORDINATE', 0))

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

    def coordinate_changed(self, idx):
        self.config['COORDINATE'] = self.ui.comboBox_coord.currentIndex()
        self.save_config()

        if idx == 0:
            self.ui.label_az.setText('Yaw ( ° )')
            self.ui.label_el.setText('Pitch ( ° )')
            self.ui.label_roll.setText('Roll ( ° )')

            self.ui.dial_az.setMinimum(YAW_MIN)
            self.ui.dial_az.setMaximum(YAW_MAX)
            self.ui.doubleSpinBox_az.setMinimum(YAW_MIN)
            self.ui.doubleSpinBox_az.setMaximum(YAW_MAX)

            self.ui.dial_el.setMinimum(PITCH_MIN)
            self.ui.dial_el.setMaximum(PITCH_MAX)
            self.ui.doubleSpinBox_el.setMinimum(PITCH_MIN)
            self.ui.doubleSpinBox_el.setMaximum(PITCH_MAX)

            self.ui.dial_roll.setMinimum(ROLL_MIN)
            self.ui.dial_roll.setMaximum(ROLL_MAX)
            self.ui.doubleSpinBox_roll.setMinimum(ROLL_MIN)
            self.ui.doubleSpinBox_roll.setMaximum(ROLL_MAX)
        elif idx == 1:
            self.ui.label_az.setText('Horiz. θy ( ° )')
            self.ui.label_el.setText('Vert. θz ( ° )')
            self.ui.label_roll.setText('Roll offset ( ° )')

            self.ui.dial_az.setMinimum(THETA_Y_MIN)
            self.ui.dial_az.setMaximum(THETA_Y_MAX)
            self.ui.doubleSpinBox_az.setMinimum(THETA_Y_MIN)
            self.ui.doubleSpinBox_az.setMaximum(THETA_Y_MAX)

            self.ui.dial_el.setMinimum(THETA_Z_MIN)
            self.ui.dial_el.setMaximum(THETA_Z_MAX)
            self.ui.doubleSpinBox_el.setMinimum(THETA_Z_MIN)
            self.ui.doubleSpinBox_el.setMaximum(THETA_Z_MAX)

            self.ui.dial_roll.setMinimum(ROLL_MIN)
            self.ui.dial_roll.setMaximum(ROLL_MAX)
            self.ui.doubleSpinBox_roll.setMinimum(ROLL_MIN)
            self.ui.doubleSpinBox_roll.setMaximum(ROLL_MAX)
        elif idx == 2:
            self.ui.label_az.setText('Horiz. θy ( ° )')
            self.ui.label_el.setText('Vert. θz ( ° )')
            self.ui.label_roll.setText('Roll offset ( ° )')

            self.ui.dial_az.setMinimum(THETA_Y_MIN)
            self.ui.dial_az.setMaximum(THETA_Y_MAX)
            self.ui.doubleSpinBox_az.setMinimum(THETA_Y_MIN)
            self.ui.doubleSpinBox_az.setMaximum(THETA_Y_MAX)

            self.ui.dial_el.setMinimum(THETA_Z_MIN)
            self.ui.dial_el.setMaximum(THETA_Z_MAX)
            self.ui.doubleSpinBox_el.setMinimum(THETA_Z_MIN)
            self.ui.doubleSpinBox_el.setMaximum(THETA_Z_MAX)

            self.ui.dial_roll.setMinimum(ROLL_MIN)
            self.ui.dial_roll.setMaximum(ROLL_MAX)
            self.ui.doubleSpinBox_roll.setMinimum(ROLL_MIN)
            self.ui.doubleSpinBox_roll.setMaximum(ROLL_MAX)
        elif idx == 3:
            self.ui.label_az.setText('Horiz. θy ( ° )')
            self.ui.label_el.setText('Vert. θz ( ° )')
            self.ui.label_roll.setText('Roll offset ( ° )')

            self.ui.dial_az.setMinimum(THETA_Y_MIN)
            self.ui.dial_az.setMaximum(THETA_Y_MAX)
            self.ui.doubleSpinBox_az.setMinimum(THETA_Y_MIN)
            self.ui.doubleSpinBox_az.setMaximum(THETA_Y_MAX)

            self.ui.dial_el.setMinimum(THETA_Z_MIN)
            self.ui.dial_el.setMaximum(THETA_Z_MAX)
            self.ui.doubleSpinBox_el.setMinimum(THETA_Z_MIN)
            self.ui.doubleSpinBox_el.setMaximum(THETA_Z_MAX)

            self.ui.dial_roll.setMinimum(ROLL_MIN)
            self.ui.dial_roll.setMaximum(ROLL_MAX)
            self.ui.doubleSpinBox_roll.setMinimum(ROLL_MIN)
            self.ui.doubleSpinBox_roll.setMaximum(ROLL_MAX)
        elif idx == 4:
            self.ui.label_az.setText('Azimuth ( ° )')
            self.ui.label_el.setText('Elevation ( ° )')
            self.ui.label_roll.setText('Roll offset ( ° )')

            self.ui.dial_az.setMinimum(AZIMUTH_MIN)
            self.ui.dial_az.setMaximum(AZIMUTH_MAX)
            self.ui.doubleSpinBox_az.setMinimum(AZIMUTH_MIN)
            self.ui.doubleSpinBox_az.setMaximum(AZIMUTH_MAX)

            self.ui.dial_el.setMinimum(ELEVATION_MIN)
            self.ui.dial_el.setMaximum(ELEVATION_MAX)
            self.ui.doubleSpinBox_el.setMinimum(ELEVATION_MIN)
            self.ui.doubleSpinBox_el.setMaximum(ELEVATION_MAX)

            self.ui.dial_roll.setMinimum(ROLL_MIN)
            self.ui.dial_roll.setMaximum(ROLL_MAX)
            self.ui.doubleSpinBox_roll.setMinimum(ROLL_MIN)
            self.ui.doubleSpinBox_roll.setMaximum(ROLL_MAX)
        elif idx == 5:
            self.ui.label_az.setText('Azimuth ( ° )')
            self.ui.label_el.setText('Elevation ( ° )')
            self.ui.label_roll.setText('Roll offset ( ° )')

            self.ui.dial_az.setMinimum(AZIMUTH_MIN)
            self.ui.dial_az.setMaximum(AZIMUTH_MAX)
            self.ui.doubleSpinBox_az.setMinimum(AZIMUTH_MIN)
            self.ui.doubleSpinBox_az.setMaximum(AZIMUTH_MAX)

            self.ui.dial_el.setMinimum(ELEVATION_MIN)
            self.ui.dial_el.setMaximum(ELEVATION_MAX)
            self.ui.doubleSpinBox_el.setMinimum(ELEVATION_MIN)
            self.ui.doubleSpinBox_el.setMaximum(ELEVATION_MAX)

            self.ui.dial_roll.setMinimum(ROLL_MIN)
            self.ui.dial_roll.setMaximum(ROLL_MAX)
            self.ui.doubleSpinBox_roll.setMinimum(ROLL_MIN)
            self.ui.doubleSpinBox_roll.setMaximum(ROLL_MAX)
        elif idx == 6:
            self.ui.label_az.setText('Azimuth ( ° )')
            self.ui.label_el.setText('Elevation ( ° )')
            self.ui.label_roll.setText('Roll offset ( ° )')

            self.ui.dial_az.setMinimum(AZIMUTH_MIN)
            self.ui.dial_az.setMaximum(AZIMUTH_MAX)
            self.ui.doubleSpinBox_az.setMinimum(AZIMUTH_MIN)
            self.ui.doubleSpinBox_az.setMaximum(AZIMUTH_MAX)

            self.ui.dial_el.setMinimum(ELEVATION_MIN)
            self.ui.dial_el.setMaximum(ELEVATION_MAX)
            self.ui.doubleSpinBox_el.setMinimum(ELEVATION_MIN)
            self.ui.doubleSpinBox_el.setMaximum(ELEVATION_MAX)

            self.ui.dial_roll.setMinimum(ROLL_MIN)
            self.ui.dial_roll.setMaximum(ROLL_MAX)
            self.ui.doubleSpinBox_roll.setMinimum(ROLL_MIN)
            self.ui.doubleSpinBox_roll.setMaximum(ROLL_MAX)
        self.ui.pushButton_set.setEnabled(True)

    def doa_backmount_yawpitch(self, theta_h, theta_v, roll_offset):
        theta_h_rad = theta_h/180.0*PI
        theta_v_rad = theta_v/180.0*PI

        err = ''

        yaw = -theta_h
        if math.cos(theta_h_rad) == 0 and math.sin(theta_v_rad) == 0:
            pitch = 0
        elif abs(math.sin(theta_v_rad)/math.cos(theta_h_rad)) <= 1:
            pitch = math.asin(math.sin(theta_v_rad) /
                              math.cos(theta_h_rad))/PI*180.0
        else:
            pitch = 0
            err = 'DoA error: impossible DoA angle'
            return 0, 0, 0, err
        roll = roll_offset
        return yaw, pitch, roll, err

    def doa_backmount_yawroll(self, theta_h, theta_v, roll_offset):
        theta_h_rad = theta_h/180.0*PI
        theta_v_rad = theta_v/180.0*PI

        err = ''

        if theta_v == 0:
            yaw = -theta_h
        elif abs(math.sin(theta_v_rad)/math.sin(math.atan2(
                math.sin(theta_v_rad), math.sin(theta_h_rad)))) <= 1:
            yaw = -math.asin(math.sin(theta_v_rad)/math.sin(math.atan2(
                math.sin(theta_v_rad), math.sin(theta_h_rad))))/PI*180.0
        else:
            yaw = 0
            err = 'DoA error: impossible DoA angle'
            return 0, 0, 0, err

        pitch = 0.0
        roll = -math.atan2(math.sin(theta_v_rad),
                           math.sin(theta_h_rad))/PI*180.0+roll_offset

        return yaw, pitch, roll, err

    def doa_sidemount_yawroll(self, theta_h, theta_v, roll_offset):
        theta_h_rad = theta_h/180.0*PI
        theta_v_rad = theta_v/180.0*PI

        err = ''

        yaw = theta_v+90.0
        pitch = 0.0
        if theta_v == 90 and theta_h == 0:
            roll = 90+roll_offset
        elif theta_v == -90 and theta_h == 0:
            roll = 90+roll_offset
        elif abs(math.sin(theta_h_rad) / math.cos(theta_v_rad)) <= 1:
            roll = math.cos(math.sin(theta_h_rad) /
                            math.cos(theta_v_rad))/PI*180.0+roll_offset
        else:
            err = 'DoA error: impossible DoA angle'
            return 0, 0, 0, err

        return yaw, pitch, roll, err

    def det_backmount_yawpitch(self, azimuth, elevation, roll_offset):
        az_rad = azimuth/180.0*PI
        el_rad = elevation/180.0*PI
        err = ''

        yaw = -math.asin(math.sin(az_rad)*math.cos(el_rad))/PI*180.0
        if elevation == 0 and azimuth == 90:
            pitch = 0
        elif elevation == 0 and azimuth == -90:
            pitch = 0
        else:
            pitch = math.asin(math.sin(
                el_rad)/math.cos(
                    math.asin(math.sin(az_rad)*math.cos(el_rad))))/PI*180.0
        roll = roll_offset

        return yaw, pitch, roll, err

    def det_backmount_yawroll(self, azimuth, elevation, roll_offset):
        az_rad = azimuth/180.0*PI
        el_rad = elevation/180.0*PI
        err = ''

        if elevation == 0:
            yaw = -azimuth
        else:
            yaw = -math.asin(math.sin(el_rad) /
                             math.sin(math.atan2(math.tan(el_rad),
                                                 math.sin(az_rad))))/PI*180.0
        pitch = 0.0
        roll = -math.atan2(math.tan(el_rad), math.sin(az_rad)
                           )/PI*180.0+roll_offset

        return yaw, pitch, roll, err

    def det_sidemount_yawroll(self, azimuth, elevation, roll_offset):
        yaw = elevation+90.0
        pitch = 0.0
        roll = 90.0-azimuth+roll_offset

        return yaw, pitch, roll

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
        angle1 = self.ui.doubleSpinBox_az.value()
        angle2 = self.ui.doubleSpinBox_el.value()
        angle3 = self.ui.doubleSpinBox_roll.value()
        err = ''

        coord = self.ui.comboBox_coord.currentIndex()
        if coord == 0:
            yaw = angle1
            pitch = angle2
            roll = angle3
        elif coord == 1:
            yaw, pitch, roll, err = self.doa_backmount_yawpitch(
                angle1, angle2, angle3)
        elif coord == 2:
            yaw, pitch, roll, err = self.doa_backmount_yawroll(
                angle1, angle2, angle3)
        elif coord == 3:
            yaw, pitch, roll, err = self.doa_sidemount_yawroll(
                angle1, angle2, angle3)
        elif coord == 4:
            yaw, pitch, roll, err = self.det_backmount_yawpitch(
                angle1, angle2, angle3)
        elif coord == 5:
            yaw, pitch, roll, err = self.det_backmount_yawroll(
                angle1, angle2, angle3)
        elif coord == 6:
            yaw, pitch, roll, err = self.det_sidemount_yawroll(
                angle1, angle2, angle3)

        if err:
            self.display_message(err)
            return

        if yaw < YAW_MIN or yaw > YAW_MAX or pitch < PITCH_MIN \
                or pitch > PITCH_MAX or roll < ROLL_MIN or roll > ROLL_MAX:
            self.display_message(
                'Error: unable to set robot position [' +
                str(yaw)+','+str(pitch)+','+str(roll)+']')
        else:
            x_offset = str(self.ui.doubleSpinBox_x.value())
            y_offset = str(self.ui.doubleSpinBox_y.value())
            z_offset = str(self.ui.doubleSpinBox_z.value())
            tool_offset = str(self.ui.doubleSpinBox_tool.value())

            msg = tsk_cmd+','+str(-yaw)+','+str(pitch)+','+str(roll) +\
                ','+x_offset + ','+y_offset+','+z_offset+','+tool_offset+'\r\n'

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

            self.ui.pushButton_ctrl.setEnabled(True)

        elif status == TCPClient.CONNECTED:
            self.connect_cmd_port()

    def connect_cmd_port(self):
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

            # self.ui.pushButton_init.setText('Stop')

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

                self.ui.groupBox_ctrl.setEnabled(True)

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
