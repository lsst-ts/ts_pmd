# This file is part of ts_pmd.
#
# Developed for the Vera Rubin Telescope and Site Project.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__all__ = ["MitutoyoComponent"]

import math
import pty
import os
import logging

import serial

from .mock_server import MockSerial

SIMULATION_SERIAL_PORT = "/dev/ttyUSB0"
READ_TIMEOUT = 5.0  # [seconds]


class MitutoyoComponent:
    """Mitutoyo controller.

    A class for the Mitutoyo dial gauge.

    Parameters
    ----------
    simulation_mode : `bool`
        Whether the component is in simulation mode.

    Attributes
    ----------
    position : `float`
        The position of the device.
    connected : `bool`
        Whether the device is connected.
    """

    def __init__(self, simulation_mode, log=None):
        self.connected = False
        self.simulation_mode = bool(simulation_mode)
        self.names = ["", "", "", "", "", "", "", ""]
        if log is None:
            self.log = logging.getLogger(type(self).__name__)
        else:
            self.log = log.getChild(type(self).__name__)

    def connect(self):
        """Connect to the device."""
        if not self.simulation_mode:
            try:
                self.log.debug("Trying to open serial connection")
                self.commander = serial.Serial(
                    port=self.serial_port, timeout=READ_TIMEOUT
                )
            except Exception as e:
                self.log.exception(e)
                raise
        else:
            main, reader = pty.openpty()
            self.log.debug("Creating MOCK serial connection")
            self.commander = MockSerial(os.ttyname(main))

        self.connected = True
        self.log.debug("Connection to device completed")

    def disconnect(self):
        """Disconnect from the device."""
        self.log.debug("Disconnecting serial device")
        self.commander.close()
        self.connected = False

    def configure(self, config):
        """Configure the device.

        Parameters
        ----------
        config : `types.Simplenamespace`
            The configuration object.
        """
        for index, device in enumerate(config["devices"]):
            self.names[index] = device
        self.hub_type = config["hub_type"]
        self.units = config["units"]
        self.location = config["location"]
        self.serial_port = config["serial_port"]

        self.log.debug("Configuration completed")

    def send_msg(self, msg):
        """Send a message to the device.

        Parameters
        ----------
        msg : `str`
            The message to send.

        Raises
        ------
        Exception
            Raised when the device is not connected.

        Returns
        -------
        reply : `bytes`
            The reply from the device.
        """

        if not self.connected:
            raise Exception("Not connected")
        self.log.debug(f"Message to be sent is {msg}")
        self.commander.write(f"{msg}\r".encode())
        self.log.debug("Message written")
        reply = self.commander.read_until(b"\r")
        # Hub returns an empty string if a device is not read successfully
        # instead of raising a timeout exception
        if reply != b"":
            self.log.debug(f"Read successful in send_msg, got {reply}")
            return reply
        else:
            reply = b"\r"
            self.log.debug("Channel timed out or empty")
            return reply

    def get_slots_position(self):
        """Get all device slot positions.

        Raises
        ------
        Exception
            Raised when the device is not connected.

        Returns
        -------
        position : `list` of `float`
            An array of values from the devices.
        """

        if not self.connected:
            raise Exception("Not connected")
        position = [
            math.nan,
            math.nan,
            math.nan,
            math.nan,
            math.nan,
            math.nan,
            math.nan,
            math.nan,
        ]
        for i, name in enumerate(self.names):
            # Skip the channels that have nothing configured
            if name == "":
                continue
            reply = self.send_msg(str(i + 1))
            # an empty reading returns b'', unsure what b"\r" is but was
            # here originally
            if reply != b"\r":
                split_reply = reply.decode().split(":")
                position[i] = float(split_reply[-1])
            else:
                position[i] = math.nan
        return position
