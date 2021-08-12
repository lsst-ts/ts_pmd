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

__all__ = ["MockSerial", "MockMitutoyoHub"]

import logging
import queue
import math

import serial


class MockSerial(serial.Serial):
    def __init__(
        self,
        port,
        baudrate=9600,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=3,
        xonxoff=False,
        rtscts=False,
        write_timeout=None,
        dsrdtr=False,
        inter_byte_timeout=None,
        exclusive=None,
    ):
        super().__init__(
            port=port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            timeout=timeout,
            xonxoff=xonxoff,
            rtscts=rtscts,
            write_timeout=write_timeout,
            dsrdtr=dsrdtr,
            inter_byte_timeout=inter_byte_timeout,
            exclusive=exclusive,
        )
        self.log = logging.getLogger(__name__)

        self.device = MockMitutoyoHub()
        self.message_queue = queue.Queue()

        self.log.info("Mock Serial created.")

    def read_until(self, character):
        self.log.info("Reading from queue.")
        if not self.message_queue.empty():
            msg = self.message_queue.get()
            return msg.encode()
        raise Exception("Port timed out.")

    def write(self, data):
        self.log.info(data)
        msg = self.device.parse_message(data)
        self.log.debug(msg)
        self.message_queue.put(msg)
        self.log.info("Putting into queue")


class MockMitutoyoHub:
    def __init__(
        self,
        positions=[
            0.00009,
            0.001,
            0.002,
            0.003,
            math.nan,
            0.005,
            math.nan,
            math.nan,
        ],
    ):
        self.positions = positions
        if len(self.positions) != 8:
            raise Exception("positions must contain exactly 8 values.")
        self.commands = {str(i): self.get_position for i in range(1, 9)}
        self.log = logging.getLogger(__name__)
        self.log.info(self.commands)

    def parse_message(self, msg):
        self.log.info(msg)
        msg = msg.decode().rstrip("\r\n")
        self.log.info(msg)
        # raise Exception("Intentional Failure")
        if msg in self.commands.keys():
            reply = self.commands[msg](msg)
            if reply is not None:
                self.log.info(reply)
                return reply
        raise NotImplementedError(f"{msg} not implemented.")

    def get_position(self, index):
        slot_position = self.positions[int(index) - 1]
        self.log.info(slot_position)
        if not math.isnan(slot_position):
            return f"{index}:{slot_position:+f}\r"
        else:
            return "\r"
