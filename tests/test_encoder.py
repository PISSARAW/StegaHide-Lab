"""Tests for the LSB encoder."""

import tempfile
from pathlib import Path

import pytest
from PIL import Image

from steganography.encoder import encode_message


def _make_blank_png(width: int = 100, height: int = 100) -> Path:
    """Create a temporary solid-white PNG and return its path."""
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    img.save(tmp.name, format="PNG")
    return Path(tmp.name)


class TestEncodeMessage:
    def test_creates_output_file(self, tmp_path):
        carrier = _make_blank_png()
        output = tmp_path / "stego.png"
        encode_message(carrier, output, "hello")
        assert output.exists()

    def test_output_is_valid_png(self, tmp_path):
        carrier = _make_blank_png()
        output = tmp_path / "stego.png"
        encode_message(carrier, output, "hello")
        img = Image.open(output)
        assert img.format == "PNG"

    def test_output_same_dimensions(self, tmp_path):
        carrier = _make_blank_png(200, 150)
        output = tmp_path / "stego.png"
        encode_message(carrier, output, "hello")
        img = Image.open(output)
        assert img.size == (200, 150)

    def test_raises_for_non_png_output(self, tmp_path):
        carrier = _make_blank_png()
        with pytest.raises(ValueError, match="PNG"):
            encode_message(carrier, tmp_path / "out.jpg", "hello")

    def test_raises_for_missing_input(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            encode_message(tmp_path / "nonexistent.png", tmp_path / "out.png", "hi")

    def test_raises_when_message_too_large(self, tmp_path):
        # 1×1 PNG gives only 3 usable LSBs → can store 3 bits of payload.
        carrier = _make_blank_png(1, 1)
        long_msg = "A" * 1000
        with pytest.raises(ValueError, match="too large"):
            encode_message(carrier, tmp_path / "out.png", long_msg)

    def test_empty_message(self, tmp_path):
        """An empty string should be encodable without error."""
        carrier = _make_blank_png()
        output = tmp_path / "stego.png"
        encode_message(carrier, output, "")
        assert output.exists()

    def test_unicode_message(self, tmp_path):
        carrier = _make_blank_png()
        output = tmp_path / "stego.png"
        encode_message(carrier, output, "こんにちは 🌏")
        assert output.exists()
