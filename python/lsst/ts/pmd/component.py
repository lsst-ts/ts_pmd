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

import asyncio
import logging
import math
import time

from lsst.ts import tcpip

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
        self.read_error_count = 0
        self.reader = None
        self.writer = None
        self.lock = asyncio.Lock()
        self.long_timeout = 30
        self.timeout = 5
        if log is None:
            self.log = logging.getLogger(type(self).__name__)
        else:
            self.log = log.getChild(type(self).__name__)

    async def connect(self):
        """Connect to the device."""
        async with self.lock:
            connect_task = asyncio.open_connection(host=self.host, port=int(self.port))
            self.reader, self.writer = await asyncio.wait_for(
                connect_task, timeout=self.long_timeout
            )
            self.connected = True
            self.log.debug("Connection to device completed")

    async def disconnect(self):
        """Disconnect from the device."""
        async with self.lock:
            if self.writer is None:
                return
            try:
                await tcpip.close_stream_writer(self.writer)
            except Exception:
                self.log.exception("Disconnect failed, continuing")
            finally:
                self.writer = None
                self.reader = None
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
        self.host = config["host"]
        self.port = config["port"]

        self.log.debug("Configuration completed")

    async def send_msg(self, msg):
        """Send a message to the device.

        Parameters
        ----------
        msg : `str`
            The message to send.

        Raises
        ------
        RuntimeError
            Raised when the device is not connected.

        Returns
        -------
        reply : `bytes`
            The reply from the device.
        """

        async with self.lock:
            if not self.connected:
                raise RuntimeError("Not connected")
            self.log.debug(f"Message to be sent is {msg}")
            msg = msg + "\r"
            msg = msg.encode()
            if self.writer is not None:
                self.writer.write(msg)
                await self.writer.drain()
            self.log.debug("Message written")
            # It seems there might be a bit of a lag, so adding a sleep here.
            time.sleep(0.1)
            reply = await asyncio.wait_for(
                self.reader.readuntil(b"\r"), timeout=self.timeout
            )
            # Hub returns an empty string if a device is not read successfully
            # instead of raising a timeout exception
            if reply != b"":
                self.log.debug(f"Read successful in send_msg, got {reply}")
            else:
                reply = b"\r"
                self.log.debug("Channel timed out or empty")
            return reply

    async def get_slots_position(self):
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
            reply = await self.send_msg(str(i + 1))
            # an empty reading returns b'', unsure what b"\r" is but was
            # here originally
            if reply != b"\r":
                split_reply = reply.decode().split(":")
                position[i] = float(split_reply[-1])
            else:
                position[i] = math.nan
                # Try to recover multiplexer
                self.log.error(
                    f"Sensor {name} is not reading. {self.read_error_count} continuous read errors reported"
                )

                if self.read_error_count == 2 and self.multiplexer_recovery():
                    self.log.info("Multiplexer recovered")
                    self.read_error_count = 0
                else:
                    self.read_error_count += 1
                    self.log.error(
                        "Multiplexer recovery failed "
                        f"{self.read_error_count} times"
                        " continuously"
                    )

        if self.read_error_count <= 3:
            return position
        else:
            err_msg = "Three continuous reads of sensor ended in error."
            self.log.exception(err_msg)
            raise IOError(err_msg)

    async def multiplexer_recovery(self):
        """Recovery of multiplexer when a sensor drops out.
        This is a work around for a faulty multiplexer which appears to drop
        the signal of devices in plugs 5-8.

        Raises
        ------
        RuntimeError
            Raised when the device is not connected.

        Returns
        -------
        success : `boolean`
            Indicates that reconnection was successful.
        """

        if not self.connected:
            raise RuntimeError("Not connected")

        # enter the config interface
        reply = await self.send_msg("SPC")
        await asyncio.sleep(5)
        self.log.debug(f"Multiplexer SPC response is: {reply}")
        reply3 = self.send_msg("QU")
        await asyncio.sleep(2)
        self.log.debug(f"{reply3=}")

        # now check the sensors
        positions = await self.get_slots_position()
        success = True
        for i, name in enumerate(self.names):
            # Skip the channels that have nothing configured
            if name == "":
                continue
            elif positions[i]:
                self.log.debug(f"Sensor {i} = {positions[i]:0.3f}")
            else:
                self.log.error(
                    f"Sensor {i} returned a blank string. " "Multiplexer reset failed."
                )
                success = False

        return success
