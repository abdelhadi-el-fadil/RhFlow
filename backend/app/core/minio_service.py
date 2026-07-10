from __future__ import annotations

from datetime import timedelta
from io import BytesIO

from minio import Minio
from minio.error import S3Error


class MinioStorageServiceError(Exception):
    pass

class MinioStorageService:
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool,
        public_endpoint: str,
        public_secure: bool,
    ) -> None:
        self.bucket_name = bucket_name

        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region="us-east-1",
        )

        self.public_client = Minio(
            public_endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=public_secure,
            region="us-east-1",
        )

    def _ensure_bucket(self) -> None:
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as exc:
            raise MinioStorageServiceError(str(exc)) from exc

    def upload_bytes(self, object_key: str, payload: bytes, content_type: str) -> None:
        self._ensure_bucket()
        try:
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_key,
                data=BytesIO(payload),
                length=len(payload),
                content_type=content_type,
            )
        except S3Error as exc:
            raise MinioStorageServiceError(str(exc)) from exc

    def delete_object(self, object_key: str) -> None:
        self._ensure_bucket()
        try:
            self.client.remove_object(self.bucket_name, object_key)
        except S3Error as exc:
            raise MinioStorageServiceError(str(exc)) from exc

    def get_presigned_get_url(self, object_key: str, expires_minutes: int = 15) -> str:
        self._ensure_bucket()
        try:
            return self.public_client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_key,
                expires=timedelta(minutes=expires_minutes),
            )
        except S3Error as exc:
            raise MinioStorageServiceError(str(exc)) from exc