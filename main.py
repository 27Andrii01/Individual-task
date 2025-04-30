import os
import base64
import zlib
from PIL import Image, PngImagePlugin
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

#---------------------------------------------------------------

# Helpers

def load_private_key(path: str):
    """Load an RSA private key from PEM, error if missing."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Private key not found: {path}")
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def load_public_key(path: str):
    """Load an RSA public key from PEM, error if missing."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Public key not found: {path}")
    with open(path, "rb") as f:
        return serialization.load_pem_public_key(f.read())
      
#---------------------------------------------------------------

# Signing

def sign_image(input_png: str, priv_key_path: str, output_png: str):
    """
    Embed a digital RSA signature into a PNG image for later authenticity checks.

    This function performs the following steps:
      1. Loads the RSA private key from `priv_key_path` (PEM format).
      2. Opens `input_png`, converts it to RGBA mode for consistency, and reads its raw pixel bytes.
      3. Generates an RSA signature (PKCS#1 v1.5 with SHA-256) over those bytes.
      4. Compresses the binary signature with zlib and Base64-encodes it to make it appear as random data.
      5. Splits the encoded signature into two halves for added stealth.
      6. Embeds these halves into the PNG’s metadata fields:
         - `"Software"`: an innocuous label
         - `"Comment"`: first half of the signature
         - `"Description"`: second half of the signature
      7. Saves the result as `output_png`, visually identical to the original but carrying the hidden signature.

    Args:
        input_png (str): Path to the original PNG file to be signed.
        priv_key_path (str): Path to the RSA private key (PEM) used for signing.
        output_png (str): Path where the signed PNG will be written.

    Returns:
        None. Prints a confirmation message upon successful signing.
    """
    # 1) Key & image
    priv = load_private_key(priv_key_path)
    img = Image.open(input_png).convert("RGBA")
    data = img.tobytes()

    # 2) Sign
    raw_sig = priv.sign(data, padding.PKCS1v15(), hashes.SHA256())

    # 3) Compress and b64
    comp = zlib.compress(raw_sig)
    b64 = base64.b64encode(comp).decode("ascii")

    # 4) Split into two contiguous pieces
    mid = len(b64) // 2
    part1, part2 = b64[:mid], b64[mid:]

    # 5) Build metadata
    pnginfo = PngImagePlugin.PngInfo()
    pnginfo.add_text("Software", "MyImageSigner v1.0")
    pnginfo.add_text("Comment", part1)
    pnginfo.add_text("Description", part2)

    # 6) Save signed image
    img.save(output_png, "PNG", pnginfo=pnginfo)
    print(f"✅ Signed image saved to {output_png}")
  
#---------------------------------------------------------------

# Verification

def verify_image(png_path: str, pub_key_path: str) -> bool:
    """
    Verify the digital signature embedded in a PNG file.

    This function uses the provided RSA public key to confirm that the image
    at `png_path` has not been altered since it was signed. It:

      1. Loads the RSA public key from `pub_key_path`.
      2. Opens the PNG, normalizes it to RGBA, and reads its raw pixel bytes.
      3. Extracts and reassembles the compressed, Base64-encoded signature
         stored across the 'Comment' and 'Description' text chunks.
      4. Decompresses and decodes the signature, then verifies it against
         the image bytes using RSA+SHA-256.

    Returns:
        True if the signature is present and valid (image is authentic),
        False otherwise (missing fields, decode errors, or tampering detected).
    """
    pub = load_public_key(pub_key_path)
    img = Image.open(png_path).convert("RGBA")

    # 2) Grab both halves
    info = img.info
    p1 = info.get("Comment")
    p2 = info.get("Description")
    if not p1 or not p2:
        print(f"⚠️  Missing signature fields in {png_path}")
        return False

    # 3) Reconstruct, decode & decompress
    b64 = p1 + p2
    try:
        comp = base64.b64decode(b64)
        signature = zlib.decompress(comp)
    except Exception as e:
        print(f"❌ Failed to reconstruct signature: {e}")
        return False

    # 4) Verify
    try:
        pub.verify(
            signature,
            img.tobytes(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        print(f"✅ {png_path}: Signature valid.")
        return True
    except Exception:
        print(f"❌ {png_path}: Signature invalid or image tampered.")
        return False
      
#---------------------------------------------------------------

# Tampering

def tamper_image(input_png: str, output_png: str):
    """
    Create a tampered copy of a signed PNG to test signature verification.

    This function simulates an unauthorized modification by flipping one bit
    in the first pixel of the image, while preserving all embedded text chunks
    (including any signature data). Use this to confirm that verify_image()
    correctly flags tampered files.

    Steps:
      1. Open the source PNG and read its info dict (all text chunks).
      2. Build a new PngInfo object and re-add each metadata key/value pair.
      3. Convert the image to RGBA mode so pixels can be modified.
      4. Flip the least-significant bit of the red channel in pixel (0,0).
      5. Save the result to `output_png`, embedding the original metadata.

    Args:
        input_png:  Path to the signed PNG file to be tampered.
        output_png: Path where the tampered PNG will be saved.

    Returns:
        None. Prints a confirmation message upon successful save.
    """
    orig = Image.open(input_png)
    info = orig.info

    # Rebuild metadata
    pnginfo = PngImagePlugin.PngInfo()
    for k, v in info.items():
        pnginfo.add_text(k, v)

    # Mutate
    img = orig.convert("RGBA")
    px = img.load()
    r, g, b, a = px[0, 0]
    px[0, 0] = (r ^ 1, g, b, a) 

    img.save(output_png, "PNG", pnginfo=pnginfo)
    print(f"✅ Tampered image saved to {output_png}")

#---------------------------------------------------------------

# Demo

if __name__ == "__main__":
    ORIGINAL = "original.png"
    PRIVATE  = "private.pem"
    PUBLIC   = "public.pem"
    SIGNED   = "signed.png"
    TAMPED   = "signed_tampered.png"

    # Sign → verify → tamper → verify again
    sign_image(ORIGINAL, PRIVATE, SIGNED)
    verify_image(SIGNED, PUBLIC)
    tamper_image(SIGNED, TAMPED)
    verify_image(TAMPED, PUBLIC)

