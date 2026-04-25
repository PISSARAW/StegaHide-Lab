"""
StegaHide Lab – steganography toolkit for hiding and extracting messages in PNG images.

Modules:
    encoder    – LSB (Least Significant Bit) message embedding
    decoder    – LSB message extraction
    encryption – optional symmetric encryption / decryption of payloads
"""

from .encoder import encode_message
from .decoder import decode_message
from .encryption import encrypt_message, decrypt_message

__all__ = [
    "encode_message",
    "decode_message",
    "encrypt_message",
    "decrypt_message",
]
