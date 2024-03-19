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

__all__ = ["MockServer", "MockMitutoyoHub"]

import logging
import math

from lsst.ts import tcpip


class MockServer(tcpip.OneClientReadLoopServer):
    def __init__(self, log=None):
        if log is None:
            self.log = logging.getLogger(__name__)
        else:
            self.log = log
        self.device = MockMitutoyoHub()
        super().__init__(
            name="PMD Mock Server",
            host=tcpip.LOCAL_HOST,
            port=0,
            log=self.log,
            terminator=b"\r",
        )

    async def read_and_dispatch(self):
        line = await self.read_str()
        reply = self.device.parse_message(line)
        self.log.debug(f"{reply=}")
        await self.write_str(reply)


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
        self.commands["SPC"] = self.multiplexer_recovery
        self.commands["QU"] = self.multiplexer_recovery
        self.log = logging.getLogger(__name__)
        self.log.debug(f"{self.commands=}")
        self.fail_mode = False

    def parse_message(self, msg):
        self.log.debug(f"{msg=}")
        if msg in self.commands.keys():
            if not self.fail_mode:
                reply = self.commands[msg](msg)
                self.log.debug(f"{reply=}")
                return reply
            else:
                return ""
        raise NotImplementedError(f"{msg} not implemented.")

    def get_position(self, index):
        slot_position = self.positions[int(index) - 1]
        self.log.info(slot_position)
        if not math.isnan(slot_position):
            return f"{index}:{slot_position:+f}"
        else:
            return ""

    def multiplexer_recovery(self, something):
        return ""
