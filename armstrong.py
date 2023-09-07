import sys
import math
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt
from PySide6.QtCore import QThread, QFile
from PySide6.QtUiTools import QUiLoader

from pathlib import Path
import json

from tcpclient import TCPClient

_VERSION_ = "v3.1"
STATUS_STR = (
    '<a href="https://hpc-gitlab.aptiv.com/zjx8rj/automation/-/tree/main/armstrong_gui">Source Code</a>'
    + "&nbsp;•&nbsp;"
    + '<a href="https://hpc-gitlab.aptiv.com/zjx8rj/automation/-/issues">Issue Tracker</a>'
    + "&nbsp;•&nbsp;"
    + '<a href="https://hpc-gitlab.aptiv.com/zjx8rj/automation/-/tree/main/armstrong_matlab">MATLAB API</a>'
    + "&nbsp;•&nbsp;"
    + '<a href="https://hpc-gitlab.aptiv.com/zjx8rj/automation/-/tree/main/#armstrong">CANape Lib</a>'
)

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
# TOOLX_MIN = -100
# TOOLX_MAX = 100
# TOOLY_MIN = -100
# TOOLY_MAX = 100
# TOOLZ_MIN = 0
# TOOLZ_MAX = 250
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

        self.ui.pushButton_ctrl.clicked.connect(self.on_ctrl_connect_button_clicked)

        self.ui.pushButton_load.clicked.connect(self.on_load_button_clicked)

        self.ui.pushButton_home.clicked.connect(self.on_home_button_clicked)

        self.ui.pushButton_minrange.clicked.connect(self.on_minrange_button_clicked)

        self.ui.pushButton_set.clicked.connect(self.on_set_button_clicked)

        self.ui.dial_az.valueChanged.connect(self.az_dial)
        self.ui.doubleSpinBox_az.valueChanged.connect(self.az_spinbox)
        self.ui.dial_el.valueChanged.connect(self.el_dial)
        self.ui.doubleSpinBox_el.valueChanged.connect(self.el_spinbox)
        self.ui.dial_roll.valueChanged.connect(self.roll_dial)
        self.ui.doubleSpinBox_roll.valueChanged.connect(self.roll_spinbox)

        self.ui.horizontalSlider_x.valueChanged.connect(self.x_slider)
        self.ui.doubleSpinBox_x.valueChanged.connect(self.x_spinbox)

        self.ui.horizontalSlider_y.valueChanged.connect(self.y_slider)
        self.ui.doubleSpinBox_y.valueChanged.connect(self.y_spinbox)

        self.ui.horizontalSlider_z.valueChanged.connect(self.z_slider)
        self.ui.doubleSpinBox_z.valueChanged.connect(self.z_spinbox)

        self.ui.horizontalSlider_minrange.valueChanged.connect(self.minrange_slider)
        self.ui.spinBox_minrange.valueChanged.connect(self.minrange_spinbox)

        self.ui.horizontalSlider_toolx.valueChanged.connect(self.tool_slider_x)
        self.ui.doubleSpinBox_toolx.valueChanged.connect(self.tool_spinbox_x)

        self.ui.horizontalSlider_tooly.valueChanged.connect(self.tool_slider_y)
        self.ui.doubleSpinBox_tooly.valueChanged.connect(self.tool_spinbox_y)

        self.ui.horizontalSlider_toolz.valueChanged.connect(self.tool_slider_z)
        self.ui.doubleSpinBox_toolz.valueChanged.connect(self.tool_spinbox_z)

        self.ui.comboBox_coord.currentIndexChanged.connect(self.coordinate_changed)

        self.ui.show()

    def init_ui(self):
        self.ui.pushButton_ctrl.setStyleSheet("background-color: green; color: white;")
        self.ui.groupBox_ctrl.setEnabled(False)

        self.ui.comboBox_coord.addItems(
            [
                "Robot Coordinate",
                "Radar DoA (Backmount using Yaw and Pitch)",
                "Radar DoA (Backmount using Yaw and Roll)",
                "Radar DoA (Topmount using Yaw and Roll)",
                "Radar Detection (Backmount using Yaw and Pitch)",
                "Radar Detection (Backmount using Yaw and Roll)",
                "Radar Detection (Topmount using Yaw and Roll)",
            ]
        )

        self.ui.comboBox_coord.setCurrentIndex(self.config.get("COORDINATE", 0))
        self.coordinate_changed(self.config.get("COORDINATE", 0))

        # TCP Client
        self.config["IP"] = self.config.get("IP", "192.168.0.20")
        self.config["CTRL_PORT"] = self.config.get("CTRL_PORT", 10002)
        self.config["CMD_PORT"] = self.config.get("CMD_PORT", 10003)
        self.config["SPEED"] = self.config.get("SPEED", 30)
        self.ui.lineEdit_ip.setText(self.config["IP"])
        self.ui.spinBox_ctrl_port.setValue(self.config["CTRL_PORT"])
        self.ui.spinBox_cmd_port.setValue(self.config["CMD_PORT"])

        self.ui.spinBox_speed.setValue(self.config["SPEED"])

        self.config["TOOLX"] = self.config.get("TOOLX", 0)
        self.ui.doubleSpinBox_toolx.setValue(self.config["TOOLX"])
        self.config["TOOLY"] = self.config.get("TOOLY", 0)
        self.ui.doubleSpinBox_tooly.setValue(self.config["TOOLY"])
        self.config["TOOLZ"] = self.config.get("TOOLZ", 60)
        self.ui.doubleSpinBox_toolz.setValue(self.config["TOOLZ"])

        status_label = QtWidgets.QLabel("&nbsp;" + _VERSION_ + " • " + STATUS_STR)
        status_label.setTextFormat(QtCore.Qt.RichText)
        status_label.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        status_label.setOpenExternalLinks(True)
        self.ui.statusBar().addWidget(status_label)

        self.save_config()

        self.ui.groupBox_ctrl.setStyleSheet(":enabled { background-color: white;} :disabled {background-color: #EEEEEE}")

        self.ui.pushButton_load.setStyleSheet(
            ":enabled { background-color: #81D4FA;} :disabled {background-color: #E0E0E0}"
        )
        self.ui.pushButton_home.setStyleSheet(
            ":enabled { background-color: #81D4FA;} :disabled {background-color: #E0E0E0}"
        )
        self.ui.pushButton_minrange.setStyleSheet(
            ":enabled { background-color: #81D4FA;} :disabled {background-color: #E0E0E0}"
        )
        self.ui.pushButton_set.setStyleSheet(
            ":enabled { background-color: #81D4FA;} :disabled {background-color: #E0E0E0}"
        )

    def save_config(self):
        try:
            json.dump(self.config, open("config.json", "w+"))
        except PermissionError as err:
            pass

    def coordinate_changed(self, idx):
        self.config["COORDINATE"] = self.ui.comboBox_coord.currentIndex()
        self.save_config()

        if idx == 0:
            self.ui.label_az.setText("Yaw")
            self.ui.label_el.setText("Pitch")
            self.ui.label_roll.setText("Roll")

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
            self.ui.label_az.setText("Horiz. θy")
            self.ui.label_el.setText("Vert. θz")
            self.ui.label_roll.setText("Roll offset")

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
            self.ui.label_az.setText("Horiz. θy")
            self.ui.label_el.setText("Vert. θz")
            self.ui.label_roll.setText("Roll offset")

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
            self.ui.label_az.setText("Horiz. θy")
            self.ui.label_el.setText("Vert. θz")
            self.ui.label_roll.setText("Roll offset")

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
            self.ui.label_az.setText("Azimuth")
            self.ui.label_el.setText("Elevation")
            self.ui.label_roll.setText("Roll offset")

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
            self.ui.label_az.setText("Azimuth")
            self.ui.label_el.setText("Elevation")
            self.ui.label_roll.setText("Roll offset")

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
            self.ui.label_az.setText("Azimuth")
            self.ui.label_el.setText("Elevation")
            self.ui.label_roll.setText("Roll offset")

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
        theta_h_rad = theta_h / 180.0 * PI
        theta_v_rad = theta_v / 180.0 * PI

        err = ""

        yaw = -theta_h
        if math.cos(theta_h_rad) == 0 and math.sin(theta_v_rad) == 0:
            pitch = 0
        elif abs(math.sin(theta_v_rad) / math.cos(theta_h_rad)) <= 1:
            pitch = (
                math.asin(math.sin(theta_v_rad) / math.cos(theta_h_rad)) / PI * 180.0
            )
        else:
            pitch = 0
            err = "DoA error: impossible DoA angle"
            return 0, 0, 0, err
        roll = roll_offset
        return yaw, pitch, roll, err

    def doa_backmount_yawroll(self, theta_h, theta_v, roll_offset):
        theta_h_rad = theta_h / 180.0 * PI
        theta_v_rad = theta_v / 180.0 * PI

        err = ""

        if theta_h == 0 and theta_v != 0:
            yaw = -theta_v
            roll = -90 + roll_offset
        elif theta_h != 0 and theta_v == 0:
            yaw = -theta_h
            roll = roll_offset
        elif theta_h == 0 and theta_v == 0:
            yaw = 0
            roll = roll_offset
        elif (
            abs(
                math.sin(theta_v_rad)
                / math.sin(math.atan(math.sin(theta_v_rad) / math.sin(theta_h_rad)))
            )
            <= 1
        ):
            yaw = (
                -math.asin(
                    math.sin(theta_v_rad)
                    / math.sin(math.atan(math.sin(theta_v_rad) / math.sin(theta_h_rad)))
                )
                / PI
                * 180.0
            )
            roll = (
                -math.atan(math.sin(theta_v_rad) / math.sin(theta_h_rad)) / PI * 180.0
                + roll_offset
            )
        else:
            yaw = 0
            err = "DoA error: impossible DoA angle"
            return 0, 0, 0, err

        pitch = 0.0

        return yaw, pitch, roll, err

    def doa_topmount_yawroll(self, theta_h, theta_v, roll_offset):
        theta_h_rad = theta_h / 180.0 * PI
        theta_v_rad = theta_v / 180.0 * PI

        err = ""

        yaw = -theta_v + 90.0
        pitch = 0.0
        if theta_v == 90 and theta_h == 0:
            roll = 90 + roll_offset
        elif theta_v == -90 and theta_h == 0:
            roll = 90 + roll_offset
        elif abs(math.sin(theta_h_rad) / math.cos(theta_v_rad)) <= 1:
            roll = (
                180
                - math.acos(math.sin(theta_h_rad) / math.cos(theta_v_rad)) / PI * 180.0
                + roll_offset
            )
        else:
            err = "DoA error: impossible DoA angle"
            return 0, 0, 0, err

        return yaw, pitch, roll, err

    def det_backmount_yawpitch(self, azimuth, elevation, roll_offset):
        az_rad = azimuth / 180.0 * PI
        el_rad = elevation / 180.0 * PI
        err = ""

        yaw = -math.asin(math.sin(az_rad) * math.cos(el_rad)) / PI * 180.0
        if elevation == 0 and azimuth == 90:
            pitch = 0
        elif elevation == 0 and azimuth == -90:
            pitch = 0
        else:
            pitch = (
                math.asin(
                    math.sin(el_rad)
                    / math.cos(math.asin(math.sin(az_rad) * math.cos(el_rad)))
                )
                / PI
                * 180.0
            )
        roll = roll_offset

        return yaw, pitch, roll, err

    def det_backmount_yawroll(self, azimuth, elevation, roll_offset):
        az_rad = azimuth / 180.0 * PI
        el_rad = elevation / 180.0 * PI
        err = ""

        if azimuth == 0 and elevation != 0:
            yaw = -elevation
            roll = -90 + roll_offset
        elif azimuth != 0 and elevation == 0:
            yaw = -azimuth
            roll = roll_offset
        elif azimuth == 0 and elevation == 0:
            yaw = 0
            roll = roll_offset
        else:
            yaw = (
                -math.asin(
                    math.sin(el_rad)
                    / math.sin(math.atan(math.tan(el_rad) / math.sin(az_rad)))
                )
                / PI
                * 180.0
            )
            roll = (
                -math.atan(math.tan(el_rad) / math.sin(az_rad)) / PI * 180.0
                + roll_offset
            )
        pitch = 0.0

        return yaw, pitch, roll, err

    def det_topmount_yawroll(self, azimuth, elevation, roll_offset):
        err = ""
        yaw = -elevation + 90.0
        pitch = 0.0
        roll = 90.0 + azimuth + roll_offset

        return yaw, pitch, roll, err

    def on_load_button_clicked(self):
        tsk_cmd = str(2.0)
        azi = "0.0"
        ele = "0.0"
        rol = "0.0"
        x_offset = "0.0"
        y_offset = "0.0"
        z_offset = "0.0"
        tool_x = "0.0"
        tool_y = "0.0"
        tool_z = "0.0"

        msg = (
            tsk_cmd
            + ","
            + azi
            + ","
            + ele
            + ","
            + rol
            + ","
            + x_offset
            + ","
            + y_offset
            + ","
            + z_offset
            + ","
            + tool_x
            + ","
            + tool_y
            + ","
            + tool_z
            + "\r\n"
        )

        self.display_message(msg)
        self.cmd_socket.sendrecv(msg)
        self.ui.pushButton_set.setEnabled(True)

    def on_home_button_clicked(self):
        self.config["TOOLX"] = self.ui.doubleSpinBox_toolx.value()
        self.config["TOOLY"] = self.ui.doubleSpinBox_tooly.value()
        self.config["TOOLZ"] = self.ui.doubleSpinBox_toolz.value()
        self.save_config()

        tsk_cmd = str(1.0)
        azi = "0.0"
        ele = "0.0"
        rol = "0.0"
        x_offset = "0.0"
        y_offset = "0.0"
        z_offset = "0.0"
        tool_x = "0.0"
        tool_y = "0.0"
        tool_z = str(self.config["TOOLZ"])

        msg = (
            tsk_cmd
            + ","
            + azi
            + ","
            + ele
            + ","
            + rol
            + ","
            + x_offset
            + ","
            + y_offset
            + ","
            + z_offset
            + ","
            + tool_x
            + ","
            + tool_y
            + ","
            + tool_z
            + "\r\n"
        )

        self.display_message(msg)
        self.cmd_socket.sendrecv(msg)
        self.ui.pushButton_set.setEnabled(True)

        # self.ui.spinBox_cmd_port.setEnabled(False)

    def on_minrange_button_clicked(self):
        tsk_cmd = str(5.0)
        azi = "0.0"
        ele = str(self.ui.spinBox_minrange.value())
        rol = "0.0"
        x_offset = "0.0"
        y_offset = "0.0"
        z_offset = "0.0"
        tool_x = "0.0"
        tool_y = "0.0"
        tool_z = "0.0"

        msg = (
            tsk_cmd
            + ","
            + azi
            + ","
            + ele
            + ","
            + rol
            + ","
            + x_offset
            + ","
            + y_offset
            + ","
            + z_offset
            + ","
            + tool_x
            + ","
            + tool_y
            + ","
            + tool_z
            + "\r\n"
        )

        self.display_message(msg)
        self.cmd_socket.sendrecv(msg)
        self.ui.pushButton_set.setEnabled(True)

    def on_set_button_clicked(self):
        self.ui.pushButton_set.setEnabled(False)
        tsk_cmd = str(3.0)
        angle1 = self.ui.doubleSpinBox_az.value()
        angle2 = self.ui.doubleSpinBox_el.value()
        angle3 = self.ui.doubleSpinBox_roll.value()
        err = ""

        coord = self.ui.comboBox_coord.currentIndex()
        if coord == 0:
            yaw = angle1
            pitch = angle2
            roll = angle3
        elif coord == 1:
            yaw, pitch, roll, err = self.doa_backmount_yawpitch(angle1, angle2, angle3)
        elif coord == 2:
            yaw, pitch, roll, err = self.doa_backmount_yawroll(angle1, angle2, angle3)
        elif coord == 3:
            yaw, pitch, roll, err = self.doa_topmount_yawroll(angle1, angle2, angle3)
        elif coord == 4:
            yaw, pitch, roll, err = self.det_backmount_yawpitch(angle1, angle2, angle3)
        elif coord == 5:
            yaw, pitch, roll, err = self.det_backmount_yawroll(angle1, angle2, angle3)
        elif coord == 6:
            yaw, pitch, roll, err = self.det_topmount_yawroll(angle1, angle2, angle3)

        if err:
            self.display_message(err)
            return

        if (
            yaw < YAW_MIN
            or yaw > YAW_MAX
            or pitch < PITCH_MIN
            or pitch > PITCH_MAX
            or roll < ROLL_MIN
            or roll > ROLL_MAX
        ):
            self.display_message(
                "Error: unable to set robot position ["
                + str(yaw)
                + ","
                + str(pitch)
                + ","
                + str(roll)
                + "]"
            )
        else:
            x_offset = str(self.ui.doubleSpinBox_x.value())
            y_offset = str(self.ui.doubleSpinBox_y.value())
            z_offset = str(self.ui.doubleSpinBox_z.value())
            tool_x = str(self.ui.doubleSpinBox_toolx.value())
            tool_y = str(self.ui.doubleSpinBox_tooly.value())
            tool_z = str(self.ui.doubleSpinBox_toolz.value())

            msg = (
                tsk_cmd
                + ","
                + str(-yaw)
                + ","
                + str(pitch)
                + ","
                + str(roll)
                + ","
                + x_offset
                + ","
                + y_offset
                + ","
                + z_offset
                + ","
                + tool_x
                + ","
                + tool_y
                + ","
                + tool_z
                + "\r\n"
            )

            self.display_message(msg)
            self.cmd_socket.sendrecv(msg)

            self.config["TOOLX"] = self.ui.doubleSpinBox_toolx.value()
            self.config["TOOLY"] = self.ui.doubleSpinBox_tooly.value()
            self.config["TOOLZ"] = self.ui.doubleSpinBox_toolz.value()
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

    def minrange_slider(self, val):
        self.ui.spinBox_minrange.setValue(val)

    def minrange_spinbox(self, val):
        self.ui.horizontalSlider_minrange.setValue(val)

    def tool_slider_x(self, val):
        self.ui.doubleSpinBox_toolx.setValue(val)

    def tool_spinbox_x(self, val):
        self.ui.horizontalSlider_toolx.setValue(val)
        self.ui.pushButton_set.setEnabled(True)

    def tool_slider_y(self, val):
        self.ui.doubleSpinBox_tooly.setValue(val)

    def tool_spinbox_y(self, val):
        self.ui.horizontalSlider_tooly.setValue(val)
        self.ui.pushButton_set.setEnabled(True)

    def tool_slider_z(self, val):
        self.ui.doubleSpinBox_toolz.setValue(val)

    def tool_spinbox_z(self, val):
        self.ui.horizontalSlider_toolz.setValue(val)
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
        if self.ui.pushButton_ctrl.text() == "START":
            self.ui.pushButton_ctrl.setEnabled(False)
            self.ui.pushButton_ctrl.setStyleSheet(
                "background-color: grey; color: white;"
            )

            self.ui.lineEdit_ip.setEnabled(False)
            self.ui.spinBox_ctrl_port.setEnabled(False)
            self.ui.spinBox_cmd_port.setEnabled(False)
            self.ui.spinBox_speed.setEnabled(False)

            self.ctrl_thread = QThread()
            self.ctrl_socket = TCPClient(
                self.ui.lineEdit_ip.text(), self.ui.spinBox_ctrl_port.value()
            )

            self.ctrl_socket.status.connect(self.on_ctrl_status_update)
            self.ctrl_socket.message.connect(self.on_tcp_client_message_ready)
            self.ctrl_thread.started.connect(self.ctrl_socket.start)
            self.ctrl_socket.moveToThread(self.ctrl_thread)
            self.ctrl_thread.start()

        elif self.ui.pushButton_ctrl.text() == "STOP":
            self.ui.pushButton_ctrl.setEnabled(False)
            self.ui.pushButton_ctrl.setStyleSheet(
                "background-color: grey; color: white;"
            )

            self.display_message("1;1;STOP")
            self.ctrl_socket.sendrecv("1;1;STOP")
            self.display_message("1;1;SRVOFF")
            self.ctrl_socket.sendrecv("1;1;SRVOFF")
            self.display_message("1;1;CNTLOFF")
            self.ctrl_socket.sendrecv("1;1;CNTLOFF")

            self.ctrl_socket.close()
            self.cmd_socket.close()

    def on_ctrl_status_update(self, status, addr):
        if status == TCPClient.STOP:
            self.ui.pushButton_ctrl.setText("START")
            self.ui.pushButton_ctrl.setStyleSheet(
                "background-color: green; color: white;"
            )

            self.ctrl_socket.status.disconnect()
            self.ctrl_socket.message.disconnect()
            self.ctrl_thread.quit()

            self.ui.lineEdit_ip.setEnabled(True)
            self.ui.spinBox_ctrl_port.setEnabled(True)
            self.ui.spinBox_cmd_port.setEnabled(True)
            self.ui.spinBox_speed.setEnabled(True)

            self.ui.groupBox_ctrl.setEnabled(False)

            self.ui.pushButton_ctrl.setEnabled(True)

        elif status == TCPClient.CONNECTED:
            self.connect_cmd_port()

    def connect_cmd_port(self):
        self.cmd_thread = QThread()
        self.cmd_socket = TCPClient(
            self.ui.lineEdit_ip.text(), self.ui.spinBox_cmd_port.value()
        )

        self.cmd_socket.status.connect(self.on_cmd_status_update)
        self.cmd_socket.message.connect(self.on_tcp_client_message_ready)
        self.cmd_thread.started.connect(self.cmd_socket.start)
        self.cmd_socket.moveToThread(self.cmd_thread)
        self.cmd_thread.start()

    def on_cmd_status_update(self, status, addr):
        if status == TCPClient.STOP:
            self.ctrl_socket.close()

            self.ui.pushButton_ctrl.setText("START")
            self.ui.pushButton_ctrl.setStyleSheet(
                "background-color: green; color: white;"
            )

            self.cmd_socket.status.disconnect()
            self.cmd_socket.message.disconnect()
            self.cmd_thread.quit()

            self.ui.lineEdit_ip.setEnabled(True)
            self.ui.spinBox_ctrl_port.setEnabled(True)
            self.ui.spinBox_cmd_port.setEnabled(True)
            self.ui.spinBox_speed.setEnabled(True)

            self.ui.groupBox_ctrl.setEnabled(False)

        elif status == TCPClient.CONNECTED:
            self.config["IP"] = self.ui.lineEdit_ip.text()
            self.config["CTRL_PORT"] = self.ui.spinBox_ctrl_port.value()
            self.config["CMD_PORT"] = self.ui.spinBox_cmd_port.value()
            self.save_config()

            # self.ui.pushButton_init.setText('STOP')

            speed = self.ui.spinBox_speed.value()

            success = 0
            self.display_message("1;1;RSTALRM")
            success += self.ctrl_socket.sendrecv("1;1;RSTALRM")
            self.display_message("1;1;STOP")
            success += self.ctrl_socket.sendrecv("1;1;STOP")
            self.display_message("1;1;CNTLON")
            success += self.ctrl_socket.sendrecv("1;1;CNTLON")
            self.display_message("1;1;STATE")
            success += self.ctrl_socket.sendrecv("1;1;STATE")
            self.display_message("1;1;SRVON")
            success += self.ctrl_socket.sendrecv("1;1;SRVON")
            self.display_message("1;1;SLOTINIT")
            success += self.ctrl_socket.sendrecv("1;1;SLOTINIT")
            self.display_message("1;1;RUNARMSTRONG;0")
            success += self.ctrl_socket.sendrecv("1;1;RUNARMSTRONG;0")
            self.display_message("1;1;OVRD=" + str(speed))
            success += self.ctrl_socket.sendrecv("1;1;OVRD=" + str(speed))

            success = 0
            if success == 0:
                self.config["SPEED"] = speed
                self.save_config()

                self.ui.groupBox_ctrl.setEnabled(True)

            self.ui.pushButton_ctrl.setText("STOP")
            self.ui.pushButton_ctrl.setStyleSheet(
                "background-color: Red; color: white;"
            )
        self.ui.pushButton_ctrl.setEnabled(True)

    def on_tcp_client_message_ready(self, msg):
        self.ui.textBrowser.append(
            '<p style="text-align: center;">'
            + '<span style="color: #2196F3;"><strong>'
            + "Received: "
            + "</strong></span>"
            + '<span style="color: #2196F3;">'
            + msg
            + "</span></p>"
        )

    def display_message(self, msg):
        self.ui.textBrowser.append(
            '<p style="text-align: left;">'
            + '<span style="color: #000000;"><strong>'
            + "Sent: "
            + "</strong></span>"
            + '<span style="color: #000000;">'
            + msg
            + "</span></p>"
        )


if __name__ == "__main__":
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    sys.exit(app.exec())
