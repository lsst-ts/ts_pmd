"""Sphinx configuration file for TSSW package"""

from typing import Any
from documenteer.conf.pipelinespkg import *  # type: ignore # noqa

project = "ts_pmd"  # noqa
html_theme_options["logotext"] = project  # type: ignore # noqa
html_title = project  # noqa
doxylink: dict[Any, Any] = {}
html_short_title = project  # noqa

intersphinx_mapping["ts_xml"] = ("https://ts-xml.lsst.io", None)  # type: ignore # noqa
intersphinx_mapping["ts_salobj"] = ("https://ts-salobj.lsst.io", None)  # type: ignore # noqa
