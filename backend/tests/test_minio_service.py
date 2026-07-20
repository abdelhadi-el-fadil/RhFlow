from datetime import timedelta

from app.core.minio_service import MinioStorageService


class _DummyPublicClient:
    def __init__(self, url: str) -> None:
        self._url = url
        self.last_call: dict[str, object] = {}

    def presigned_get_object(
        self,
        bucket_name: str,
        object_name: str,
        expires: timedelta,
    ) -> str:
        self.last_call = {
            "bucket_name": bucket_name,
            "object_name": object_name,
            "expires": expires,
        }
        return self._url


def _build_service(prefix: str) -> MinioStorageService:
    return MinioStorageService(
        endpoint="localhost:9000",
        access_key="test-key",
        secret_key="test-secret",
        bucket_name="rhflow",
        secure=False,
        public_endpoint="rhflow.app",
        public_secure=True,
        public_path_prefix=prefix,
    )


def test_get_presigned_get_url_applies_public_path_prefix() -> None:
    service = _build_service(prefix="storage")
    service._ensure_bucket = lambda: None  # type: ignore[method-assign]
    dummy = _DummyPublicClient(
        "https://rhflow.app/rhflow/signatures/user-1.jpg?X-Amz-Signature=abc",
    )
    service.public_client = dummy  # type: ignore[assignment]

    url = service.get_presigned_get_url("signatures/user-1.jpg", expires_minutes=15)

    assert url.startswith("https://rhflow.app/storage/rhflow/signatures/user-1.jpg?")
    assert dummy.last_call["bucket_name"] == "rhflow"
    assert dummy.last_call["object_name"] == "signatures/user-1.jpg"


def test_get_presigned_get_url_does_not_duplicate_existing_prefix() -> None:
    service = _build_service(prefix="storage")
    service._ensure_bucket = lambda: None  # type: ignore[method-assign]
    dummy = _DummyPublicClient(
        "https://rhflow.app/storage/rhflow/signatures/user-1.jpg?X-Amz-Signature=abc",
    )
    service.public_client = dummy  # type: ignore[assignment]

    url = service.get_presigned_get_url("signatures/user-1.jpg")

    assert url == "https://rhflow.app/storage/rhflow/signatures/user-1.jpg?X-Amz-Signature=abc"


def test_get_presigned_get_url_without_prefix_is_unchanged() -> None:
    service = _build_service(prefix="")
    service._ensure_bucket = lambda: None  # type: ignore[method-assign]
    dummy = _DummyPublicClient(
        "https://rhflow.app/rhflow/signatures/user-1.jpg?X-Amz-Signature=abc",
    )
    service.public_client = dummy  # type: ignore[assignment]

    url = service.get_presigned_get_url("signatures/user-1.jpg")

    assert url == "https://rhflow.app/rhflow/signatures/user-1.jpg?X-Amz-Signature=abc"
