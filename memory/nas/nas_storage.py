"""
Tier 2: NAS Persistent Storage
Shared storage across edge devices via Argon EON NAS
"""
import json
import aiofiles
from pathlib import Path
from typing import Any, Optional
from config.settings import settings


class NASStorage:
    """NAS-based persistent storage (Tier 2)"""

    def __init__(self):
        self.base_path = Path(settings.memory.nas_share_path)
        self.cache_dir = self.base_path / "prime-spark-cache"
        self.models_dir = self.base_path / "models"
        self.data_dir = self.base_path / "data"

    def _ensure_dirs(self):
        """Ensure required directories exist"""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.models_dir.mkdir(parents=True, exist_ok=True)
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"NAS directory creation error: {e}")

    def _get_path(self, key: str, storage_type: str = "cache") -> Path:
        """Get file path for a key"""
        base = {
            "cache": self.cache_dir,
            "models": self.models_dir,
            "data": self.data_dir
        }.get(storage_type, self.cache_dir)

        # Create subdirectories based on key hash for better distribution
        key_hash = hash(key) % 256
        subdir = base / f"{key_hash:02x}"
        subdir.mkdir(parents=True, exist_ok=True)

        return subdir / f"{key}.json"

    async def get(self, key: str, storage_type: str = "cache") -> Optional[Any]:
        """Get value from NAS"""
        try:
            file_path = self._get_path(key, storage_type)
            if not file_path.exists():
                return None

            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            print(f"NAS get error for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, storage_type: str = "cache") -> bool:
        """Set value in NAS"""
        try:
            self._ensure_dirs()
            file_path = self._get_path(key, storage_type)

            async with aiofiles.open(file_path, 'w') as f:
                await f.write(json.dumps(value, indent=2))
            return True
        except Exception as e:
            print(f"NAS set error for {key}: {e}")
            return False

    async def delete(self, key: str, storage_type: str = "cache") -> bool:
        """Delete value from NAS"""
        try:
            file_path = self._get_path(key, storage_type)
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            print(f"NAS delete error for {key}: {e}")
            return False

    async def exists(self, key: str, storage_type: str = "cache") -> bool:
        """Check if key exists in NAS"""
        try:
            file_path = self._get_path(key, storage_type)
            return file_path.exists()
        except Exception as e:
            print(f"NAS exists error for {key}: {e}")
            return False

    async def list_keys(self, storage_type: str = "cache") -> list[str]:
        """List all keys in a storage type"""
        try:
            base = {
                "cache": self.cache_dir,
                "models": self.models_dir,
                "data": self.data_dir
            }.get(storage_type, self.cache_dir)

            keys = []
            for json_file in base.rglob("*.json"):
                # Extract key from filename
                key = json_file.stem
                keys.append(key)
            return keys
        except Exception as e:
            print(f"NAS list_keys error: {e}")
            return []

    async def get_stats(self) -> dict:
        """Get NAS storage statistics"""
        try:
            total_files = 0
            total_size = 0

            for storage_type in ["cache", "models", "data"]:
                base = {
                    "cache": self.cache_dir,
                    "models": self.models_dir,
                    "data": self.data_dir
                }.get(storage_type, self.cache_dir)

                for file in base.rglob("*.json"):
                    total_files += 1
                    total_size += file.stat().st_size

            return {
                "total_files": total_files,
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "is_mounted": self.base_path.exists(),
                "cache_files": len(await self.list_keys("cache")),
                "model_files": len(await self.list_keys("models")),
                "data_files": len(await self.list_keys("data")),
            }
        except Exception as e:
            print(f"NAS stats error: {e}")
            return {"error": str(e)}

    async def save_model(self, model_name: str, model_data: bytes) -> bool:
        """Save a model file to NAS"""
        try:
            self._ensure_dirs()
            model_path = self.models_dir / model_name

            async with aiofiles.open(model_path, 'wb') as f:
                await f.write(model_data)
            return True
        except Exception as e:
            print(f"NAS save_model error: {e}")
            return False

    async def load_model(self, model_name: str) -> Optional[bytes]:
        """Load a model file from NAS"""
        try:
            model_path = self.models_dir / model_name
            if not model_path.exists():
                return None

            async with aiofiles.open(model_path, 'rb') as f:
                return await f.read()
        except Exception as e:
            print(f"NAS load_model error: {e}")
            return None


# Global NAS storage instance
nas_storage = NASStorage()
