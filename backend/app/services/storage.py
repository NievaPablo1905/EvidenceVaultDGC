"""MinIO storage service."""
import io
from typing import BinaryIO

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

_client: Minio | None = None


def get_minio_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_SECURE,
        )
        _ensure_bucket(_client)
    return _client


def _ensure_bucket(client: Minio) -> None:
    bucket = settings.MINIO_BUCKET
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
    except S3Error as exc:
        raise RuntimeError(f"Cannot initialise MinIO bucket '{bucket}': {exc}") from exc


def upload_evidence(object_key: str, data: BinaryIO, size: int, content_type: str) -> None:
    client = get_minio_client()
    client.put_object(
        settings.MINIO_BUCKET,
        object_key,
        data,
        size,
        content_type=content_type,
    )


def download_evidence(object_key: str) -> tuple[io.RawIOBase, int, str]:
    """Returns (stream, size, content_type)."""
    client = get_minio_client()
    response = client.get_object(settings.MINIO_BUCKET, object_key)
    size = int(response.headers.get("Content-Length", 0))
    content_type = response.headers.get("Content-Type", "application/octet-stream")
    return response, size, content_type
