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

import logging
import math
import os
import pathlib
import unittest

from lsst.ts import pmd, salobj

logging.basicConfig()
logger = logging.getLogger(__name__)

TEST_CONFIG_DIR = pathlib.Path(__file__).parents[1].joinpath("tests", "data", "config")

CONFIGS = [
    "_init.yaml",
]


class PMDCscTestCase(salobj.BaseCscTestCase, unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        os.environ["LSST_SITE"] = "pmd"
        return super().setUp()

    def basic_make_csc(
        self,
        index,
        initial_state,
        config_dir=TEST_CONFIG_DIR,
        simulation_mode=0,
        override="",
    ):
        return pmd.PMDCsc(
            initial_state=initial_state,
            index=index,
            config_dir=TEST_CONFIG_DIR,
            simulation_mode=simulation_mode,
            override=override,
        )

    async def test_standard_state_transitions(self):
        async with self.make_csc(
            initial_state=salobj.State.STANDBY, index=1, simulation_mode=1
        ):
            await self.check_standard_state_transitions(enabled_commands=[])

    async def test_bin_script(self):
        await self.check_bin_script(
            name="PMD",
            exe_name="run_pmd",
            index=1,
        )

    async def test_telemetry(self):
        async with self.make_csc(
            initial_state=salobj.State.ENABLED, index=1, simulation_mode=1
        ):
            position = await self.remote.tel_position.aget()
            self.assertTrue(not math.isnan(position.position[0]))
            self.assertTrue(not math.isnan(position.position[1]))
            self.assertTrue(not math.isnan(position.position[2]))
            self.assertTrue(not math.isnan(position.position[3]))
            self.assertTrue(math.isnan(position.position[4]))
            self.assertTrue(not math.isnan(position.position[5]))
            self.assertTrue(math.isnan(position.position[6]))
            self.assertTrue(math.isnan(position.position[7]))

    async def test_metadata(self):
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
            )
