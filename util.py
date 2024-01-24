import json
import time


def start_leftbot_sequence(msg_obj, ctrl_obj):
    """
    Start the left robot sequence.

    This function sends a series of commands to initialize and start the left robot sequence.

    :param msg_obj: The message object for displaying messages.
    :type msg_obj: callable
    :param ctrl_obj: The control object for sending commands to the left robot.
    :type ctrl_obj: TCPClient

    :return: 0 if the sequence is successfully started, 1 otherwise.
    :rtype: int
    """
    msg_obj("1;1;RSTALRM")
    if ctrl_obj.send_wait("1;1;RSTALRM"):
        return 1

    msg_obj("1;1;STOP")
    if ctrl_obj.send_wait("1;1;STOP"):
        return 1

    msg_obj("1;1;SRVOFF")
    if ctrl_obj.send_wait("1;1;SRVOFF"):
        return 1

    msg_obj("1;1;OPEN=")
    if ctrl_obj.send_wait("1;1;OPEN="):
        return 1

    msg_obj("1;1;CNTLON")
    if ctrl_obj.send_wait("1;1;CNTLON"):
        return 1

    msg_obj("1;1;SRVON")
    if ctrl_obj.send_wait("1;1;SRVON"):
        return 1

    msg_obj("1;1;SLOTINIT")
    if ctrl_obj.send_wait("1;1;SLOTINIT"):
        return 1

    msg_obj("1;1;RUNLEFTROBOT;0")
    if ctrl_obj.send_wait("1;1;RUNLEFTROBOT;0"):
        return 1

    time.sleep(1)

    return 0


def start_rightbot_sequence(msg_obj, ctrl_obj):
    """
    Start the right robot sequence.

    This function sends a series of commands to initialize and start the right robot sequence.

    :param msg_obj: The message object for displaying messages.
    :type msg_obj: callable
    :param ctrl_obj: The control object for sending commands to the right robot.
    :type ctrl_obj: TCPClient

    :return: 0 if the sequence is successfully started, 1 otherwise.
    :rtype: int
    """
    msg_obj("1;1;RSTALRM")
    if ctrl_obj.send_wait("1;1;RSTALRM"):
        return 1

    msg_obj("1;1;STOP")
    if ctrl_obj.send_wait("1;1;STOP"):
        return 1

    msg_obj("1;1;SRVOFF")
    if ctrl_obj.send_wait("1;1;SRVOFF"):
        return 1

    msg_obj("1;1;OPEN=")
    if ctrl_obj.send_wait("1;1;OPEN="):
        return 1

    msg_obj("1;1;CNTLON")
    if ctrl_obj.send_wait("1;1;CNTLON"):
        return 1

    msg_obj("1;1;SRVON")
    if ctrl_obj.send_wait("1;1;SRVON"):
        return 1

    msg_obj("1;1;SLOTINIT")
    if ctrl_obj.send_wait("1;1;SLOTINIT"):
        return 1

    msg_obj("1;1;RUNRIGHTROBOT;0")
    if ctrl_obj.send_wait("1;1;RUNRIGHTROBOT;0"):
        return 1

    time.sleep(1)

    return 0


def stop_sequence(msg_obj, ctrl_obj, unused_cmd_obj):
    """
    Stop the robot sequence.

    This function sends commands to stop the robot sequence.

    :param msg_obj: The message object for displaying messages.
    :type msg_obj: callable
    :param ctrl_obj: The control object for sending commands to the robot.
    :type ctrl_obj: TCPClient
    :param unused_cmd_obj: Unused command object.
    :type unused_cmd_obj: object

    :return: None
    """
    msg_obj("1;1;STOP")
    ctrl_obj.send("1;1;STOP")
    msg_obj("1;1;SRVOFF")
    ctrl_obj.send("1;1;SRVOFF")
    msg_obj("1;1;CNTLOFF")
    ctrl_obj.send("1;1;CNTLOFF")
    msg_obj("1;1;CLOSE")
    ctrl_obj.send("1;1;CLOSE")

    # ctrl_obj.close()
    # cmd_obj.close()


def save_config(config):
    """
    Save the configuration to a file.

    This function saves the provided configuration dictionary to a JSON file.

    :param config: The configuration dictionary to be saved.
    :type config: dict

    :return: None
    """
    try:
        with open("config.json", "w+", encoding="utf-8") as write_file:
            json.dump(config, write_file, indent=4)
    except PermissionError:
        pass


def html_received_msg(msg):
    """
    Format a received message as HTML.

    This function formats a received message as an HTML paragraph with a specific style.

    :param msg: The received message.
    :type msg: str

    :return: The formatted HTML string.
    :rtype: str
    """
    return (
        '<p style="text-align: center;">'
        + '<span style="color: #2196F3;"><strong>'
        + "Received: "
        + "</strong></span>"
        + '<span style="color: #2196F3;">'
        + msg
        + "</span></p>"
    )


def html_sent_msg(msg):
    """
    Format a sent message as HTML.

    This function formats a sent message as an HTML paragraph with a specific style.

    :param msg: The sent message.
    :type msg: str

    :return: The formatted HTML string.
    :rtype: str
    """
    return (
        '<p style="text-align: left;">'
        + '<span style="color: #000000;"><strong>'
        + "Sent: "
        + "</strong></span>"
        + '<span style="color: #000000;">'
        + msg
        + "</span></p>"
    )


def html_err_msg(msg):
    """
    Format an error message as HTML.

    This function formats an error message as an HTML paragraph with a specific style.

    :param msg: The error message.
    :type msg: str

    :return: The formatted HTML string.
    :rtype: str
    """
    return (
        '<p style="text-align: left;">'
        + '<span style="color: red;">'
        + msg
        + "</span></p>"
    )
