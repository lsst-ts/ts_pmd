__all__ = ["execute_csc"]

import asyncio

from lsst.ts import salobj

from .csc import PMDCsc


def execute_csc():
    asyncio.run(PMDCsc.amain(index=True))


def command_csc():
    asyncio.run(salobj.CscCommander.amain(name="PMD", index=True))
