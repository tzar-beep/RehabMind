"""Idempotently provision self-hosted S3-compatible storage (MinIO).

Enforces the audio privacy baseline:
  - private bucket: no bucket policy, no anonymous access
  - versioning NOT enabled (deleted audio must not survive as old versions)
  - lifecycle expiry after 1 day as a backstop for orphaned objects
    (the application deletes audio immediately after processing)
  - a least-privilege application user (S3_ACCESS_KEY) limited to put/get/delete under
    audio/ in this bucket; the application never uses the root credentials

Root credentials are read from MINIO_ROOT_USER / MINIO_ROOT_PASSWORD only here.

Usage:
  uv run python -m app.scripts.provision_storage                        # local development
  python -m app.scripts.provision_storage --confirm-production          # self-hosted stack
"""

import argparse
import os
import sys
import time
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from minio import MinioAdmin
from minio.credentials import StaticProvider

from app.core.config import ROOT_ENV_FILE, get_settings

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
POLICY_NAME = "rehabmind-audio"


def _root_credentials() -> tuple[str, str]:
    if ROOT_ENV_FILE.exists():  # local development: same .env as the app
        from dotenv import dotenv_values

        env = {**dotenv_values(ROOT_ENV_FILE), **os.environ}
    else:
        env = dict(os.environ)
    return env["MINIO_ROOT_USER"], env["MINIO_ROOT_PASSWORD"]  # type: ignore[return-value]


def provision(confirm_production: bool) -> None:
    s = get_settings()
    host = urlparse(s.s3_endpoint_url or "").hostname
    if s.app_env == "production" and not confirm_production:
        sys.exit("refused: pass --confirm-production to provision production storage")
    if s.app_env == "development" and host not in LOCAL_HOSTS:
        sys.exit(f"refused: non-local endpoint {s.s3_endpoint_url} in development")

    root_user, root_password = _root_credentials()
    s3 = boto3.client(
        "s3",
        endpoint_url=s.s3_endpoint_url,
        region_name=s.s3_region,
        aws_access_key_id=root_user,
        aws_secret_access_key=root_password,
    )
    for _ in range(30):
        try:
            s3.list_buckets()
            break
        except EndpointConnectionError:
            time.sleep(1)
    else:
        sys.exit(f"storage not reachable at {s.s3_endpoint_url}")

    bucket = s.s3_bucket_audio
    try:
        s3.head_bucket(Bucket=bucket)
    except ClientError:
        s3.create_bucket(Bucket=bucket)
        print(f"created bucket {bucket}")
    try:
        s3.delete_bucket_policy(Bucket=bucket)
    except ClientError:
        pass
    if s3.get_bucket_versioning(Bucket=bucket).get("Status") == "Enabled":
        sys.exit(f"versioning is enabled on {bucket}; deleted audio would be retained")
    s3.put_bucket_lifecycle_configuration(
        Bucket=bucket,
        LifecycleConfiguration={
            "Rules": [
                {
                    "ID": "expire-ephemeral-audio",
                    "Status": "Enabled",
                    "Filter": {"Prefix": ""},
                    "Expiration": {"Days": 1},
                }
            ]
        },
    )
    print(f"bucket {bucket}: private, unversioned, 1-day expiry backstop")

    endpoint = urlparse(s.s3_endpoint_url or "")
    admin = MinioAdmin(
        endpoint=endpoint.netloc,
        credentials=StaticProvider(root_user, root_password),
        secure=endpoint.scheme == "https",
    )
    admin.policy_add(
        POLICY_NAME,
        policy={
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
                    "Resource": [f"arn:aws:s3:::{bucket}/audio/*"],
                },
                {
                    # HeadBucket for readiness checks only.
                    "Effect": "Allow",
                    "Action": ["s3:ListBucket"],
                    "Resource": [f"arn:aws:s3:::{bucket}"],
                },
            ],
        },
    )
    admin.user_add(s.s3_access_key, s.s3_secret_key.get_secret_value())
    try:
        admin.attach_policy([POLICY_NAME], user=s.s3_access_key)
    except Exception as e:
        if "already" not in str(e).lower():
            raise
    print(f"user {s.s3_access_key}: limited to {bucket}/audio/*")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--confirm-production", action="store_true")
    provision(parser.parse_args().confirm_production)
