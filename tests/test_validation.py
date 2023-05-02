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

import unittest

import jsonschema
from lsst.ts import salobj
from lsst.ts.pmd.config_schema import CONFIG_SCHEMA


class ValidationTestCase(unittest.TestCase):
    def setUp(self):
        self.schema = CONFIG_SCHEMA
        self.validator = salobj.DefaultingValidator(schema=self.schema)

    def test_all_specified(self):
        data = {
            "hub_config": [
                {
                    "sal_index": 1,
                    "telemetry_interval": 1,
                    "devices": ["Dial Gage"],
                    "units": "um",
                    "location": "Office",
                    "host": "127.0.0.1",
                    "port": 9999,
                    "hub_type": "Mitutoyo",
                }
            ]
        }
        data_copy = data.copy()
        result = self.validator.validate(data)
        self.assertEqual(data, data_copy)
        for field, value in data.items():
            self.assertEqual(result[field], value)

    def test_invalid_configs(self):
        good_data = {
            "hub_config": [
                {
                    "sal_index": 1,
                    "telemetry_interval": 1,
                    "devices": ["Dial Gage"],
                    "units": "um",
                    "location": "Office",
                    "host": "127.0.0.1",
                    "port": 9999,
                    "hub_type": "Mitutoyo",
                }
            ]
        }
        bad_hub_items = {
            "hub_config": [
                {
                    "sal_index": 0,
                    "telemetry_interval": "Sandwich",
                    "devices": 1,
                    "units": "fff",
                    "location": 1,
                    "host": 12,
                    "port": "ninety-nine",
                    "hub_type": "Sandwich",
                }
            ]
        }
        for name, bad_value in bad_hub_items.items():
            bad_data = good_data.copy()
            bad_data["hub_config"][0][name] = bad_value
            with self.assertRaises(jsonschema.exceptions.ValidationError):
                self.validator.validate(bad_data)
