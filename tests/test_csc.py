import unittest
import math
import pathlib
import logging

from lsst.ts import salobj, pmd

logging.basicConfig()
logger = logging.getLogger(__name__)

TEST_CONFIG_DIR = pathlib.Path(__file__).parents[1].joinpath("tests", "data", "config")

CONFIGS = [
    "metadata_test.yaml",
]


class PMDCscTestCase(unittest.IsolatedAsyncioTestCase, salobj.BaseCscTestCase):
    def basic_make_csc(
        self,
        index,
        initial_state,
        config_dir=TEST_CONFIG_DIR,
        simulation_mode=0,
        settings_to_apply="",
    ):
        return pmd.PMDCsc(
            initial_state=initial_state,
            index=index,
            config_dir=TEST_CONFIG_DIR,
            simulation_mode=simulation_mode,
            settings_to_apply=settings_to_apply,
        )

    async def test_standard_state_transitions(self):
        async with self.make_csc(
            initial_state=salobj.State.STANDBY, index=1, simulation_mode=1
        ):
            await self.check_standard_state_transitions(
                enabled_commands=[], settingsToApply="current"
            )

    async def test_bin_script(self):
        await self.check_bin_script(
            name="PMD",
            exe_name="run_pmd.py",
            index=1,
        )

    async def test_telemetry(self):
        async with self.make_csc(
            initial_state=salobj.State.ENABLED,
            index=1,
            simulation_mode=1,
            settings_to_apply="current",
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
            settings_to_apply="current",
        ):
            tmp = await self.remote.evt_metadata.aget()
            logger.debug(f"tmp is {tmp}")
            await self.assert_next_sample(
                topic=self.remote.evt_metadata,
                hubType="Mitutoyo",
                location="AT",
                names="micrometer1,micrometer2,micrometer3,micrometer4,,micrometer5,,",
                units="um",
            )


if __name__ == "__main__":
    unittest.main()
