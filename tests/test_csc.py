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

import asyncio
import logging
import math
import pathlib
import unittest

from lsst.ts import pmd
from lsst.ts import salobj

logger = logging.getLogger(__name__)

TEST_CONFIG_DIR = pathlib.Path(__file__).parents[1].joinpath("tests", "data", "config")

CONFIGS = [
    "_init.yaml",
]


class PMDCscTestCase(salobj.BaseCscTestCase, unittest.IsolatedAsyncioTestCase):

    def basic_make_csc(
        self,
        index: int,
        initial_state: salobj.State | int,
        config_dir: str | pathlib.Path=TEST_CONFIG_DIR,
        simulation_mode: int=0,
        override: str="",
    ) -> pmd.PMDCsc:
        return pmd.PMDCsc(
            initial_state=initial_state,
            index=index,
            config_dir=TEST_CONFIG_DIR,
            simulation_mode=simulation_mode,
            override=override,
        )

    async def test_standard_state_transitions(self) -> None:
        async with self.make_csc(
            initial_state=salobj.State.STANDBY, index=1, simulation_mode=1
        ):
            await self.check_standard_state_transitions(enabled_commands=[], timeout=10)

    async def test_bin_script(self) -> None:
        await self.check_bin_script(
            name="PMD",
            exe_name="run_pmd",
            index=1,
        )

    async def test_telemetry(self) -> None:
        async with self.make_csc(
            initial_state=salobj.State.ENABLED, index=1, simulation_mode=1
        ):
            position = await self.remote.tel_position.aget(timeout=10)
            self.assertTrue(not math.isnan(position.position[0]))
            self.assertTrue(not math.isnan(position.position[1]))
            self.assertTrue(not math.isnan(position.position[2]))
            self.assertTrue(not math.isnan(position.position[3]))
            self.assertTrue(math.isnan(position.position[4]))
            self.assertTrue(not math.isnan(position.position[5]))
            self.assertTrue(math.isnan(position.position[6]))
            self.assertTrue(math.isnan(position.position[7]))

    async def test_retry(self) -> None:
        async with self.make_csc(
            initial_state=salobj.State.ENABLED, index=1, simulation_mode=1
        ):
            self.csc.simulator.device.fail_mode = True
            await asyncio.sleep(1)
            await self.assert_next_summary_state(state=salobj.State.FAULT, flush=True)

    async def test_metadata(self) -> None:
        async with self.make_csc(
            initial_state=salobj.State.DISABLED,
            index=1,
            config_dir=TEST_CONFIG_DIR,
            simulation_mode=1,
        ):
            await self.assert_next_sample(
                topic=self.remote.evt_metadata,
                hubType="Mitutoyo",
                location="AT",
                names="micrometer1,micrometer2,micrometer3,micrometer4,,micrometer5,,",
                units="um",
                timeout=10,
            )
