"""
End-to-End Encryption Manager

Provides comprehensive encryption services for data at rest and in transit,
key management, and cryptographic operations.
"""

import logging
import hashlib
import hmac
import base64
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import json

logger = logging.getLogger(__name__)


class EncryptionAlgorithm(Enum):
    """Supported encryption algorithms"""
    AES_256_GCM = "aes-256-gcm"
    AES_256_CBC = "aes-256-cbc"
    CHACHA20_POLY1305 = "chacha20-poly1305"
    RSA_2048 = "rsa-2048"
    RSA_4096 = "rsa-4096"


class KeyType(Enum):
    """Encryption key types"""
    SYMMETRIC = "symmetric"
    ASYMMETRIC_PUBLIC = "asymmetric_public"
    ASYMMETRIC_PRIVATE = "asymmetric_private"
    SIGNING = "signing"


@dataclass
class EncryptionKey:
    """Encryption key metadata"""
    key_id: str
    key_type: KeyType
    algorithm: EncryptionAlgorithm
    created_at: datetime
    expires_at: Optional[datetime]
    rotation_period_days: int
    usage_count: int = 0
    last_used: Optional[datetime] = None
    enabled: bool = True


@dataclass
class EncryptedData:
    """Encrypted data container"""
    ciphertext: bytes
    algorithm: EncryptionAlgorithm
    key_id: str
    iv: Optional[bytes]  # Initialization vector
    auth_tag: Optional[bytes]  # Authentication tag for AEAD
    metadata: Dict


class EncryptionManager:
    """
    End-to-End Encryption Manager

    Features:
    - Multiple encryption algorithms
    - Automatic key rotation
    - Key versioning
    - Envelope encryption
    - Authenticated encryption (AEAD)
    - Data integrity verification
    - Secure key storage
    - Audit logging
    """

    def __init__(
        self,
        default_algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM,
        key_rotation_days: int = 90,
        enable_envelope_encryption: bool = True,
    ):
        self.default_algorithm = default_algorithm
        self.key_rotation_days = key_rotation_days
        self.enable_envelope_encryption = enable_envelope_encryption

        # Key storage (in production, use HSM or KMS)
        self.keys: Dict[str, EncryptionKey] = {}
        self.key_material: Dict[str, bytes] = {}  # Encrypted key material

        # Master key for envelope encryption
        self.master_key_id = self._generate_master_key()

        # Encryption operations log
        self.operations_log: List[Dict] = []

        logger.info(f"Initialized EncryptionManager (algorithm: {default_algorithm.value})")

    def _generate_master_key(self) -> str:
        """Generate master encryption key"""
        key_id = f"master-{secrets.token_hex(16)}"

        # Generate 256-bit key
        key_material = secrets.token_bytes(32)

        metadata = EncryptionKey(
            key_id=key_id,
            key_type=KeyType.SYMMETRIC,
            algorithm=EncryptionAlgorithm.AES_256_GCM,
            created_at=datetime.now(),
            expires_at=None,  # Master key doesn't expire
            rotation_period_days=365,
        )

        self.keys[key_id] = metadata
        self.key_material[key_id] = key_material

        logger.info(f"Generated master key: {key_id}")
        return key_id

    def generate_data_key(
        self,
        algorithm: Optional[EncryptionAlgorithm] = None,
        rotation_days: Optional[int] = None,
    ) -> str:
        """
        Generate a new data encryption key

        Args:
            algorithm: Encryption algorithm to use
            rotation_days: Days until automatic rotation

        Returns:
            Key ID
        """
        algorithm = algorithm or self.default_algorithm
        rotation_days = rotation_days or self.key_rotation_days

        key_id = f"dek-{secrets.token_hex(16)}"

        # Generate key material based on algorithm
        if algorithm in [EncryptionAlgorithm.AES_256_GCM, EncryptionAlgorithm.AES_256_CBC]:
            key_material = secrets.token_bytes(32)  # 256 bits
        elif algorithm == EncryptionAlgorithm.CHACHA20_POLY1305:
            key_material = secrets.token_bytes(32)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        # Envelope encryption: encrypt data key with master key
        if self.enable_envelope_encryption:
            encrypted_key_material = self._encrypt_with_master_key(key_material)
        else:
            encrypted_key_material = key_material

        # Store key metadata
        metadata = EncryptionKey(
            key_id=key_id,
            key_type=KeyType.SYMMETRIC,
            algorithm=algorithm,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=rotation_days),
            rotation_period_days=rotation_days,
        )

        self.keys[key_id] = metadata
        self.key_material[key_id] = encrypted_key_material

        logger.info(f"Generated data key: {key_id} (algorithm: {algorithm.value})")
        return key_id

    def encrypt(
        self,
        plaintext: bytes,
        key_id: Optional[str] = None,
        additional_data: Optional[bytes] = None,
    ) -> EncryptedData:
        """
        Encrypt data

        Args:
            plaintext: Data to encrypt
            key_id: Key to use (generates new if None)
            additional_data: Additional authenticated data (AAD)

        Returns:
            EncryptedData object
        """
        # Generate key if not provided
        if key_id is None:
            key_id = self.generate_data_key()

        if key_id not in self.keys:
            raise ValueError(f"Key not found: {key_id}")

        key_metadata = self.keys[key_id]

        # Check if key is enabled and not expired
        if not key_metadata.enabled:
            raise ValueError(f"Key is disabled: {key_id}")

        if key_metadata.expires_at and datetime.now() > key_metadata.expires_at:
            logger.warning(f"Key expired: {key_id}, rotating...")
            key_id = self._rotate_key(key_id)
            key_metadata = self.keys[key_id]

        # Get decrypted key material
        key_material = self._get_key_material(key_id)

        # Encrypt based on algorithm
        algorithm = key_metadata.algorithm

        if algorithm == EncryptionAlgorithm.AES_256_GCM:
            ciphertext, iv, auth_tag = self._encrypt_aes_gcm(
                plaintext, key_material, additional_data
            )
        elif algorithm == EncryptionAlgorithm.AES_256_CBC:
            ciphertext, iv = self._encrypt_aes_cbc(plaintext, key_material)
            auth_tag = None
        elif algorithm == EncryptionAlgorithm.CHACHA20_POLY1305:
            ciphertext, iv, auth_tag = self._encrypt_chacha20(
                plaintext, key_material, additional_data
            )
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        # Update key usage
        key_metadata.usage_count += 1
        key_metadata.last_used = datetime.now()

        # Log operation
        self._log_operation('encrypt', key_id, len(plaintext), len(ciphertext))

        return EncryptedData(
            ciphertext=ciphertext,
            algorithm=algorithm,
            key_id=key_id,
            iv=iv,
            auth_tag=auth_tag,
            metadata={'encrypted_at': datetime.now().isoformat()},
        )

    def decrypt(
        self,
        encrypted_data: EncryptedData,
        additional_data: Optional[bytes] = None,
    ) -> bytes:
        """
        Decrypt data

        Args:
            encrypted_data: EncryptedData object
            additional_data: Additional authenticated data (must match encryption)

        Returns:
            Decrypted plaintext
        """
        key_id = encrypted_data.key_id

        if key_id not in self.keys:
            raise ValueError(f"Key not found: {key_id}")

        key_metadata = self.keys[key_id]
        key_material = self._get_key_material(key_id)

        algorithm = encrypted_data.algorithm

        try:
            if algorithm == EncryptionAlgorithm.AES_256_GCM:
                plaintext = self._decrypt_aes_gcm(
                    encrypted_data.ciphertext,
                    key_material,
                    encrypted_data.iv,
                    encrypted_data.auth_tag,
                    additional_data,
                )
            elif algorithm == EncryptionAlgorithm.AES_256_CBC:
                plaintext = self._decrypt_aes_cbc(
                    encrypted_data.ciphertext,
                    key_material,
                    encrypted_data.iv,
                )
            elif algorithm == EncryptionAlgorithm.CHACHA20_POLY1305:
                plaintext = self._decrypt_chacha20(
                    encrypted_data.ciphertext,
                    key_material,
                    encrypted_data.iv,
                    encrypted_data.auth_tag,
                    additional_data,
                )
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")

            # Log operation
            self._log_operation('decrypt', key_id, len(encrypted_data.ciphertext), len(plaintext))

            return plaintext

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def _encrypt_aes_gcm(
        self,
        plaintext: bytes,
        key: bytes,
        aad: Optional[bytes],
    ) -> Tuple[bytes, bytes, bytes]:
        """Encrypt using AES-256-GCM (authenticated encryption)"""
        # In production, use cryptography library
        # This is a simplified simulation
        iv = secrets.token_bytes(12)  # 96-bit nonce for GCM

        # Simulate encryption (in reality, use cryptography.hazmat)
        ciphertext = self._xor_encrypt(plaintext, key, iv)

        # Simulate authentication tag
        auth_tag = self._compute_auth_tag(ciphertext, key, iv, aad)

        return ciphertext, iv, auth_tag

    def _decrypt_aes_gcm(
        self,
        ciphertext: bytes,
        key: bytes,
        iv: bytes,
        auth_tag: bytes,
        aad: Optional[bytes],
    ) -> bytes:
        """Decrypt using AES-256-GCM"""
        # Verify authentication tag
        expected_tag = self._compute_auth_tag(ciphertext, key, iv, aad)
        if not hmac.compare_digest(auth_tag, expected_tag):
            raise ValueError("Authentication tag verification failed")

        # Decrypt
        plaintext = self._xor_encrypt(ciphertext, key, iv)
        return plaintext

    def _encrypt_aes_cbc(
        self,
        plaintext: bytes,
        key: bytes,
    ) -> Tuple[bytes, bytes]:
        """Encrypt using AES-256-CBC"""
        iv = secrets.token_bytes(16)  # 128-bit IV for CBC

        # Add PKCS7 padding
        padded = self._pkcs7_pad(plaintext, 16)

        # Simulate encryption
        ciphertext = self._xor_encrypt(padded, key, iv)

        return ciphertext, iv

    def _decrypt_aes_cbc(
        self,
        ciphertext: bytes,
        key: bytes,
        iv: bytes,
    ) -> bytes:
        """Decrypt using AES-256-CBC"""
        # Decrypt
        padded = self._xor_encrypt(ciphertext, key, iv)

        # Remove padding
        plaintext = self._pkcs7_unpad(padded)

        return plaintext

    def _encrypt_chacha20(
        self,
        plaintext: bytes,
        key: bytes,
        aad: Optional[bytes],
    ) -> Tuple[bytes, bytes, bytes]:
        """Encrypt using ChaCha20-Poly1305"""
        nonce = secrets.token_bytes(12)

        # Simulate encryption
        ciphertext = self._xor_encrypt(plaintext, key, nonce)

        # Compute Poly1305 tag
        auth_tag = self._compute_auth_tag(ciphertext, key, nonce, aad)

        return ciphertext, nonce, auth_tag

    def _decrypt_chacha20(
        self,
        ciphertext: bytes,
        key: bytes,
        nonce: bytes,
        auth_tag: bytes,
        aad: Optional[bytes],
    ) -> bytes:
        """Decrypt using ChaCha20-Poly1305"""
        # Verify tag
        expected_tag = self._compute_auth_tag(ciphertext, key, nonce, aad)
        if not hmac.compare_digest(auth_tag, expected_tag):
            raise ValueError("Authentication tag verification failed")

        # Decrypt
        plaintext = self._xor_encrypt(ciphertext, key, nonce)
        return plaintext

    def _xor_encrypt(self, data: bytes, key: bytes, iv: bytes) -> bytes:
        """Simple XOR encryption (placeholder for real crypto)"""
        # In production, use proper AES/ChaCha20 from cryptography library
        # This is just a simulation for demonstration
        key_stream = hashlib.sha256(key + iv).digest()
        while len(key_stream) < len(data):
            key_stream += hashlib.sha256(key_stream).digest()

        return bytes(a ^ b for a, b in zip(data, key_stream[:len(data)]))

    def _compute_auth_tag(
        self,
        ciphertext: bytes,
        key: bytes,
        iv: bytes,
        aad: Optional[bytes],
    ) -> bytes:
        """Compute authentication tag"""
        h = hmac.new(key, digestmod=hashlib.sha256)
        h.update(iv)
        h.update(ciphertext)
        if aad:
            h.update(aad)
        return h.digest()[:16]  # 128-bit tag

    def _pkcs7_pad(self, data: bytes, block_size: int) -> bytes:
        """Add PKCS7 padding"""
        padding_length = block_size - (len(data) % block_size)
        padding = bytes([padding_length] * padding_length)
        return data + padding

    def _pkcs7_unpad(self, data: bytes) -> bytes:
        """Remove PKCS7 padding"""
        padding_length = data[-1]
        return data[:-padding_length]

    def _encrypt_with_master_key(self, data: bytes) -> bytes:
        """Encrypt data with master key (envelope encryption)"""
        master_key = self.key_material[self.master_key_id]
        iv = secrets.token_bytes(12)
        encrypted = self._xor_encrypt(data, master_key, iv)
        return iv + encrypted

    def _decrypt_with_master_key(self, encrypted_data: bytes) -> bytes:
        """Decrypt data with master key"""
        master_key = self.key_material[self.master_key_id]
        iv = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        return self._xor_encrypt(ciphertext, master_key, iv)

    def _get_key_material(self, key_id: str) -> bytes:
        """Get decrypted key material"""
        encrypted_material = self.key_material[key_id]

        if self.enable_envelope_encryption and key_id != self.master_key_id:
            return self._decrypt_with_master_key(encrypted_material)
        else:
            return encrypted_material

    def _rotate_key(self, old_key_id: str) -> str:
        """Rotate encryption key"""
        old_metadata = self.keys[old_key_id]

        # Generate new key with same algorithm
        new_key_id = self.generate_data_key(
            algorithm=old_metadata.algorithm,
            rotation_days=old_metadata.rotation_period_days,
        )

        # Disable old key
        old_metadata.enabled = False

        logger.info(f"Rotated key {old_key_id} to {new_key_id}")
        return new_key_id

    def rotate_all_keys(self) -> int:
        """Rotate all expired or near-expiration keys"""
        rotated_count = 0
        threshold = datetime.now() + timedelta(days=7)  # Rotate keys expiring within 7 days

        for key_id, metadata in list(self.keys.items()):
            if metadata.expires_at and metadata.expires_at < threshold and metadata.enabled:
                self._rotate_key(key_id)
                rotated_count += 1

        logger.info(f"Rotated {rotated_count} keys")
        return rotated_count

    def _log_operation(self, operation: str, key_id: str, input_size: int, output_size: int) -> None:
        """Log encryption operation"""
        self.operations_log.append({
            'timestamp': datetime.now(),
            'operation': operation,
            'key_id': key_id,
            'input_size': input_size,
            'output_size': output_size,
        })

    def get_key_statistics(self) -> Dict:
        """Get key usage statistics"""
        active_keys = sum(1 for k in self.keys.values() if k.enabled)
        total_usage = sum(k.usage_count for k in self.keys.values())

        # Keys by algorithm
        algorithm_counts = {}
        for key in self.keys.values():
            algo = key.algorithm.value
            algorithm_counts[algo] = algorithm_counts.get(algo, 0) + 1

        # Recent operations
        recent_window = datetime.now() - timedelta(hours=1)
        recent_ops = [op for op in self.operations_log if op['timestamp'] > recent_window]

        return {
            'total_keys': len(self.keys),
            'active_keys': active_keys,
            'total_usage_count': total_usage,
            'keys_by_algorithm': algorithm_counts,
            'recent_operations': len(recent_ops),
            'recent_encryptions': sum(1 for op in recent_ops if op['operation'] == 'encrypt'),
            'recent_decryptions': sum(1 for op in recent_ops if op['operation'] == 'decrypt'),
        }
