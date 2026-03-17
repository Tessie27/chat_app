"""
Secure chat protocol with encryption
"""

import json
import hashlib
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import socket
from datetime import datetime


def ts():
    return datetime.now().strftime("%H:%M:%S")


class SecureProtocol:
    """Handles encrypted message exchange"""

    def __init__(self, password=None):
        self.key = None
        self.cipher = None
        if password:
            self.derive_key(password)

    def derive_key(self, password, salt=None):
        """Derive encryption key from password"""
        if not salt:
            salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.cipher = Fernet(key)
        return salt

    def encrypt_packet(self, data):
        """Encrypt packet data"""
        if not hasattr(self, "cipher") or self.cipher is None:
            return data  # No encryption
        json_str = json.dumps(data)
        encrypted = self.cipher.encrypt(json_str.encode())
        return {"type": "encrypted", "data": base64.b64encode(encrypted).decode()}

    def decrypt_packet(self, packet):
        """Decrypt packet if encrypted"""
        if (
            packet.get("type") == "encrypted"
            and hasattr(self, "cipher")
            and self.cipher
        ):
            encrypted = base64.b64decode(packet["data"])
            decrypted = self.cipher.decrypt(encrypted)
            return json.loads(decrypted.decode())
        return packet


# Enhanced send/recv with encryption
def send(sock, data, crypto=None):
    """Send data with optional encryption"""
    if crypto:
        data = crypto.encrypt_packet(data)
    raw = json.dumps(data).encode()
    length = len(raw).to_bytes(4, "big")
    sock.sendall(length + raw)


def recv(sock, crypto=None):
    """Receive data with optional decryption"""
    raw_len = _recv_exact(sock, 4)
    if not raw_len:
        return None
    length = int.from_bytes(raw_len, "big")
    raw = _recv_exact(sock, length)
    if not raw:
        return None
    data = json.loads(raw.decode())
    if crypto:
        data = crypto.decrypt_packet(data)
    return data


def _recv_exact(sock, n):
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data
