# pylint: disable=too-many-lines
"""
This module provides an app named "ArmStrong" that controls the motion of a robot arm.

The app uses Python to communicate with the robot arm and send commands to it.
The app is designed to be easy to use and can be customized to suit different needs.

By: Zhengyu Peng <zhengyu.peng@aptiv.com>

"""

import sys
import math
from pathlib import Path
import json

from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import QThread, QFile
from PySide6.QtUiTools import QUiLoader

from tcpclient import TCPClient

_VERSION_ = "v3.2"
STATUS_STR = (
    '<a href="https://hpc-gitlab.aptiv.com/zjx8rj/automation#armstrong">New Release</a>'  # pylint: disable=line-too-long
    + "&nbsp;•&nbsp;"
    + '<a href="https://hpc-gitlab.aptiv.com/zjx8rj/automation/-/issues">Issue Tracker</a>'
    + "&nbsp;•&nbsp;"
    + '<a href="https://hpc-gitlab.aptiv.com/zjx8rj/automation/-/tree/main/armstrong_matlab">MATLAB API</a>'  # pylint: disable=line-too-long
    + "&nbsp;•&nbsp;"
    + '<a href="https://hpc-gitlab.aptiv.com/zjx8rj/automation/-/tree/main/#armstrong">CANape Lib</a>'  # pylint: disable=line-too-long
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


class MyApp(QtWidgets.QMainWindow):  # pylint: disable=too-many-public-methods
    """
    The ArmStrong GUI for robot arm control
    """

    def __init__(self):
        """
        Initializes the MyApp class.

        :return: None
        """
        super().__init__()

        config_file = Path("config.json")
        if config_file.exists():
            with open("config.json", "r", encoding="utf-8") as read_file:
                self.config = json.load(read_file)
        else:
            self.config = {}
            with open("config.json", "w+", encoding="utf-8") as write_file:
                json.dump(self.config, write_file)

        self.ctrl_thread = None
        self.ctrl_socket = None
        self.cmd_thread = None
        self.cmd_socket = None

        # Load UI
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
        """
        Initializes the user interface of the MyApp class.

        :return: None
        """
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

        self.ui.groupBox_ctrl.setStyleSheet(
            ":enabled { background-color: white;} :disabled {background-color: #EEEEEE}"
        )

        self.ui.pushButton_load.setStyleSheet(
            ":enabled { background-color: #E0F2F1;} :disabled {background-color: #E0E0E0}"
        )
        self.ui.pushButton_home.setStyleSheet(
            ":enabled { background-color: #E0F2F1;} :disabled {background-color: #E0E0E0}"
        )
        self.ui.pushButton_minrange.setStyleSheet(
            ":enabled { background-color: #E0F2F1;} :disabled {background-color: #E0E0E0}"
        )
        self.ui.pushButton_set.setStyleSheet(
            ":enabled { background-color: #E0F2F1;} :disabled {background-color: #E0E0E0}"
        )

    def save_config(self):
        """
        Saves the configuration settings to a JSON file.

        :return: None
        """
        try:
            with open("config.json", "w+", encoding="utf-8") as write_file:
                json.dump(self.config, write_file)
        except PermissionError:
            pass

    def coordinate_changed(self, idx):
        """
        Updates the UI based on the selected coordinate system.

        :param idx: The index of the selected coordinate system.
        :type idx: int
        :return: None
        """
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
        """
        Calculates the yaw, pitch, and roll angles for a backmount radar system using yaw and pitch.

        :param theta_h: The horizontal angle in degrees.
        :type theta_h: float
        :param theta_v: The vertical angle in degrees.
        :type theta_v: float
        :param roll_offset: The roll offset in degrees.
        :type roll_offset: float
        :return: A tuple containing the yaw, pitch, roll, and error message (if any).
        :rtype: tuple
        """
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
        """
        Calculates the yaw, pitch, and roll angles for a backmount radar system using yaw and roll.

        :param theta_h: The horizontal angle in degrees.
        :type theta_h: float
        :param theta_v: The vertical angle in degrees.
        :type theta_v: float
        :param roll_offset: The roll offset in degrees.
        :type roll_offset: float
        :return: A tuple containing the yaw, pitch, roll, and error message (if any).
        :rtype: tuple
        """
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
        """
        Calculates the yaw, pitch, and roll angles for a topmount radar system using yaw and roll.

        :param theta_h: The horizontal angle in degrees.
        :type theta_h: float
        :param theta_v: The vertical angle in degrees.
        :type theta_v: float
        :param roll_offset: The roll offset in degrees.
        :type roll_offset: float
        :return: A tuple containing the yaw, pitch, roll, and error message (if any).
        :rtype: tuple
        """
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
        """
        Calculates the yaw, pitch, and roll angles for a backmount radar system using yaw and pitch.

        :param azimuth: The azimuth angle in degrees.
        :type azimuth: float
        :param elevation: The elevation angle in degrees.
        :type elevation: float
        :param roll_offset: The roll offset in degrees.
        :type roll_offset: float
        :return: A tuple containing the yaw, pitch, roll, and error message (if any).
        :rtype: tuple
        """
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
        """
        Calculate yaw, pitch, and roll angles for a backmount device.

        :param float azimuth: Azimuth angle in degrees.
        :param float elevation: Elevation angle in degrees.
        :param float roll_offset: Roll offset angle in degrees.

        :return: Tuple[float, float, float, str]
            A tuple containing the calculated yaw, pitch, roll angles, and an error message.

        The function calculates the yaw, pitch, and roll angles based on the provided azimuth,
        elevation, and roll_offset. The result is returned as a tuple, and any errors
        encountered during the calculation are included in the 'err' field of the tuple.

        Note:
        - Azimuth and elevation are expected in degrees.
        - The angles are returned in degrees.
        """
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
        """
        Calculate yaw, pitch, and roll angles for a topmount device.

        :param float azimuth: Azimuth angle in degrees.
        :param float elevation: Elevation angle in degrees.
        :param float roll_offset: Roll offset angle in degrees.

        :return: Tuple[float, float, float, str]
            A tuple containing the calculated yaw, pitch, roll angles, and an error message.

        The function calculates the yaw, pitch, and roll angles based on the provided azimuth,
        elevation, and roll_offset for a topmount device. The result is returned as a tuple,
        and any errors encountered during the calculation are included in the 'err' field
        of the tuple.

        Note:
        - Azimuth and elevation are expected in degrees.
        - The angles are returned in degrees.
        """
        err = ""
        yaw = -elevation + 90.0
        pitch = 0.0
        roll = 90.0 + azimuth + roll_offset

        return yaw, pitch, roll, err

    def on_load_button_clicked(self):
        """
        Handle the event when the load button is clicked.

        This method prepares a task command and associated parameters, constructs a message,
        displays the message, sends it via the command socket, and enables a specific UI button.

        :return: None

        The method performs the following steps:
        1. Set task command (`tsk_cmd`) to "2.0".
        2. Set azimuth (`azi`), elevation (`ele`), roll (`rol`), and offsets to "0.0".
        3. Construct a message (`msg`) by concatenating the parameters with commas.
        4. Display the message using the `display_message` method.
        5. Send and receive the message via the command socket (`cmd_socket`).
        6. Enable a specific UI button (`pushButton_set`).

        Note:
        - Parameters are represented as strings ("0.0").
        - The message format is "<tsk_cmd>,<azi>,<ele>,<rol>,<x_offset>,<y_offset>,
        <z_offset>,<tool_x>,<tool_y>,<tool_z>\r\n".
        """
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
        """
        Handle the event when the home button is clicked.

        This method saves the current configuration of tool coordinates, updates the task command
        and associated parameters, constructs a message, displays the message, sends it via the
        command socket, and enables a specific UI button.

        :return: None

        The method performs the following steps:
        1. Save the current tool coordinates to the configuration (`config`)
        using doubleSpinBox values.
        2. Set task command (`tsk_cmd`) to "1.0".
        3. Set azimuth (`azi`), elevation (`ele`), roll (`rol`), and offsets to "0.0".
        4. Retrieve tool coordinates from the configuration for the Z-axis (`tool_z`).
        5. Construct a message (`msg`) by concatenating the parameters with commas.
        6. Display the message using the `display_message` method.
        7. Send and receive the message via the command socket (`cmd_socket`).
        8. Enable a specific UI button (`pushButton_set`).

        Note:
        - Parameters are represented as strings ("0.0").
        - The message format is "<tsk_cmd>,<azi>,<ele>,<rol>,<x_offset>,<y_offset>,
        <z_offset>,<tool_x>,<tool_y>,<tool_z>\r\n".
        """
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
        """
        Handle the event when the minrange button is clicked.

        This method updates the task command and associated parameters for setting minimum range,
        constructs a message, displays the message, sends it via the command socket, and enables
        a specific UI button.

        :return: None

        The method performs the following steps:
        1. Set task command (`tsk_cmd`) to "5.0".
        2. Set azimuth (`azi`) and roll (`rol`) to "0.0".
        3. Retrieve elevation value from the spinBox (`spinBox_minrange`) for the
        elevation parameter (`ele`).
        4. Set offsets and tool coordinates to "0.0".
        5. Construct a message (`msg`) by concatenating the parameters with commas.
        6. Display the message using the `display_message` method.
        7. Send and receive the message via the command socket (`cmd_socket`).
        8. Enable a specific UI button (`pushButton_set`).

        Note:
        - Parameters are represented as strings ("0.0").
        - The message format is "<tsk_cmd>,<azi>,<ele>,<rol>,<x_offset>,<y_offset>,
        <z_offset>,<tool_x>,<tool_y>,<tool_z>\r\n".
        """
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
        """
        Handle the event when the set button is clicked.

        This method sets the robot position based on the selected coordinate system and angles.
        It constructs a message, displays the message, sends it via the command socket, and updates
        the configuration with the current tool coordinates.

        :return: None

        The method performs the following steps:
        1. Disable the set button (`pushButton_set`).
        2. Set task command (`tsk_cmd`) to "3.0".
        3. Retrieve angles from UI doubleSpinBox elements (`doubleSpinBox_az`,
        `doubleSpinBox_el`, `doubleSpinBox_roll`).
        4. Determine the coordinate system based on the selected index in comboBox_coord.
        5. Calculate yaw, pitch, and roll based on the selected coordinate system using
        specific methods.
        6. Display an error message if any calculation error occurs.
        7. Check if the calculated angles are within the specified range.
        8. If angles are within the range, construct a message (`msg`) and display it.
        9. Send and receive the message via the command socket (`cmd_socket`).
        10. Update the configuration with the current tool coordinates.
        11. Enable the set button (`pushButton_set`).

        Note:
        - Parameters and angles are represented as strings.
        - The message format is "<tsk_cmd>,<yaw>,<pitch>,<roll>,<x_offset>,<y_offset>,
        <z_offset>,<tool_x>,<tool_y>,<tool_z>\r\n".
        """
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
        """
        Update the value of the x-coordinate based on the slider position.

        :param float val: The slider position representing the x-coordinate.

        :return: None

        The method sets the value of the x-coordinate in the associated
        doubleSpinBox (`doubleSpinBox_x`)
        based on the provided slider position.
        """
        self.ui.doubleSpinBox_x.setValue(val)

    def x_spinbox(self, val):
        """
        Update the value of the x-coordinate based on the spinbox input.

        :param float val: The input value representing the x-coordinate.

        :return: None

        The method sets the value of the x-coordinate in the associated
        horizontalSlider (`horizontalSlider_x`)
        based on the provided input value and enables the set button (`pushButton_set`).
        """
        self.ui.horizontalSlider_x.setValue(val)
        self.ui.pushButton_set.setEnabled(True)

    def y_slider(self, val):
        """
        Update the value of the y-coordinate based on the slider position.

        :param float val: The slider position representing the y-coordinate.

        :return: None

        The method sets the value of the y-coordinate in the associated
        doubleSpinBox (`doubleSpinBox_y`)
        based on the provided slider position.
        """
        self.ui.doubleSpinBox_y.setValue(val)

    def y_spinbox(self, val):
        """
        Update the value of the y-coordinate based on the spinbox input.

        :param float val: The input value representing the y-coordinate.

        :return: None

        The method sets the value of the y-coordinate in the associated
        horizontalSlider (`horizontalSlider_y`)
        based on the provided input value and enables the set button (`pushButton_set`).
        """
        self.ui.horizontalSlider_y.setValue(val)
        self.ui.pushButton_set.setEnabled(True)

    def z_slider(self, val):
        """
        Update the value of the z-coordinate based on the slider position.

        :param float val: The slider position representing the z-coordinate.

        :return: None

        The method sets the value of the z-coordinate in the associated
        doubleSpinBox (`doubleSpinBox_z`)
        based on the provided slider position.
        """
        self.ui.doubleSpinBox_z.setValue(val)

    def z_spinbox(self, val):
        """
        Update the value of the z-coordinate based on the spinbox input.

        :param float val: The input value representing the z-coordinate.

        :return: None

        The method sets the value of the z-coordinate in the associated
        horizontalSlider (`horizontalSlider_z`)
        based on the provided input value and enables the set button (`pushButton_set`).
        """
        self.ui.horizontalSlider_z.setValue(val)
        self.ui.pushButton_set.setEnabled(True)

    def minrange_slider(self, val):
        """
        Update the value of the minimum range based on the slider position.

        :param float val: The slider position representing the minimum range.

        :return: None

        The method sets the value of the minimum range in the associated
        spinBox (`spinBox_minrange`)
        based on the provided slider position.
        """
        self.ui.spinBox_minrange.setValue(val)

    def minrange_spinbox(self, val):
        """
        Update the value of the minimum range based on the spinbox input.

        :param float val: The input value representing the minimum range.

        :return: None

        The method sets the value of the minimum range in the associated
        horizontalSlider (`horizontalSlider_minrange`)
        based on the provided input value and enables the set button (`pushButton_set`).
        """
        self.ui.horizontalSlider_minrange.setValue(val)

    def tool_slider_x(self, val):
        """
        Update the value of the tool x-coordinate based on the slider position.

        :param float val: The slider position representing the tool x-coordinate.

        :return: None

        The method sets the value of the tool x-coordinate in the associated
        doubleSpinBox (`doubleSpinBox_toolx`)
        based on the provided slider position and enables the set button (`pushButton_set`).
        """
        self.ui.doubleSpinBox_toolx.setValue(val)

    def tool_spinbox_x(self, val):
        """
        Update the value of the tool x-coordinate based on the spinbox input.

        :param float val: The input value representing the tool x-coordinate.

        :return: None

        The method sets the value of the tool x-coordinate in the associated
        horizontalSlider (`horizontalSlider_toolx`)
        based on the provided input value and enables the set button (`pushButton_set`).
        """
        self.ui.horizontalSlider_toolx.setValue(val)
        self.ui.pushButton_set.setEnabled(True)

    def tool_slider_y(self, val):
        """
        Update the value of the tool y-coordinate based on the slider position.

        :param float val: The slider position representing the tool y-coordinate.

        :return: None

        The method sets the value of the tool y-coordinate in the associated
        doubleSpinBox (`doubleSpinBox_tooly`)
        based on the provided slider position.
        """
        self.ui.doubleSpinBox_tooly.setValue(val)

    def tool_spinbox_y(self, val):
        """
        Update the value of the tool y-coordinate based on the spinbox input.

        :param float val: The input value representing the tool y-coordinate.

        :return: None

        The method sets the value of the tool y-coordinate in the associated
        horizontalSlider (`horizontalSlider_tooly`)
        based on the provided input value and enables the set button (`pushButton_set`).
        """
        self.ui.horizontalSlider_tooly.setValue(val)
        self.ui.pushButton_set.setEnabled(True)

    def tool_slider_z(self, val):
        """
        Update the value of the tool z-coordinate based on the slider position.

        :param float val: The slider position representing the tool z-coordinate.

        :return: None

        The method sets the value of the tool z-coordinate in the associated
        doubleSpinBox (`doubleSpinBox_toolz`)
        based on the provided slider position.
        """
        self.ui.doubleSpinBox_toolz.setValue(val)

    def tool_spinbox_z(self, val):
        """
        Update the value of the tool z-coordinate based on the spinbox input.

        :param float val: The input value representing the tool z-coordinate.

        :return: None

        The method sets the value of the tool z-coordinate in the associated
        horizontalSlider (`horizontalSlider_toolz`)
        based on the provided input value and enables the set button (`pushButton_set`).
        """
        self.ui.horizontalSlider_toolz.setValue(val)
        self.ui.pushButton_set.setEnabled(True)

    def az_dial(self, val):
        """
        Update the value of the azimuth angle based on the dial input.

        :param float val: The dial input representing the azimuth angle.

        :return: None

        The method sets the value of the azimuth angle in the associated
        doubleSpinBox (`doubleSpinBox_az`)
        based on the provided dial input.
        """
        self.ui.doubleSpinBox_az.setValue(val)

    def az_spinbox(self, val):
        """
        Update the value of the azimuth angle based on the spinbox input.

        :param float val: The input value representing the azimuth angle.

        :return: None

        The method sets the value of the azimuth angle in the associated dial (`dial_az`)
        based on the provided input value and enables the set button (`pushButton_set`).
        """
        self.ui.dial_az.setValue(val)
        self.ui.pushButton_set.setEnabled(True)

    def el_dial(self, val):
        """
        Update the value of the elevation angle based on the dial input.

        :param float val: The dial input representing the elevation angle.

        :return: None

        The method sets the value of the elevation angle in the associated
        doubleSpinBox (`doubleSpinBox_el`)
        based on the provided dial input.
        """
        self.ui.doubleSpinBox_el.setValue(val)

    def el_spinbox(self, val):
        """
        Update the value of the elevation angle based on the spinbox input.

        :param float val: The input value representing the elevation angle.

        :return: None

        The method sets the value of the elevation angle in the associated dial (`dial_el`)
        based on the provided input value and enables the set button (`pushButton_set`).
        """
        self.ui.dial_el.setValue(val)
        self.ui.pushButton_set.setEnabled(True)

    def roll_dial(self, val):
        """
        Update the value of the roll angle based on the dial input.

        :param float val: The dial input representing the roll angle.

        :return: None

        The method sets the value of the roll angle in the associated
        doubleSpinBox (`doubleSpinBox_roll`)
        based on the provided dial input.
        """
        self.ui.doubleSpinBox_roll.setValue(val)

    def roll_spinbox(self, val):
        """
        Update the value of the roll angle based on the spinbox input.

        :param float val: The input value representing the roll angle.

        :return: None

        The method sets the value of the roll angle in the associated dial (`dial_roll`)
        based on the provided input value and enables the set button (`pushButton_set`).
        """
        self.ui.dial_roll.setValue(val)
        self.ui.pushButton_set.setEnabled(True)

    def on_ctrl_connect_button_clicked(self):
        """
        Handle the event when the control connect button is clicked.

        This method manages the connection and disconnection of the control socket based on the
        current state of the button ("START" or "STOP"). It updates the UI elements accordingly.

        :return: None

        The method performs the following steps:
        1. If the button text is "START":
           a. Disable the control connect button (`pushButton_ctrl`).
           b. Change the button appearance to indicate it's in progress.
           c. Disable relevant UI elements (IP, control port, command port, speed).
           d. Create a control socket (`ctrl_socket`) and move it to a separate
           thread (`ctrl_thread`).
           e. Connect signals to update status and handle incoming messages.
           f. Start the control thread.
        2. If the button text is "STOP":
           a. Disable the control connect button (`pushButton_ctrl`).
           b. Change the button appearance to indicate it's in progress.
           c. Display and send "STOP," "SRVOFF," and "CNTLOFF" commands to the control socket.
           d. Close the control socket.
           e. Close the command socket.

        Note:
        - The control socket (`ctrl_socket`) and control thread (`ctrl_thread`)
        are instance variables.
        """
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

    def on_ctrl_status_update(self, status, unused_addr):
        """
        Handle the update of the control socket status.

        This method is called when the status of the control socket
        changes. It updates the UI elements based on the new status
        and performs necessary actions.

        :param int status: The new status of the control socket.
        :param str addr: The address of the control socket.

        :return: None

        The method performs the following steps:
        1. If the new status is STOP:
           a. Set the control connect button text to "START."
           b. Change the button appearance to indicate it's ready to start.
           c. Disconnect signals and quit the control thread.
           d. Enable relevant UI elements (IP, control port, command port, speed).
           e. Disable the control group box (`groupBox_ctrl`).
           f. Enable the control connect button (`pushButton_ctrl`).
        2. If the new status is CONNECTED:
           a. Call the `connect_cmd_port` method to establish a connection on the command port.
        """
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
        """
        Establish a connection on the command port.

        This method creates a new command socket (`cmd_socket`)
        and moves it to a separate thread (`cmd_thread`).
        It connects signals to update status and handle incoming
        messages and starts the command thread.

        :return: None

        The method performs the following steps:
        1. Create a new command thread (`cmd_thread`).
        2. Create a new command socket (`cmd_socket`) with the provided IP and command port values.
        3. Connect signals to update status and handle incoming messages.
        4. Start the command thread.
        """
        self.cmd_thread = QThread()
        self.cmd_socket = TCPClient(
            self.ui.lineEdit_ip.text(), self.ui.spinBox_cmd_port.value()
        )

        self.cmd_socket.status.connect(self.on_cmd_status_update)
        self.cmd_socket.message.connect(self.on_tcp_client_message_ready)
        self.cmd_thread.started.connect(self.cmd_socket.start)
        self.cmd_socket.moveToThread(self.cmd_thread)
        self.cmd_thread.start()

    def on_cmd_status_update(self, status, unused_addr):
        """
        Handle the update of the command socket status.

        This method is called when the status of the command socket changes.
        It updates the UI elements based on the new status and performs
        necessary actions.

        :param int status: The new status of the command socket.
        :param str addr: The address of the command socket.

        :return: None

        The method performs the following steps:
        1. If the new status is STOP:
           a. Close the control socket (`ctrl_socket`).
           b. Set the control connect button text to "START."
           c. Change the button appearance to indicate it's ready to start.
           d. Disconnect signals and quit the command thread.
           e. Enable relevant UI elements (IP, control port, command port, speed).
           f. Disable the control group box (`groupBox_ctrl`).
        2. If the new status is CONNECTED:
           a. Save the configuration with the updated IP and port values.
           b. Set up the control socket with necessary initialization commands.
           c. If the initialization commands are successful, update the
           configuration and enable the control group box.
           d. Set the control connect button text to "STOP."
           e. Change the button appearance to indicate it's in progress.
           f. Enable the control connect button (`pushButton_ctrl`).
        """
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
        """
        Handle the event when a message is ready from the TCP client.

        This method is called when a message is received from the TCP
        client. It appends the received message to the text browser in
        the user interface.

        :param str msg: The received message.

        :return: None
        """
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
        """
        Display a message in the text browser.

        This method appends a formatted message to the text browser in
        the user interface, indicating whether the message was sent or received.

        :param str msg: The message to be displayed.

        :return: None
        """
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
