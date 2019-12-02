import boto3


def get_token(env) -> str:
    sm_client = boto3.client("secretsmanager")
    return sm_client.get_secret_value(
        SecretId=f"gfw-api/{get_secret_suffix(env)}-token"
    )


def get_secret_suffix(env) -> str:
    if env == "production":
        suffix: str = "prod"
    else:
        suffix = "staging"
    return suffix
