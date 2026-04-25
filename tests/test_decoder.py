"""Tests for the LSB decoder."""

import tempfile
from pathlib import Path

import pytest
from PIL import Image

from steganography.decoder import decode_message
from steganography.encoder import encode_message


def _make_blank_png(width: int = 200, height: int = 200) -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img = Image.new("RGB", (width, height), color=(128, 200, 50))
    img.save(tmp.name, format="PNG")
    return Path(tmp.name)


class TestDecodeMessage:
    def test_round_trip_simple(self, tmp_path):
        carrier = _make_blank_png()
        stego = tmp_path / "stego.png"
        message = "Hello, steganography!"
        encode_message(carrier, stego, message)
        assert decode_message(stego) == message

    def test_round_trip_empty_message(self, tmp_path):
        carrier = _make_blank_png()
        stego = tmp_path / "stego.png"
        encode_message(carrier, stego, "")
        assert decode_message(stego) == ""

    def test_round_trip_unicode(self, tmp_path):
        carrier = _make_blank_png()
        stego = tmp_path / "stego.png"
        message = "日本語テスト 🎌"
        encode_message(carrier, stego, message)
        assert decode_message(stego) == message

    def test_round_trip_multiline(self, tmp_path):
        carrier = _make_blank_png()
        stego = tmp_path / "stego.png"
        message = "line1\nline2\nline3"
        encode_message(carrier, stego, message)
        assert decode_message(stego) == message

    def test_raises_for_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            decode_message(tmp_path / "ghost.png")

    def test_raises_for_unencoded_image(self, tmp_path):
        """A plain PNG with no hidden data should raise ValueError."""
        plain = _make_blank_png(10, 10)
        with pytest.raises(ValueError):
            decode_message(plain)

    def test_long_message_round_trip(self, tmp_path):
        carrier = _make_blank_png(500, 500)
        stego = tmp_path / "stego.png"
        message = "A" * 500
        encode_message(carrier, stego, message)
        assert decode_message(stego) == message
