"""
encoder.py – LSB steganography encoder.

Embeds a secret message into the least-significant bits of a PNG image's
pixel colour channels.  A 32-bit big-endian length prefix is stored first so
the decoder knows exactly how many bits to read.

Supported format: PNG (lossless – required for LSB to survive save/load).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

# Delimiter appended so decoder can find message end without relying solely on
# the length prefix (acts as a sanity-check).
_DELIMITER = "<<END>>"


def _text_to_bits(text: str) -> list[int]:
    """Return a flat list of bits (MSB-first) representing *text* in UTF-8."""
    bits: list[int] = []
    for byte in text.encode("utf-8"):
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    return bits


def _int_to_bits(value: int, width: int = 32) -> list[int]:
    """Return *width* bits (MSB-first) representing the unsigned integer *value*."""
    return [(value >> (width - 1 - i)) & 1 for i in range(width)]


def encode_message(
    input_image_path: str | Path,
    output_image_path: str | Path,
    message: str,
) -> None:
    """Embed *message* into *input_image_path* and write the result to *output_image_path*.

    The output image must use the PNG format (lossless).  If the output path
    does not end with ``.png`` a ``ValueError`` is raised.

    Parameters
    ----------
    input_image_path:
        Path to the carrier PNG image.
    output_image_path:
        Destination path for the stego PNG image.
    message:
        Plaintext (or pre-encrypted bytes encoded as a string) to hide.

    Raises
    ------
    ValueError
        If the output path is not a PNG file, or if the message is too large
        to fit inside the carrier image.
    FileNotFoundError
        If *input_image_path* does not exist.
    """
    input_image_path = Path(input_image_path)
    output_image_path = Path(output_image_path)

    if output_image_path.suffix.lower() != ".png":
        raise ValueError(
            f"Output image must be a PNG file, got: '{output_image_path.suffix}'"
        )

    if not input_image_path.exists():
        raise FileNotFoundError(f"Input image not found: '{input_image_path}'")

    payload = message + _DELIMITER
    payload_bits = _text_to_bits(payload)
    length_bits = _int_to_bits(len(payload_bits))
    all_bits = length_bits + payload_bits

    img = Image.open(input_image_path).convert("RGB")
    width, height = img.size
    total_pixels = width * height

    # Each pixel has 3 channels (R, G, B) → 3 available LSBs per pixel.
    available_bits = total_pixels * 3
    if len(all_bits) > available_bits:
        raise ValueError(
            f"Message too large: needs {len(all_bits)} bits but image only "
            f"provides {available_bits} bits of capacity."
        )

    pixel_access = img.load()
    if pixel_access is None:
        raise ValueError(f"Failed to load pixel data from '{input_image_path}'.")
    bit_index = 0

    for y in range(height):
        for x in range(width):
            r, g, b = pixel_access[x, y]
            channels = [r, g, b]
            for c in range(3):
                if bit_index < len(all_bits):
                    channels[c] = (channels[c] & ~1) | all_bits[bit_index]
                    bit_index += 1
            pixel_access[x, y] = (channels[0], channels[1], channels[2])

    img.save(output_image_path, format="PNG")
