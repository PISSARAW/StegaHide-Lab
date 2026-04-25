"""
cli.py – Command-line interface for StegaHide Lab.

Sub-commands
------------
encode  Embed a secret message into a PNG image.
decode  Extract a hidden message from a stego PNG image.
keygen  Generate a new encryption key.

Examples
--------
Generate an encryption key::

    python cli.py keygen

Encode a plaintext message::

    python cli.py encode --input carrier.png --output stego.png --message "Hello!"

Encode an encrypted message::

    python cli.py encode --input carrier.png --output stego.png \\
        --message "Hello!" --key <FERNET_KEY>

Decode a hidden message::

    python cli.py decode --input stego.png

Decode an encrypted hidden message::

    python cli.py decode --input stego.png --key <FERNET_KEY>
"""

import argparse
import sys

from steganography.decoder import decode_message
from steganography.encoder import encode_message
from steganography.encryption import decrypt_message, encrypt_message, generate_key


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="steghide-lab",
        description="StegaHide Lab – LSB steganography for PNG images.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    # ── keygen ────────────────────────────────────────────────────────────────
    subparsers.add_parser(
        "keygen",
        help="Generate a new Fernet encryption key.",
    )

    # ── encode ────────────────────────────────────────────────────────────────
    enc = subparsers.add_parser(
        "encode",
        help="Hide a message inside a PNG image.",
    )
    enc.add_argument(
        "-i", "--input",
        required=True,
        metavar="INPUT",
        help="Path to the carrier PNG image.",
    )
    enc.add_argument(
        "-o", "--output",
        required=True,
        metavar="OUTPUT",
        help="Path for the output stego PNG image.",
    )
    enc.add_argument(
        "-m", "--message",
        required=True,
        metavar="MESSAGE",
        help="Secret message to hide.",
    )
    enc.add_argument(
        "-k", "--key",
        default=None,
        metavar="KEY",
        help=(
            "Fernet encryption key.  When supplied the message is encrypted "
            "before embedding.  Generate a key with the 'keygen' sub-command."
        ),
    )

    # ── decode ────────────────────────────────────────────────────────────────
    dec = subparsers.add_parser(
        "decode",
        help="Extract a hidden message from a stego PNG image.",
    )
    dec.add_argument(
        "-i", "--input",
        required=True,
        metavar="INPUT",
        help="Path to the stego PNG image.",
    )
    dec.add_argument(
        "-k", "--key",
        default=None,
        metavar="KEY",
        help=(
            "Fernet decryption key.  Required when the message was encrypted "
            "during encoding."
        ),
    )

    return parser


def _cmd_keygen(_args: argparse.Namespace) -> int:
    key = generate_key()
    print(f"Generated key (keep this secret!):\n{key}")
    return 0


def _cmd_encode(args: argparse.Namespace) -> int:
    message = args.message

    if args.key:
        try:
            message = encrypt_message(message, args.key)
        except ValueError as exc:
            print(f"[ERROR] Encryption failed: {exc}", file=sys.stderr)
            return 1

    try:
        encode_message(args.input, args.output, message)
        print(f"[OK] Message hidden in '{args.output}'.")
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    return 0


def _cmd_decode(args: argparse.Namespace) -> int:
    try:
        message = decode_message(args.input)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if args.key:
        try:
            message = decrypt_message(message, args.key)
        except ValueError as exc:
            print(f"[ERROR] Decryption failed: {exc}", file=sys.stderr)
            return 1

    print(f"Hidden message:\n{message}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "keygen":
        return _cmd_keygen(args)
    if args.command == "encode":
        return _cmd_encode(args)
    if args.command == "decode":
        return _cmd_decode(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
