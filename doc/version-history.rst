.. _version_history:Version_History:

===============
Version History
===============

v0.2.1
======
* Updated unit tests to use the correct configuration file name
* Fixed when a device fails to report its position that it returns an empty string instead of reporting a timeout exception

v0.2.0
======
* Added log handling over DDS
* Added transitions to fault state when telemetry loop has a problem and when the device fails to connect
* Fixed bug where serial_port configuration was not being respected
* Added basic support for CscCommander class 

0.1.0
=====
* Added initial CSC
* Added position telemetry
* Added metadata event
* Added Mitutoyo hub component
* Added conda recipe
* Upgrade to black 20.8
* Fix conda package