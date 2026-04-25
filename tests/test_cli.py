"""Tests for the CLI interface."""

import tempfile
from pathlib import Path

import pytest
from PIL import Image

from cli import main


def _make_blank_png(width: int = 200, height: int = 200) -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img = Image.new("RGB", (width, height), color=(100, 150, 200))
    img.save(tmp.name, format="PNG")
    return Path(tmp.name)


class TestKeygenCommand:
    def test_keygen_exits_zero(self, capsys):
        rc = main(["keygen"])
        assert rc == 0

    def test_keygen_prints_key(self, capsys):
        main(["keygen"])
        out = capsys.readouterr().out
        assert "Generated key" in out
        assert len(out.strip().split("\n")) >= 2  # header + key line


class TestEncodeCommand:
    def test_encode_exits_zero(self, tmp_path):
        carrier = _make_blank_png()
        output = tmp_path / "stego.png"
        rc = main(["encode", "-i", str(carrier), "-o", str(output), "-m", "hi"])
        assert rc == 0
        assert output.exists()

    def test_encode_prints_ok(self, tmp_path, capsys):
        carrier = _make_blank_png()
        output = tmp_path / "stego.png"
        main(["encode", "-i", str(carrier), "-o", str(output), "-m", "hi"])
        out = capsys.readouterr().out
        assert "[OK]" in out

    def test_encode_missing_input_returns_nonzero(self, tmp_path):
        rc = main(
            ["encode", "-i", str(tmp_path / "nope.png"), "-o", str(tmp_path / "out.png"), "-m", "x"]
        )
        assert rc != 0

    def test_encode_non_png_output_returns_nonzero(self, tmp_path):
        carrier = _make_blank_png()
        rc = main(["encode", "-i", str(carrier), "-o", str(tmp_path / "out.bmp"), "-m", "x"])
        assert rc != 0

    def test_encode_with_encryption(self, tmp_path, capsys):
        from steganography.encryption import generate_key

        carrier = _make_blank_png()
        output = tmp_path / "stego.png"
        key = generate_key()
        rc = main(
            ["encode", "-i", str(carrier), "-o", str(output), "-m", "secret", f"--key={key}"]
        )
        assert rc == 0

    def test_encode_with_bad_key_returns_nonzero(self, tmp_path):
        carrier = _make_blank_png()
        output = tmp_path / "stego.png"
        rc = main(
            ["encode", "-i", str(carrier), "-o", str(output), "-m", "hello", "--key=bad-key"]
        )
        assert rc != 0


class TestDecodeCommand:
    def _encode(self, carrier: Path, output: Path, message: str) -> None:
        main(["encode", "-i", str(carrier), "-o", str(output), "-m", message])

    def test_decode_exits_zero(self, tmp_path, capsys):
        carrier = _make_blank_png()
        stego = tmp_path / "stego.png"
        self._encode(carrier, stego, "hello")
        rc = main(["decode", "-i", str(stego)])
        assert rc == 0

    def test_decode_prints_message(self, tmp_path, capsys):
        carrier = _make_blank_png()
        stego = tmp_path / "stego.png"
        self._encode(carrier, stego, "hello world")
        capsys.readouterr()  # clear encode output
        main(["decode", "-i", str(stego)])
        out = capsys.readouterr().out
        assert "hello world" in out

    def test_decode_encrypted_round_trip(self, tmp_path, capsys):
        from steganography.encryption import generate_key

        carrier = _make_blank_png()
        stego = tmp_path / "stego.png"
        key = generate_key()
        main(
            ["encode", "-i", str(carrier), "-o", str(stego), "-m", "topsecret", f"--key={key}"]
        )
        capsys.readouterr()
        main(["decode", "-i", str(stego), f"--key={key}"])
        out = capsys.readouterr().out
        assert "topsecret" in out

    def test_decode_missing_file_returns_nonzero(self, tmp_path):
        rc = main(["decode", "-i", str(tmp_path / "ghost.png")])
        assert rc != 0

    def test_decode_wrong_key_returns_nonzero(self, tmp_path):
        from steganography.encryption import generate_key

        carrier = _make_blank_png()
        stego = tmp_path / "stego.png"
        key1 = generate_key()
        key2 = generate_key()
        main(
            ["encode", "-i", str(carrier), "-o", str(stego), "-m", "secret", f"--key={key1}"]
        )
        rc = main(["decode", "-i", str(stego), f"--key={key2}"])
        assert rc != 0
