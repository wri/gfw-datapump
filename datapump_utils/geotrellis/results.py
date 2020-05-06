import os

from botocore.exceptions import ClientError
from datapump_utils.logger import get_logger

from datapump_utils.s3 import s3_client

LOGGER = get_logger(__name__)


def success_file_exists(result_path):
    try:
        # this will throw exception if success file isn't present
        s3_client().head_object(
            Bucket=os.environ["S3_BUCKET_PIPELINE"], Key=f"{result_path}/_SUCCESS",
        )

        return True
    except ClientError:
        return False


def get_result_uris(results_path):
    result_bucket = os.environ["S3_BUCKET_PIPELINE"]
    object_list = s3_client().list_objects(Bucket=result_bucket, Prefix=results_path)

    keys = [object["Key"] for object in object_list["Contents"]]
    csv_keys = filter(lambda key: key.endswith(".csv"), keys)

    # sometimes Spark creates empty partitions when it shuffles, but the GFW API will throw errors if you try
    # to upload an empty file, so just remove these from the list
    nonempty_csv_keys = []
    for key in csv_keys:
        meta = s3_client().head_object(Bucket=result_bucket, Key=key)
        if meta["ContentLength"] > 0:
            nonempty_csv_keys.append(key)

    return [
        f"https://{result_bucket}.s3.amazonaws.com/{key}" for key in nonempty_csv_keys
    ]
