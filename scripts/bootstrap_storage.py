# /// script
# requires-python = ">=3.12"
# dependencies = ["boto3>=1.35", "python-dotenv>=1.0"]
# ///
"""Idempotently provision local S3-compatible storage (MinIO) for development.

Enforces the audio privacy baseline on the bucket:
  - private: no bucket policy, no anonymous access
  - versioning NOT enabled (deleted audio must not survive as old versions)
  - lifecycle expiry after 1 day as a backstop for orphaned objects
    (the application deletes audio immediately after processing)

Development only. Production buckets are provisioned by infrastructure code.

Usage:  uv run scripts/bootstrap_storage.py
"""

import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def fail(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    if os.environ.get("APP_ENV") != "development":
        fail("APP_ENV must be 'development'")

    endpoint = os.environ["S3_ENDPOINT_URL"]
    if urlparse(endpoint).hostname not in {"localhost", "127.0.0.1", "::1"}:
        fail(f"refusing to run against non-local endpoint {endpoint}")

    bucket = os.environ["S3_BUCKET_AUDIO"]
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name=os.environ.get("S3_REGION", "us-east-1"),
        aws_access_key_id=os.environ["MINIO_ROOT_USER"],
        aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
    )

    for attempt in range(30):
        try:
            s3.list_buckets()
            break
        except EndpointConnectionError:
            time.sleep(1)
    else:
        fail(f"storage not reachable at {endpoint}; is `docker compose up` running?")

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
        fail(f"versioning is enabled on {bucket}; deleted audio would be retained")

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

    rules = s3.get_bucket_lifecycle_configuration(Bucket=bucket)["Rules"]
    assert any(r["ID"] == "expire-ephemeral-audio" for r in rules)
    print(f"bucket {bucket}: private, unversioned, 1-day expiry backstop")


if __name__ == "__main__":
    main()
