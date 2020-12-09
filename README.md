# datapump

An AWS Step Function for ingesting data or reading data from the gfw-data-api, running some analysis on it, and then uploading the results to the gfw-data-api. Currently mainly focused of geotrellis-based zonal statistics using gfw_forest_loss_geotrellis.

### Commands

Different workflows can be triggered by submitting different JSON commands. Currently supported commands:

#### Data API Analysis Command

This will run a supported analysis on a dataset version in the gfw-data-api, and automatically upload results back to the gfw-data-api.