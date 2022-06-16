.. _Configuration_details:

#################
PMD Configuration
#################

The PMD's configuration file is located in the ts_config_ocs repository on GitHub.

The schema for the config file is fairly straightforward.
You have an object hub_config which contains an array that corresponds to the SAL Index of the CSC.
Inside of the array, there are fields that add metadata which describes the location and type of devices used on the hub.
It's important to note that the names array must be a non-empty value that corresponds to a device on the hub otherwise the CSC will not read from that device.
