import boto3
import structlog
from botocore.exceptions import NoCredentialsError, ClientError
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import os

from ..config import settings

logger = structlog.get_logger()


class S3Service:
    """
    Service for managing S3 operations with signed URLs.

    Critères PRD F5-01, F5-04: Génération d'URLs signées S3 avec expiration appropriée
    """

    def __init__(self):
        self.bucket_name = settings.S3_BUCKET_NAME
        self.region = settings.AWS_REGION

        # Initialize S3 client
        if self._is_mock_mode():
            self.s3_client = None
            logger.info("S3 Service initialized in mock mode")
        else:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=self.region
                )
                logger.info("S3 Service initialized", bucket=self.bucket_name, region=self.region)
            except Exception as e:
                logger.error("Failed to initialize S3 client", error=str(e))
                self.s3_client = None

    def _is_mock_mode(self) -> bool:
        """Check if running in mock mode for development"""
        return settings.MOCK_MODE or os.getenv("MOCK_MODE", "false").lower() == "true"

    def generate_signed_url(
        self,
        s3_key: str,
        expiration: int = 3600,
        method: str = 'GET'
    ) -> Optional[str]:
        """
        Generate a signed URL for S3 object access.

        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
            method: HTTP method ('GET' for download, 'PUT' for upload)

        Returns:
            Signed URL string or None if failed
        """
        if self._is_mock_mode():
            return self._mock_signed_url(s3_key, expiration)

        if not self.s3_client:
            logger.error("S3 client not initialized")
            return None

        try:
            if method == 'GET':
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': s3_key},
                    ExpiresIn=expiration
                )
            elif method == 'PUT':
                url = self.s3_client.generate_presigned_url(
                    'put_object',
                    Params={'Bucket': self.bucket_name, 'Key': s3_key},
                    ExpiresIn=expiration
                )
            else:
                raise ValueError(f"Unsupported method: {method}")

            logger.info(
                "Generated signed URL",
                s3_key=s3_key,
                method=method,
                expiration=expiration
            )
            return url

        except Exception as e:
            logger.error("Failed to generate signed URL", error=str(e), s3_key=s3_key)
            return None

    def generate_download_url(
        self,
        s3_key: str,
        filename: Optional[str] = None,
        expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate a signed download URL with custom filename.

        Args:
            s3_key: S3 object key
            filename: Custom filename for download
            expiration: URL expiration time in seconds

        Returns:
            Signed download URL or None if failed
        """
        if self._is_mock_mode():
            return self._mock_download_url(s3_key, filename, expiration)

        if not self.s3_client:
            logger.error("S3 client not initialized")
            return None

        try:
            params = {'Bucket': self.bucket_name, 'Key': s3_key}

            if filename:
                params['ResponseContentDisposition'] = f'attachment; filename="{filename}"'

            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expiration
            )

            logger.info(
                "Generated download URL",
                s3_key=s3_key,
                filename=filename,
                expiration=expiration
            )
            return url

        except Exception as e:
            logger.error("Failed to generate download URL", error=str(e), s3_key=s3_key)
            return None

    def get_object_info(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an S3 object.

        Args:
            s3_key: S3 object key

        Returns:
            Object metadata or None if failed
        """
        if self._is_mock_mode():
            return self._mock_object_info(s3_key)

        if not self.s3_client:
            return None

        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )

            return {
                'size': response.get('ContentLength', 0),
                'last_modified': response.get('LastModified'),
                'content_type': response.get('ContentType'),
                'etag': response.get('ETag', '').strip('"'),
                'exists': True
            }

        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning("S3 object not found", s3_key=s3_key)
                return {'exists': False}
            else:
                logger.error("Failed to get object info", error=str(e), s3_key=s3_key)
                return None

    def delete_object(self, s3_key: str) -> bool:
        """
        Delete an S3 object.

        Args:
            s3_key: S3 object key

        Returns:
            True if deleted successfully, False otherwise
        """
        if self._is_mock_mode():
            return self._mock_delete_object(s3_key)

        if not self.s3_client:
            return False

        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )

            logger.info("Deleted S3 object", s3_key=s3_key)
            return True

        except Exception as e:
            logger.error("Failed to delete S3 object", error=str(e), s3_key=s3_key)
            return False

    def copy_object(self, source_key: str, dest_key: str) -> bool:
        """
        Copy an S3 object.

        Args:
            source_key: Source S3 object key
            dest_key: Destination S3 object key

        Returns:
            True if copied successfully, False otherwise
        """
        if self._is_mock_mode():
            return self._mock_copy_object(source_key, dest_key)

        if not self.s3_client:
            return False

        try:
            copy_source = {
                'Bucket': self.bucket_name,
                'Key': source_key
            }

            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=dest_key
            )

            logger.info("Copied S3 object", source=source_key, dest=dest_key)
            return True

        except Exception as e:
            logger.error("Failed to copy S3 object", error=str(e), source=source_key, dest=dest_key)
            return False

    def generate_upload_url(
        self,
        s3_key: str,
        content_type: str = "video/mp4",
        expiration: int = 3600
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a presigned URL for uploading.

        Args:
            s3_key: S3 object key for upload
            content_type: Content type of the file
            expiration: URL expiration time in seconds

        Returns:
            Dictionary with upload URL and fields or None if failed
        """
        if self._is_mock_mode():
            return self._mock_upload_url(s3_key, content_type, expiration)

        if not self.s3_client:
            return None

        try:
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=s3_key,
                Fields={'Content-Type': content_type},
                Conditions=[
                    {'Content-Type': content_type},
                    ['content-length-range', 1, 1000 * 1024 * 1024]  # 1GB max
                ],
                ExpiresIn=expiration
            )

            logger.info("Generated upload URL", s3_key=s3_key, content_type=content_type)
            return response

        except Exception as e:
            logger.error("Failed to generate upload URL", error=str(e), s3_key=s3_key)
            return None

    def get_public_url(self, s3_key: str) -> str:
        """
        Get public URL for an S3 object (for objects with public read access).

        Args:
            s3_key: S3 object key

        Returns:
            Public URL string
        """
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"

    def _mock_signed_url(self, s3_key: str, expiration: int) -> str:
        """Mock signed URL for development"""
        base_url = f"https://mock-s3.example.com/{self.bucket_name}/{s3_key}"
        expires_at = datetime.utcnow() + timedelta(seconds=expiration)
        return f"{base_url}?expires={int(expires_at.timestamp())}"

    def _mock_download_url(self, s3_key: str, filename: Optional[str], expiration: int) -> str:
        """Mock download URL for development"""
        base_url = self._mock_signed_url(s3_key, expiration)
        if filename:
            return f"{base_url}&filename={filename}"
        return base_url

    def _mock_object_info(self, s3_key: str) -> Dict[str, Any]:
        """Mock object info for development"""
        return {
            'size': 1024 * 1024,  # 1MB mock size
            'last_modified': datetime.utcnow(),
            'content_type': 'video/mp4',
            'etag': 'mock-etag-123',
            'exists': True
        }

    def _mock_delete_object(self, s3_key: str) -> bool:
        """Mock object deletion for development"""
        logger.info("Mock deleting S3 object", s3_key=s3_key)
        return True

    def _mock_copy_object(self, source_key: str, dest_key: str) -> bool:
        """Mock object copy for development"""
        logger.info("Mock copying S3 object", source=source_key, dest=dest_key)
        return True

    def _mock_upload_url(self, s3_key: str, content_type: str, expiration: int) -> Dict[str, Any]:
        """Mock upload URL for development"""
        return {
            'url': f"https://mock-s3.example.com/{self.bucket_name}",
            'fields': {
                'key': s3_key,
                'Content-Type': content_type,
                'policy': 'mock-policy',
                'signature': 'mock-signature'
            }
        }


# Global S3 service instance
s3_service = S3Service()


def get_s3_service() -> S3Service:
    """Get the global S3 service instance"""
    return s3_service