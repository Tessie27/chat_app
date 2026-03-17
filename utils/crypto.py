"""
Cryptographic utilities for secure chat
"""

import os
import base64
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization


class CryptoUtils:
    """Cryptographic helper functions"""

    @staticmethod
    def generate_key_pair():
        """Generate RSA key pair for asymmetric encryption"""
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        return private_key, public_key

    @staticmethod
    def serialize_public_key(public_key):
        """Convert public key to bytes for transmission"""
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    @staticmethod
    def deserialize_public_key(key_bytes):
        """Convert bytes back to public key object"""
        return serialization.load_pem_public_key(key_bytes)

    @staticmethod
    def encrypt_asymmetric(message, public_key):
        """Encrypt message with public key"""
        if isinstance(message, str):
            message = message.encode()
        return public_key.encrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    @staticmethod
    def decrypt_asymmetric(encrypted_message, private_key):
        """Decrypt message with private key"""
        return private_key.decrypt(
            encrypted_message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    @staticmethod
    def generate_salt():
        """Generate random salt for key derivation"""
        return os.urandom(16)

    @staticmethod
    def hash_password(password, salt=None):
        """Hash password with salt using PBKDF2"""
        if not salt:
            salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt

    @staticmethod
    def verify_password(password, salt, expected_key):
        """Verify password against stored hash"""
        key, _ = CryptoUtils.hash_password(password, salt)
        return key == expected_key

    @staticmethod
    def generate_token():
        """Generate secure random token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def encrypt_file(file_path, password):
        """Encrypt a file with password"""
        key, salt = CryptoUtils.hash_password(password)
        fernet = Fernet(key)

        with open(file_path, "rb") as f:
            data = f.read()

        encrypted = fernet.encrypt(data)

        # Save salt with encrypted data
        with open(file_path + ".enc", "wb") as f:
            f.write(salt + encrypted)

        return file_path + ".enc"

    @staticmethod
    def decrypt_file(encrypted_path, password):
        """Decrypt a file with password"""
        with open(encrypted_path, "rb") as f:
            salt = f.read(16)
            encrypted_data = f.read()

        key, _ = CryptoUtils.hash_password(password, salt)
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_data)

        output_path = encrypted_path.replace(".enc", "")
        with open(output_path, "wb") as f:
            f.write(decrypted)

        return output_path


class MessageEncryptor:
    """Handle message encryption for chat"""

    def __init__(self, password=None):
        self.password = password
        self.session_keys = {}  # user -> session key
        self.fernet = None
        if password:
            self.setup_encryption(password)

    def setup_encryption(self, password):
        """Initialize encryption with password"""
        self.salt = CryptoUtils.generate_salt()
        key, _ = CryptoUtils.hash_password(password, self.salt)
        self.fernet = Fernet(key)

    def encrypt_message(self, message, recipient=None):
        """Encrypt a message (optionally for specific recipient)"""
        if not self.fernet:
            return message

        if recipient and recipient in self.session_keys:
            # Use session key for recipient
            fernet = Fernet(self.session_keys[recipient])
            return fernet.encrypt(message.encode()).decode()
        else:
            # Use global encryption
            return self.fernet.encrypt(message.encode()).decode()

    def decrypt_message(self, encrypted_message, sender=None):
        """Decrypt a message"""
        if not self.fernet:
            return encrypted_message

        try:
            if sender and sender in self.session_keys:
                fernet = Fernet(self.session_keys[sender])
                return fernet.decrypt(encrypted_message.encode()).decode()
            else:
                return self.fernet.decrypt(encrypted_message.encode()).decode()
        except Exception:
            return "[Encrypted message - cannot decrypt]"

    def establish_session_key(self, user, public_key):
        """Establish a session key with another user"""
        # Generate random session key
        session_key = Fernet.generate_key()

        # Encrypt with user's public key
        encrypted_key = CryptoUtils.encrypt_asymmetric(session_key, public_key)

        # Store session key
        self.session_keys[user] = session_key

        return encrypted_key
