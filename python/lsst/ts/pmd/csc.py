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

__all__ = ["PMDCsc", "run_pmd", "command_pmd"]

import asyncio

from lsst.ts import salobj, utils

from . import __version__
from .component import MitutoyoComponent
from .config_schema import CONFIG_SCHEMA
from .enums import ErrorCode
from .mock_server import MockServer


class PMDCsc(salobj.ConfigurableCsc):
    """The CSC for the Position Measurement Device.

    Parameters
    ----------
    index : `int`
        The index of the CSC.
    simulation_mode : `int`
        Whether the CSC is in simulation mode.
    initial_state : `lsst.ts.salobj.State`
        The initial_state of the CSC.
    config_dir : `pathlib.Path`
        The path of the configuration directory.

    Attributes
    ----------
    telemetry_task : `asyncio.Future`
        The task for running the telemetry loop.
    telemetry_interval : `float`
        The interval that telemetry is published at. (Seconds)
    component : `MitutoyoComponent`
        The component for the PMD.
    """

    valid_simulation_modes = (0, 1)
    """The valid simulation modes for the PMD."""
    version = __version__

    def __init__(
        self,
        index,
        simulation_mode=0,
        initial_state=salobj.State.STANDBY,
        config_dir=None,
        override="",
    ):
        super().__init__(
            name="PMD",
            index=index,
            config_dir=config_dir,
            initial_state=initial_state,
            simulation_mode=simulation_mode,
            config_schema=CONFIG_SCHEMA,
            override=override,
        )
        self.telemetry_task = utils.make_done_future()
        self.telemetry_interval = 1
        self.index = index
        self.component = None
        self.simulator = None

    async def configure(self, config):
        """Configure the CSC.

        Parameters
        ----------
        config : `types.Simplenamespace`
            The configuration object.
        """
        self.log.info(config)
        self.telemetry_interval = config.hub_config[self.index - 1][
            "telemetry_interval"
        ]
        if config.hub_config[self.index - 1]["hub_type"] == "Mitutoyo":
            self.component = MitutoyoComponent(self.simulation_mode, log=self.log)
        self.component.configure(config.hub_config[self.index - 1])
        await self.evt_metadata.set_write(
            hubType=self.component.hub_type,
            location=self.component.location,
            names=",".join(self.component.names),
            units=self.component.units,
        )

    async def telemetry(self):
        """Execute the telemetry loop."""
        try:
            self.log.debug("Begin sending telemetry")
            position = None
            breakpoint
            while True:
                position, isok = await self.component.determine_channel_positions()
                if not isok:
                    await self.fault(
                        ErrorCode.CHANNEL_RECOVERY_FAILED,
                        report="Failed to recover multiplexer.",
                    )
                self.log.debug(
                    "telemetry_loop received position data, now publishing event"
                )
                await self.tel_position.set_write(position=position)
                position = None  # reset so it's easier to debug exceptions
                await asyncio.sleep(self.telemetry_interval)
        except asyncio.CancelledError:
            self.log.info("Telemetry loop cancelled")

    async def handle_summary_state(self):
        """Handle the summary states."""
        if self.disabled_or_enabled:
            if self.simulation_mode and self.simulator is None:
                self.simulator = MockServer(log=self.log)
                await self.simulator.start_task
                self.component.port = self.simulator.port
            if not self.component.connected:
                try:
                    self.log.debug("in handle_summary_state: connecting")
                    await self.component.connect()
                except Exception as e:
                    self.log.error(
                        f"Connection failed. {self.component.host=} {self.component.port=}: {e!r}"
                    )
                    await self.fault(ErrorCode.HARDWARE_CONNECTION_FAILED, e.args)
            if self.telemetry_task.done():
                self.telemetry_task = asyncio.create_task(self.telemetry())
        else:
            self.log.debug(
                f"Transitioning to {self.summary_state}; cancelling telemetry loop and disconnecting."
            )
            self.telemetry_task.cancel()
            if self.component is not None:
                await self.component.disconnect()
                self.component = None
            if self.simulator is not None:
                await self.simulator.close()
                self.simulator = None

    async def close_tasks(self):
        """Close the CSC for cleanup."""
        await super().close_tasks()
        self.telemetry_task.cancel()
        if self.component is not None:
            await self.component.disconnect()
        if self.simulator is not None:
            await self.simulator.close()
            self.simulator = None

    @staticmethod
    def get_config_pkg():
        """Get the configuration package directory."""
        return "ts_config_ocs"


def run_pmd():
    """Run PMDCsc from the command line."""
    asyncio.run(PMDCsc.amain(index=True))


def command_pmd():
    """Run a PMD commander from the command line."""
    asyncio.run(salobj.CscCommander.amain(name="PMD", index=True))
