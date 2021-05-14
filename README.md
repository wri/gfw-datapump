# datapump

An AWS Step Function for ingesting data or reading data from the gfw-data-api, running some analysis on it, and then uploading the results to the gfw-data-api. Currently mainly focused of geotrellis-based zonal statistics using gfw_forest_loss_geotrellis.

### Commands

Different workflows can be triggered by submitting different JSON commands. Currently supported commands:

#### Analysis Command

This will run a supported analysis on a dataset version in the gfw-data-api, and automatically upload results back to the gfw-data-api.

```json
{
  "command": "analysis",
  "parameters": {
    "analysis_version": "Versioning for analysis run (e.g. v2020Q4)",
    "sync": "Whether or not to include when syncing results after ingesting new data. See Sync Command below.",
    "geotrellis_version":  "Version of geotrellis jar to use, if running a geotrellis analysis",
    "tables": [
      {
        "dataset": "Valid dataset on gfw-data-api",
        "version": "Valid version of above dataset. Must have a 1x1 grid asset if doing geotrellis analysis.",
        "analysis": "Analysis to perform. Must be one of [tcl, glad, viirs, modis]."
      },
      ...
    ]
  }
}
```

#### Sync Command

TThis will attempt to ingest new data for each listed sync type, and will update appropriate analyses if sync was set to true when they were created.

```json
{
  "command": "sync",
  "parameters": {
    "types": ["List of sync types to run, must be from [viirs, modis, glad, rw_areas]"],
    "sync_version": "Version to use to indicate which sync this is from. If empty, will by default use vYYYYMMDD based on the current date."
  }
}
```
