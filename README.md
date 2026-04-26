# StegaHide Lab

> ⚠️ **Projet personnel — Personal project**
>
> 🇫🇷 Ce dépôt est un **projet personnel**. Bien qu'il soit public, il n'est **pas destiné à un usage général** : il n'y a aucune garantie de support, de maintenance, de stabilité d'API ni de prise en compte des contributions ou des issues. Le code est partagé à titre informatif et pédagogique. Utilisez-le à vos propres risques.
>
> 🇬🇧 This repository is a **personal project**. Although it is public, it is **not intended for general use**: there is no guarantee of support, maintenance, API stability, or that contributions or issues will be reviewed. The code is shared for informational and educational purposes. Use at your own risk.

---

A Python toolkit for **hiding** and **extracting** secret messages inside PNG images using the
**Least Significant Bit (LSB)** steganography technique, with optional **AES encryption** (Fernet)
before embedding.

---

## Table of Contents

1. [What is Steganography?](#what-is-steganography)
2. [How LSB Steganography Works](#how-lsb-steganography-works)
3. [Forensic Implications](#forensic-implications)
4. [Project Structure](#project-structure)
5. [Installation](#installation)
6. [Quick Start](#quick-start)
7. [CLI Reference](#cli-reference)
8. [Python API](#python-api)
9. [Running Tests](#running-tests)
10. [Security Notes](#security-notes)
11. [License](#license)

---

## What is Steganography?

**Steganography** is the practice of hiding secret information *inside* an ordinary-looking carrier
medium so that the existence of the hidden message is concealed.  Unlike *cryptography*, which
makes data unreadable, steganography aims to make the data *invisible*.

Common carrier media include:

| Carrier      | Common technique         |
|--------------|--------------------------|
| Images       | LSB pixel manipulation   |
| Audio files  | Phase or LSB encoding    |
| Video        | Per-frame pixel encoding |
| Text         | Zero-width character insertion |

StegaHide Lab focuses on **digital images** (PNG format) because PNG uses **lossless compression**,
which is critical — lossy formats such as JPEG re-quantise pixel values and destroy the hidden bits.

---

## How LSB Steganography Works

Every pixel in an RGB image is composed of three 8-bit colour channels: **Red**, **Green**, and
**Blue**.  Each channel stores a value from 0 to 255.

The *least significant bit* (bit 0) of any channel contributes only ±1 to the overall colour
value — a change that is imperceptible to the human eye.

### Encoding

1. The secret message is encoded as UTF-8 bytes and converted into a flat stream of bits.
2. A 32-bit big-endian **length prefix** (number of payload bits) is prepended.
3. A sentinel **delimiter** (`<<END>>`) is appended so the decoder can verify integrity.
4. Each bit is written into the LSB of successive colour channels, scanning pixels
   left-to-right, top-to-bottom.

```
Original pixel:  R=11001010  G=10110101  B=01101100
Message bits:         0            1           1
Stego pixel:     R=11001010  G=10110101  B=01101101
                          ↑            ↑           ↑
                         LSB          LSB         LSB changed
```

### Decoding

1. The LSBs of every channel are read in scan order.
2. The first 32 bits give the payload length.
3. Exactly that many bits are collected and decoded back to UTF-8 text.
4. The delimiter is verified and stripped before the message is returned.

### Capacity

An image with *W × H* pixels provides **3 × W × H** storable bits.  A 100 × 100 PNG can hold
up to ≈ 3 750 bytes of payload (including the length prefix and delimiter overhead).

---

## Forensic Implications

LSB steganography leaves several detectable artefacts that digital forensic investigators look for:

| Detection technique | What it reveals |
|---------------------|-----------------|
| **Statistical analysis (RS analysis, Chi-square test)** | Unusual uniformity of LSB bit pairs — random-looking LSBs are suspicious in natural images whose LSBs follow non-uniform distributions. |
| **Visual LSB plane inspection** | Displaying only the LSB layer of a stego image often reveals structured patterns instead of pure noise. |
| **File size / metadata comparison** | A re-saved PNG produced by this tool will have a different hash, creation timestamp, and potentially a different ICC profile or software metadata tag compared to the original. |
| **Histogram anomalies** | Pixel value histograms for stego images show a characteristic "pairs of values" pattern caused by zeroing/setting the LSB. |
| **Known-carrier comparison** | If the original carrier image is available, a simple XOR comparison pinpoints every modified pixel. |

### Mitigations (defence-in-depth)

* **Encrypt before embedding** — even if the presence of hidden data is detected, the content
  remains confidential (use `--key` flag with a strong Fernet key).
* **Spread payload across fewer LSBs** — embed in only a subset of pixels to reduce statistical
  artefacts.
* **Use noisy natural images** — smooth gradients and solid colours are easiest to detect;
  complex textures mask modifications better.

> ⚠️ **Responsible use** — This tool is intended for educational and research purposes.  Using
> steganography to conceal illegal content or evade lawful monitoring is prohibited.

---

## Project Structure

```
StegaHide-Lab/
├── steganography/
│   ├── __init__.py        # Public API re-exports
│   ├── encoder.py         # LSB message embedding
│   ├── decoder.py         # LSB message extraction
│   └── encryption.py      # Fernet (AES-128-CBC + HMAC) helpers
├── tests/
│   ├── __init__.py
│   ├── test_encoder.py
│   ├── test_decoder.py
│   ├── test_encryption.py
│   └── test_cli.py
├── cli.py                 # Command-line interface (argparse)
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Installation

```bash
# Clone the repository
git clone https://github.com/PISSARAW/StegaHide-Lab.git
cd StegaHide-Lab

# Install dependencies (Python 3.9+)
pip install -r requirements.txt

# Optional: install as an editable package
pip install -e .
```

Dependencies:

| Package | Purpose |
|---------|---------|
| [Pillow](https://python-pillow.org/) ≥ 10.0 | PNG image I/O and pixel manipulation |
| [cryptography](https://cryptography.io/) ≥ 41.0 | Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256) |

---

## Quick Start

```bash
# 1. Generate an encryption key (save this securely!)
python cli.py keygen

# 2. Hide an encrypted message in a PNG image
python cli.py encode \
    --input  carrier.png \
    --output stego.png   \
    --message "Meet me at dawn." \
    --key    <KEY_FROM_STEP_1>

# 3. Extract and decrypt the message
python cli.py decode \
    --input stego.png \
    --key   <KEY_FROM_STEP_1>
```

---

## CLI Reference

### `keygen` — generate an encryption key

```
python cli.py keygen
```

Prints a new URL-safe base64-encoded Fernet key to standard output.

---

### `encode` — hide a message

```
python cli.py encode -i INPUT -o OUTPUT -m MESSAGE [-k KEY]
```

| Flag | Description |
|------|-------------|
| `-i`, `--input`   | Path to the carrier PNG image (read-only) |
| `-o`, `--output`  | Path for the stego PNG image (must end in `.png`) |
| `-m`, `--message` | Secret message to embed |
| `-k`, `--key`     | *(optional)* Fernet key — encrypts the message before embedding |

---

### `decode` — extract a hidden message

```
python cli.py decode -i INPUT [-k KEY]
```

| Flag | Description |
|------|-------------|
| `-i`, `--input` | Path to the stego PNG image |
| `-k`, `--key`   | *(optional)* Fernet key — required if the message was encrypted |

---

## Python API

```python
from steganography import encode_message, decode_message
from steganography import encrypt_message, decrypt_message, generate_key

# Encrypt then embed
key = generate_key()
ciphertext = encrypt_message("top secret", key)
encode_message("carrier.png", "stego.png", ciphertext)

# Extract then decrypt
raw = decode_message("stego.png")
plaintext = decrypt_message(raw, key)
print(plaintext)  # "top secret"
```

### `encode_message(input_image_path, output_image_path, message)`

Embeds `message` (str) into `input_image_path` (PNG) and writes the result to
`output_image_path` (must be `.png`).

Raises `ValueError` if the message is too large for the carrier image or the output is not PNG.
Raises `FileNotFoundError` if the input image does not exist.

---

### `decode_message(image_path)`

Extracts and returns the hidden message (str) from the stego image at `image_path`.

Raises `FileNotFoundError` if the image does not exist.
Raises `ValueError` if the image contains no valid hidden message.

---

### `generate_key() → str`

Returns a new random Fernet key as a string.

---

### `encrypt_message(message, key) → str`

Encrypts `message` with `key` using Fernet (AES-128-CBC + HMAC-SHA256) and returns the
ciphertext as a URL-safe base64 string.

---

### `decrypt_message(ciphertext, key) → str`

Decrypts `ciphertext` with `key` and returns the plaintext.  Raises `ValueError` on wrong key
or corrupted ciphertext.

---

## Running Tests

```bash
pip install pytest
python -m pytest
```

All 40 tests should pass.

---

## Security Notes

* **Key management** — Fernet keys are 32 random bytes (256 bits).  Store them securely
  (e.g., a password manager or secrets manager).  Anyone with the key can decrypt the message.
* **Image integrity** — LSB encoding modifies pixel values by ±1, which is invisible visually
  but detectable statistically.  Do not assume visual indistinguishability equals forensic
  invisibility.
* **PNG only** — JPEG and other lossy formats are not supported because they destroy the hidden
  bits during compression.
* **No authentication of the carrier** — there is no MAC over the carrier image pixels.  An
  attacker who modifies the stego image will cause decoding to fail or return garbage; the
  Fernet HMAC protects the *message content* when encryption is used.

---

## License

MIT — see [LICENSE](LICENSE) for details.
