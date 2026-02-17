"""S3/MinIO object storage wrapper for menu photos."""

import logging
import uuid
from io import BytesIO

import boto3
from botocore.exceptions import ClientError

from app.config import get_settings

logger = logging.getLogger(__name__)


class StorageService:
    """Thin wrapper around S3/MinIO for menu photo storage."""

    def __init__(self):
        settings = get_settings()
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
        )
        self.bucket_raw = settings.s3_bucket_raw_photos
        self.bucket_processed = settings.s3_bucket_processed_photos
        self.bucket_uploads = settings.s3_bucket_user_uploads

    def ensure_buckets(self) -> None:
        """Create buckets if they don't exist."""
        for bucket in [self.bucket_raw, self.bucket_processed, self.bucket_uploads]:
            try:
                self._client.head_bucket(Bucket=bucket)
            except ClientError:
                try:
                    self._client.create_bucket(Bucket=bucket)
                    logger.info("Created bucket: %s", bucket)
                except ClientError as e:
                    logger.warning("Could not create bucket %s: %s", bucket, e)

    def upload_photo(
        self,
        photo_bytes: bytes,
        bucket: str,
        key: str | None = None,
        content_type: str = "image/jpeg",
    ) -> str:
        """Upload a photo and return its S3 key."""
        if key is None:
            key = f"{uuid.uuid4()}.jpg"

        self._client.upload_fileobj(
            BytesIO(photo_bytes),
            bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )
        return key

    def get_photo_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        """Generate a presigned URL for a stored photo."""
        try:
            url = self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            logger.error("Failed to generate presigned URL: %s", e)
            return ""

    def download_photo(self, bucket: str, key: str) -> bytes:
        """Download photo bytes from S3."""
        try:
            response = self._client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()
        except ClientError as e:
            logger.error("Failed to download photo %s/%s: %s", bucket, key, e)
            return b""

    def delete_photo(self, bucket: str, key: str) -> bool:
        """Delete a photo from S3."""
        try:
            self._client.delete_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            logger.error("Failed to delete photo %s/%s: %s", bucket, key, e)
            return False
