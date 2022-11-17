__all__ = ["CONFIG_SCHEMA"]

import yaml

CONFIG_SCHEMA = yaml.safe_load(
    """
$schema: http://json-schema.org/draft-07/schema#
$id: https://github.com/lsst-ts/ts_pmd/blob/master/schema/PMDevice.yaml
title: PMD v3
description: Schema for PMD configuration files
definitions:
  hub_specific_schema:
    type: object
    properties:
      sal_index:
        type: number
        minValue: 1
        description: The SAL Component index.
      telemetry_interval:
        description: The interval at which telemetry is published. (Seconds)
        type: number
      devices:
        type: array
        description: Names of the devices.
        items:
          type: string
        minItems: 1
        maxItems: 8
      units:
        type: string
        description: Units of measurement for the devices and the unit should be a valid astropy.units string.
      location:
        type: string
        description: The location of the device.
      host:
        type: string
        description: The IP Address or host of the terminal server.
      port:
        type: number
        description: The port of the ip address of the terminal server
      hub_type:
        type: string
        description: The brand/type of device hub.
        enum: ["Mitutoyo"]
    required: [telemetry_interval, devices, units,  location, host, port, hub_type]
    additionalProperties: false
type: object
properties:
  hub_config:
    type: array
    items:
      "$ref": "#/definitions/hub_specific_schema"
required: [hub_config]
additional_properties: false
"""
)
