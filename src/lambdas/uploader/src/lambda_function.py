from datapump.globals import LOGGER, GLOBALS
from datapump.jobs.jobs import JobStatus
from datapump.jobs.geotrellis import GeotrellisJob
from datapump.clients.data_api import DataApiClient
from datapump.commands import Analysis


def handler(event, context):
    try:
        job = GeotrellisJob(**event)
        client = DataApiClient()

        if job.status == JobStatus.analyzed:
            job = _upload(job, client)
        elif job.status == JobStatus.uploading:
            job = _check_upload(job, client)

        return job.dict()
    except Exception as e:
        LOGGER.exception(e)
        job.status = JobStatus.failed
        return job.dict()


def _upload(job: GeotrellisJob, client: DataApiClient):
    for table in job.result_tables:
        if job.sync_version:
            # temporarily just appending sync versions to analysis version instead of using version inheritance
            if job.table.analysis == Analysis.glad:
                client.copy_version(
                    table.dataset, job.analysis_version, table.version, table.source_uri
                )
            else:
                client.append(table.dataset, table.version, table.source_uri)
        else:
            client.create_dataset_and_version(
                table.dataset,
                table.version,
                table.source_uri,
                table.index_columns,
                table.index_columns,
                table.table_schema,
            )
    job.status = JobStatus.uploading
    return job


def _check_upload(job: GeotrellisJob, client: DataApiClient):
    all_saved = True
    for table in job.result_tables:
        status = client.get_version(table.dataset, table.version)["status"]
        if status == "failed":
            job.status = JobStatus.failed
            return job

        all_saved &= status == "saved"

    if all_saved:
        if job.table.analysis == Analysis.glad and job.sync_version:
            for table in job.result_tables:
                dataset = client.get_dataset(table.dataset)
                versions = dataset["versions"]
                versions_to_delete = versions[: -GLOBALS.max_versions]
                for version in versions_to_delete:
                    client.delete_version(table.dataset, version)

                client.set_latest(table.dataset, job.sync_version)

        job.status = JobStatus.complete

    return job
