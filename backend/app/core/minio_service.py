from __future__ import annotations

from datetime import timedelta
from io import BytesIO
from urllib.parse import urlsplit, urlunsplit

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
        public_path_prefix: str = "",
    ) -> None:
        self.bucket_name = bucket_name
        self.public_path_prefix = public_path_prefix.strip("/")

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

    def _apply_public_path_prefix(self, presigned_url: str) -> str:
        if not self.public_path_prefix:
            return presigned_url

        parsed = urlsplit(presigned_url)
        prefix = f"/{self.public_path_prefix}"
        if parsed.path == prefix or parsed.path.startswith(f"{prefix}/"):
            return presigned_url

        path = parsed.path if parsed.path.startswith("/") else f"/{parsed.path}"
        new_path = f"{prefix}{path}"
        return urlunsplit(
            (parsed.scheme, parsed.netloc, new_path, parsed.query, parsed.fragment)
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
            url = self.public_client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_key,
                expires=timedelta(minutes=expires_minutes),
            )
            return self._apply_public_path_prefix(url)
        except S3Error as exc:
            raise MinioStorageServiceError(str(exc)) from exc

    def download_bytes(self, object_key: str) -> bytes:
        self._ensure_bucket()
        response = None
        try:
            response = self.client.get_object(self.bucket_name, object_key)
            return response.read()
        except S3Error as exc:
            raise MinioStorageServiceError(str(exc)) from exc
        finally:
            if response is not None:
                response.close()
                response.release_conn()
