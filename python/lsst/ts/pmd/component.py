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
        self.simulation_mode = bool(simulation_mode)
        self.names = ["", "", "", "", "", "", "", ""]
        self.lock = asyncio.Lock()
        self.long_timeout = 30
        self.timeout = 5
        if log is None:
            self.log = logging.getLogger(type(self).__name__)
        else:
            self.log = log.getChild(type(self).__name__)
        self.client = tcpip.Client(host="", port=None, log=self.log)

    @property
    def connected(self):
        return self.client.connected

    async def connect(self):
        """Connect to the device."""
        self.client = tcpip.Client(
            host=self.host,
            port=self.port,
            log=self.log,
            name="PMD Client",
            terminator=b"\r",
        )
        await self.client.start_task

    async def disconnect(self):
        """Disconnect from the device."""
        try:
            await self.client.close()
        except Exception:
            self.log.exception("Failed to disconnect. Closing client anyway.")
        finally:
            self.client = tcpip.Client(host="", port=None, log=self.log)

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
            await self.client.write_str(msg)
            self.log.debug("Message written")
            # It seems there might be a bit of a lag, so adding a sleep here.
            await asyncio.sleep(0.1)
            reply = await self.client.read_str()
            self.log.debug(f"{reply=}")
            # Hub returns an empty string if a device is not read successfully
            # instead of raising a timeout exception
            if reply != "":
                self.log.debug(f"Read successful in send_msg, got {reply}")
            else:
                self.log.debug("Channel timed out or empty")
            return reply

    async def get_channel_position(self):
        """Get all device slot positions.

        Does not attempt to recover the multiplexor.

        Raises
        ------
        Exception
            Raised when the device is not connected.

        Returns
        -------
        positions : `list` of `float`
            An array of values from the devices.
        isok : `bool`
            Are all the values there?
        """

        if not self.connected:
            raise RuntimeError("Not connected")
        positions = [math.nan] * len(self.names)
        for i, name in enumerate(self.names):
            # Skip the channels that have nothing configured
            if name == "":
                continue
            reply = await self.send_msg(str(i + 1))
            self.log.debug(f"{reply=}")
            if reply != "":
                split_reply = reply.split(":")
                positions[i] = float(split_reply[-1])
                self.log.debug(f"{positions=}")
            else:
                # if multiplexer_recovery succeeds return position
                # else raise IOError
                isok = False
                return positions, isok
        # Return positions if successful with no recovery needed.
        isok = True
        return positions, isok

    async def determine_channel_positions(self, max_resets=3):
        """Recovery of multiplexer when a sensor drops out.

        Read slot positions with reseting the multiplexer if value fails.
        This is a work around for a faulty multiplexer which appears to drop
        the signal of devices in plugs 5-8.

        Raises
        ------
        RuntimeError
            Raised when the device is not connected.

        Returns
        -------
        positions : `float`
            The list of micrometer values.
        isok : `boolean`
            Indicates that reconnection was successful.
        """

        if not self.connected:
            raise RuntimeError("Not connected")

        # While read_error_count is less than or equal to 3 and not success
        # Continue to recover.
        # If success is True, break the loop.
        if max_resets < 0:
            raise ValueError("max_resets must be greater than or equal to 0.")
        for ntries in range(max_resets + 1):
            self.log.debug(f"{ntries=} of {max_resets=}")
            positions, isok = await self.get_channel_position()
            if isok:
                break
            # enter the config interface
            reply = await self.send_msg("SPC")
            await asyncio.sleep(5)
            self.log.debug(f"Multiplexer SPC response is: {reply}")
            reply3 = await self.send_msg("QU")
            await asyncio.sleep(2)
            self.log.debug(f"{reply3=}")
        return positions, isok
