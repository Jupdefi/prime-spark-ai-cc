"""
Tier 3: Cloud Storage
Long-term storage using MinIO (S3-compatible) and Supabase
"""
import json
from typing import Any, Optional
import boto3
from botocore.exceptions import ClientError
from config.settings import settings


class MinIOStorage:
    """MinIO S3-compatible cloud storage"""

    def __init__(self):
        self.endpoint = settings.memory.minio_endpoint
        self.access_key = settings.memory.minio_access_key
        self.secret_key = settings.memory.minio_secret_key
        self.bucket = settings.memory.minio_bucket
        self.client = None

    def _get_client(self):
        """Get or create MinIO client"""
        if not self.client:
            self.client = boto3.client(
                's3',
                endpoint_url=self.endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            )
            # Ensure bucket exists
            try:
                self.client.head_bucket(Bucket=self.bucket)
            except ClientError:
                # Bucket doesn't exist, create it
                self.client.create_bucket(Bucket=self.bucket)

        return self.client

    async def get(self, key: str) -> Optional[Any]:
        """Get object from MinIO"""
        try:
            client = self._get_client()
            response = client.get_object(Bucket=self.bucket, Key=key)
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            print(f"MinIO get error: {e}")
            return None
        except Exception as e:
            print(f"MinIO get error: {e}")
            return None

    async def set(self, key: str, value: Any) -> bool:
        """Set object in MinIO"""
        try:
            client = self._get_client()
            serialized = json.dumps(value, indent=2)
            client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=serialized.encode('utf-8'),
                ContentType='application/json'
            )
            return True
        except Exception as e:
            print(f"MinIO set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete object from MinIO"""
        try:
            client = self._get_client()
            client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except Exception as e:
            print(f"MinIO delete error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if object exists in MinIO"""
        try:
            client = self._get_client()
            client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False
        except Exception as e:
            print(f"MinIO exists error: {e}")
            return False

    async def list_keys(self, prefix: str = "") -> list[str]:
        """List all keys with optional prefix"""
        try:
            client = self._get_client()
            response = client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)

            keys = []
            if 'Contents' in response:
                keys = [obj['Key'] for obj in response['Contents']]

            return keys
        except Exception as e:
            print(f"MinIO list_keys error: {e}")
            return []

    async def get_stats(self) -> dict:
        """Get storage statistics"""
        try:
            client = self._get_client()
            response = client.list_objects_v2(Bucket=self.bucket)

            total_objects = 0
            total_size = 0

            if 'Contents' in response:
                total_objects = len(response['Contents'])
                total_size = sum(obj['Size'] for obj in response['Contents'])

            return {
                "total_objects": total_objects,
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "bucket": self.bucket,
                "endpoint": self.endpoint,
            }
        except Exception as e:
            print(f"MinIO stats error: {e}")
            return {"error": str(e)}

    async def upload_file(self, file_path: str, key: str) -> bool:
        """Upload a file to MinIO"""
        try:
            client = self._get_client()
            client.upload_file(file_path, self.bucket, key)
            return True
        except Exception as e:
            print(f"MinIO upload_file error: {e}")
            return False

    async def download_file(self, key: str, file_path: str) -> bool:
        """Download a file from MinIO"""
        try:
            client = self._get_client()
            client.download_file(self.bucket, key, file_path)
            return True
        except Exception as e:
            print(f"MinIO download_file error: {e}")
            return False


class CloudStorage:
    """Unified cloud storage (Tier 3)"""

    def __init__(self):
        self.minio = MinIOStorage()
        # Supabase integration can be added here when needed

    async def get(self, key: str) -> Optional[Any]:
        """Get from cloud storage"""
        return await self.minio.get(key)

    async def set(self, key: str, value: Any) -> bool:
        """Set in cloud storage"""
        return await self.minio.set(key, value)

    async def delete(self, key: str) -> bool:
        """Delete from cloud storage"""
        return await self.minio.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if exists in cloud storage"""
        return await self.minio.exists(key)

    async def list_keys(self, prefix: str = "") -> list[str]:
        """List keys in cloud storage"""
        return await self.minio.list_keys(prefix)

    async def get_stats(self) -> dict:
        """Get cloud storage statistics"""
        return await self.minio.get_stats()

    async def upload_file(self, file_path: str, key: str) -> bool:
        """Upload file to cloud"""
        return await self.minio.upload_file(file_path, key)

    async def download_file(self, key: str, file_path: str) -> bool:
        """Download file from cloud"""
        return await self.minio.download_file(key, file_path)


# Global cloud storage instance
cloud_storage = CloudStorage()
