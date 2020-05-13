import os

from botocore.exceptions import ClientError
from datapump_utils.logger import get_logger

from datapump_utils.s3 import s3_client, get_s3_path_parts

LOGGER = get_logger(__name__)


def success_file_exists(results_path):
    bucket, prefix = get_s3_path_parts(results_path)

    try:
        # this will throw exception if success file isn't present
        s3_client().head_object(
            Bucket=bucket, Key=f"{prefix}/_SUCCESS",
        )

        return True
    except ClientError:
        return False


def get_result_uris(results_path):
    bucket, prefix = get_s3_path_parts(results_path)
    object_list = s3_client().list_objects(Bucket=bucket, Prefix=prefix)

    keys = [object["Key"] for object in object_list["Contents"]]
    csv_keys = filter(lambda key: key.endswith(".csv"), keys)

    # sometimes Spark creates empty partitions when it shuffles, but the GFW API will throw errors if you try
    # to upload an empty file, so just remove these from the list
    nonempty_csv_keys = []
    for key in csv_keys:
        meta = s3_client().head_object(Bucket=bucket, Key=key)
        if meta["ContentLength"] > 0:
            nonempty_csv_keys.append(key)

    return [f"https://{bucket}.s3.amazonaws.com/{key}" for key in nonempty_csv_keys]
