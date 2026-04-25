"""
decoder.py – LSB steganography decoder.

Extracts a secret message that was previously embedded by the encoder module.
The 32-bit length prefix written by the encoder is read first, followed by the
exact number of payload bits.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

_DELIMITER = "<<END>>"


def _bits_to_text(bits: list[int]) -> str:
    """Convert a flat list of bits (MSB-first) back to a UTF-8 string.

    Raises
    ------
    ValueError
        If the bit sequence length is not a multiple of 8, or the bytes cannot
        be decoded as UTF-8.
    """
    if len(bits) % 8 != 0:
        raise ValueError(
            f"Bit sequence length ({len(bits)}) is not a multiple of 8."
        )
    byte_values: list[int] = []
    for i in range(0, len(bits), 8):
        byte = 0
        for bit in bits[i : i + 8]:
            byte = (byte << 1) | bit
        byte_values.append(byte)
    try:
        return bytes(byte_values).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"Extracted bytes are not valid UTF-8: {exc}") from exc


def _bits_to_int(bits: list[int]) -> int:
    """Interpret *bits* (MSB-first) as an unsigned integer."""
    value = 0
    for bit in bits:
        value = (value << 1) | bit
    return value


def decode_message(image_path: str | Path) -> str:
    """Extract and return the hidden message from *image_path*.

    Parameters
    ----------
    image_path:
        Path to the stego PNG image produced by :func:`steganography.encoder.encode_message`.

    Returns
    -------
    str
        The hidden message (without the internal delimiter).

    Raises
    ------
    FileNotFoundError
        If *image_path* does not exist.
    ValueError
        If no valid hidden message can be found (wrong file, or the image was
        not encoded with this tool).
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: '{image_path}'")

    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    pixel_access = img.load()
    if pixel_access is None:
        raise ValueError(f"Failed to load pixel data from '{image_path}'.")

    # Flatten all LSBs from the image.
    lsbs: list[int] = []
    for y in range(height):
        for x in range(width):
            for channel in pixel_access[x, y]:
                lsbs.append(channel & 1)

    if len(lsbs) < 32:
        raise ValueError("Image is too small to contain a hidden message.")

    # Read the 32-bit length prefix.
    payload_length = _bits_to_int(lsbs[:32])

    if payload_length <= 0 or 32 + payload_length > len(lsbs):
        raise ValueError(
            "No valid hidden message found (invalid length prefix). "
            "The image may not have been encoded with StegaHide Lab."
        )

    payload_bits = lsbs[32 : 32 + payload_length]
    payload = _bits_to_text(payload_bits)

    if _DELIMITER not in payload:
        raise ValueError(
            "Delimiter not found in extracted payload. "
            "The image may not have been encoded with StegaHide Lab."
        )

    # Strip the delimiter and return the original message.
    message = payload[: payload.index(_DELIMITER)]
    return message
