from urllib.parse import urlparse


def s3_directory_exists(bucket, prefix, s3_client):
    return s3_client.list_objects(Bucket=bucket, Prefix=prefix)


def get_s3_path_parts(path):
    parsed = urlparse(path)
    bucket = parsed.netloc
    key = parsed.path
    return bucket, key