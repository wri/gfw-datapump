import click
import boto3
from datetime import date, datetime
import json
import uuid
from collections import defaultdict

# python ./tools/create_datasets.py --features s3://gfw-files/2018_update/tsv/gadm36_adm2_1_1.csv --feature_type gadm --worker_count 100 --analysis firealerts --version v20200807 --fire_alert_type viirs --env production
# python ./tools/create_datasets.py --features s3://gfw-files/2018_update/tsv/gadm36_adm2_1_1.csv --feature_type gadm --worker_count 100 --analysis firealerts --version v20200807 --fire_alert_type modis --env production
# python ./tools/create_datasets.py --features s3://gfw-data-lake/wdpa_protected_areas/v202007/text/wdpa_protected_areas_v202007_1x1.tsv  --feature_type wdpa --worker_count 80 --analysis firealerts --version v20200807 --fire_alert_type viirs --env production
# python ./tools/create_datasets.py --features s3://gfw-data-lake/wdpa_protected_areas/v202007/text/wdpa_protected_areas_v202007_1x1.tsv  --feature_type wdpa --worker_count 80 --analysis firealerts --version v20200807 --fire_alert_type modis --env production
# python ./tools/create_datasets.py --features s3://gfw-files/2018_update/tsv/gadm36_adm2_1_1.csv --feature_type gadm --worker_count 150 --analysis annualupdate_minimal --version v20200807 --tcl_year 2019 --env production
# python ./tools/create_datasets.py --features s3://gfw-data-lake/wdpa_protected_areas/v202007/text/wdpa_protected_areas_v202007_1x1.tsv --feature_type wdpa --worker_count 150 --analysis annualupdate_minimal --version v20200807 --tcl_year 2019 --env production
# python ./tools/create_datasets.py --features s3://gfw-files/2018_update/tsv/gadm36_adm2_1_1.csv --feature_type gadm --worker_count 100 --analysis gladalerts --version v20200807 --env production
# python ./tools/create_datasets.py --features s3://gfw-data-lake/wdpa_protected_areas/v202007/text/wdpa_protected_areas_v202007_1x1.tsv  --feature_type wdpa --worker_count 100 --analysis gladalerts --version v20200807 --env production
# python ./tools/create_datasets.py --features "s3://gfw-pipelines/geotrellis/features/geostore/*.tsv" --feature_type geostore --worker_count 150 --analysis annualupdate_minimal --version v20200807 --tcl_year 2019 --env production
# python ./tools/create_datasets.py --features "s3://gfw-pipelines/geotrellis/features/geostore/*.tsv" --feature_type geostore --worker_count 100 --analysis gladalerts --version v20200807 --env production
# python ./tools/create_datasets.py --features "s3://gfw-pipelines/geotrellis/features/geostore/*.tsv" --feature_type geostore --worker_count 100 --analysis firealerts --version v20200807 --env production --fire_alert_type viirs
# python ./tools/create_datasets.py --features "s3://gfw-pipelines/geotrellis/features/geostore/*.tsv" --feature_type geostore --worker_count 100 --analysis firealerts --version v20200807 --env production --fire_alert_type modis


@click.command()
@click.option("--env", help="Environment", required=True)
@click.option("--features", help="feature URI", required=True)
@click.option(
    "--feature_type",
    type=click.Choice(["gadm", "wdpa", "geostore"], case_sensitive=False),
    help="feature type",
    required=True,
)
@click.option(
    "--analysis",
    type=click.Choice(
        ["annualupdate_minimal", "gladalerts", "firealerts"], case_sensitive=False
    ),
    help="analysis type",
    required=True,
)
@click.option("--worker_count", help="number of worker instances", required=True)
@click.option("--instance_type", default="r4.2xlarge", help="EC2 instance type")
@click.option("--version", required=True, help="Quarterly version in form vYYYYMMDD")
@click.option(
    "--tcl_year",
    default=None,
    help="Tree cover loss year, required if running tcl analysis",
)
@click.option(
    "--fire_alert_type", type=click.Choice(["modis", "viirs"]), default=None,
)
@click.option(
    "--geotrellis_jar", default=None,
)
def pump_data(
    env,
    features,
    feature_type,
    analysis,
    worker_count,
    instance_type,
    version,
    tcl_year,
    fire_alert_type,
    geotrellis_jar,
):
    if "annualupdate" in analysis and not tcl_year:
        print("FAILURE: tcl_year parameter required for tree cover loss analysis")
        return

    request = {
        "Input": {
            "instance_size": instance_type,
            "instance_count": int(worker_count),
            "feature_src": features,
            "feature_type": feature_type,
            "analyses": [analysis],
            "name": f"{analysis}_{feature_type}{'_' + fire_alert_type if fire_alert_type else ''}_{date.today()}",
            "upload_type": "create",
            "get_summary": True,
            "datasets": get_dataset_names(
                feature_type, analysis, version, tcl_year, fire_alert_type
            ),
            "geotrellis_jar": geotrellis_jar,
        }
    }

    if fire_alert_type:
        request["Input"]["fire_config"] = {
            fire_alert_type: get_fire_src(fire_alert_type)
        }

    input = json.dumps(request)  # double dump because sfn client requires escaped JSON

    sfn_client = boto3.client("stepfunctions")
    if env == "production":
        arn = "arn:aws:states:us-east-1:401951483516:stateMachine:datapump-geotrellis_dataset-default"
    else:
        arn = "arn:aws:states:us-east-1:274931322839:stateMachine:datapump-geotrellis_dataset-default"

    execution_id = uuid.uuid4().hex
    response = sfn_client.start_execution(
        stateMachineArn=arn, name=execution_id, input=input,
    )

    print(f"Running job with execution arn {response['executionArn']}")


def get_fire_src(fire_alert_type):
    if fire_alert_type == "viirs":
        return [
            "s3://gfw-data-lake/nasa_viirs_fire_alerts/v1/vector/epsg-4326/tsv/near_real_time/*.tsv",
            "s3://gfw-data-lake/nasa_viirs_fire_alerts/v1/vector/epsg-4326/tsv/scientific/*.tsv",
        ]
    else:
        return [
            "s3://gfw-data-lake/nasa_modis_fire_alerts/v6/vector/epsg-4326/tsv/near_real_time/*.tsv",
            "s3://gfw-data-lake/nasa_modis_fire_alerts/v6/vector/epsg-4326/tsv/scientific/*.tsv",
        ]


def get_dataset_names(
    feature_type, analysis, version, tcl_year=None, fire_alert_type=None
):
    if feature_type == "gadm":
        if analysis == "annualupdate_minimal":
            return {
                "annualupdate_minimal": {
                    "iso": {
                        "change": f"Tree Cover Loss {tcl_year} Change - GADM Iso level - {version}",
                        "summary": f"Tree Cover Loss {tcl_year} Summary - GADM Iso level - {version}",
                        "whitelist": f"Tree Cover Loss {tcl_year} Whitelist - GADM Iso level - {version}",
                    },
                    "adm1": {
                        "change": f"Tree Cover Loss {tcl_year} Change - GADM Adm1 level - {version}",
                        "summary": f"Tree Cover Loss {tcl_year} Summary - GADM Adm1 level - {version}",
                        "whitelist": f"Tree Cover Loss {tcl_year} Whitelist - GADM Adm1 level - {version}",
                    },
                    "adm2": {
                        "change": f"Tree Cover Loss {tcl_year} Change - GADM Adm2 level - {version}",
                        "summary": f"Tree Cover Loss {tcl_year} Summary - GADM Adm2 level - {version}",
                        "whitelist": f"Tree Cover Loss {tcl_year} Whitelist - GADM Adm2 level - {version}",
                    },
                },
            }
        elif analysis == "gladalerts":
            return {
                "gladalerts": {
                    "iso": {
                        "weekly_alerts": f"Glad Alerts Weekly Change - GADM Iso level - {version}",
                        "summary": f"Glad Alerts Summary - GADM Iso level - {version}",
                        "whitelist": f"Glad Alerts Whitelist - GADM Iso level - {version}",
                    },
                    "adm1": {
                        "weekly_alerts": f"Glad Alerts Weekly Change - GADM Adm1 level - {version}",
                        "summary": f"Glad Alerts Summary - GADM Adm1 level - {version}",
                        "whitelist": f"Glad Alerts Whitelist - GADM Adm1 level - {version}",
                    },
                    "adm2": {
                        "daily_alerts": f"Glad Alerts Daily Change - GADM Adm2 level - {version}",
                        "weekly_alerts": f"Glad Alerts Weekly Change - GADM Adm2 level - {version}",
                        "summary": f"Glad Alerts Summary - GADM Adm2 level - {version}",
                        "whitelist": f"Glad Alerts Whitelist - GADM Adm2 level - {version}",
                    },
                },
            }
        elif analysis == "firealerts":
            datasets = {
                f"firealerts_{fire_alert_type.lower()}": {
                    "iso": {
                        "whitelist": f"{fire_alert_type.upper()} Fire Alerts Whitelist - GADM Iso level - {version}",
                        "weekly_alerts": f"{fire_alert_type.upper()} Fire Alerts Weekly Change - GADM Iso level - {version}",
                    },
                    "adm1": {
                        "whitelist": f"{fire_alert_type.upper()} Fire Alerts Whitelist - GADM Adm1 level - {version}",
                        "weekly_alerts": f"{fire_alert_type.upper()} Fire Alerts Weekly Change - GADM Adm1 level - {version}",
                    },
                    "adm2": {
                        "whitelist": f"{fire_alert_type.upper()} Fire Alerts Whitelist - GADM Adm2 level - {version}",
                        "daily_alerts": f"{fire_alert_type.upper()} Fire Alerts Daily Change - GADM Adm2 level - {version}",
                        "weekly_alerts": f"{fire_alert_type.upper()} Fire Alerts Weekly Change - GADM Adm2 level - {version}",
                    },
                },
            }

            # Run this manually afterwards, it takes ~6 hours to upload and will block all the other datasets
            # if "firealerts_viirs" in datasets:
            #     datasets["firealerts_viirs"]["all"] =  f"VIIRS Fire Alerts - All - {version}"

            return datasets
    elif feature_type == "wdpa":
        if analysis == "annualupdate_minimal":
            return {
                "annualupdate_minimal": {
                    "change": f"Tree Cover Loss {tcl_year} Change - WDPA- {version}",
                    "summary": f"Tree Cover Loss {tcl_year} Summary - WDPA - {version}",
                    "whitelist": f"Tree Cover Loss {tcl_year} Whitelist - WDPA - {version}",
                },
            }
        elif analysis == "gladalerts":
            return {
                "gladalerts": {
                    "daily_alerts": f"Glad Alerts Daily Change - WDPA - {version}",
                    "weekly_alerts": f"Glad Alerts Weekly Change - WDPA - {version}",
                    "summary": f"Glad Alerts Summary - WDPA - {version}",
                    "whitelist": f"Glad Alerts Whitelist - WDPA - {version}",
                },
            }
        elif analysis == "firealerts":
            return {
                f"firealerts_{fire_alert_type.lower()}": {
                    "daily_alerts": f"{fire_alert_type.upper()} Fire Alerts Daily Change - WDPA - {version}",
                    "weekly_alerts": f"{fire_alert_type.upper()} Fire Alerts Weekly Change - WDPA - {version}",
                },
            }
    elif feature_type == "geostore":
        if analysis == "annualupdate_minimal":
            return {
                "annualupdate_minimal": {
                    "change": f"Tree Cover Loss {tcl_year} Change - Geostore - {version}",
                    "summary": f"Tree Cover Loss {tcl_year} Summary - Geostore - {version}",
                    "whitelist": f"Tree Cover Loss {tcl_year} Whitelist - Geostore - {version}",
                },
            }
        elif analysis == "gladalerts":
            return {
                "gladalerts": {
                    "daily_alerts": f"Glad Alerts Daily Change - Geostore - {version}",
                    "weekly_alerts": f"Glad Alerts Weekly Change - Geostore - {version}",
                    "summary": f"Glad Alerts Summary - Geostore - {version}",
                    "whitelist": f"Glad Alerts Whitelist - Geostore - {version}",
                }
            }
        elif analysis == "firealerts":
            return {
                f"firealerts_{fire_alert_type.lower()}": {
                    "daily_alerts": f"{fire_alert_type.upper()} Fire Alerts Daily Change - Geostore - {version}",
                    "weekly_alerts": f"{fire_alert_type.upper()} Fire Alerts Weekly Change - Geostore - {version}",
                    "whitelist": f"{fire_alert_type.upper()} Fire Alerts Whitelist - Geostore - {version}",
                },
            }


if __name__ == "__main__":
    pump_data()
