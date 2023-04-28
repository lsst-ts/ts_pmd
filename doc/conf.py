"""Sphinx configuration file for TSSW package"""

from documenteer.conf.pipelinespkg import *  # noqa

project = "ts_pmd"  # noqa
html_theme_options["logotext"] = project  # noqa
html_title = project  # noqa
doxylink = {}
html_short_title = project  # noqa

intersphinx_mapping["ts_xml"] = ("https://ts-xml.lsst.io", None)  # noqa
intersphinx_mapping["ts_salobj"] = ("https://ts-salobj.lsst.io", None)  # noqa
